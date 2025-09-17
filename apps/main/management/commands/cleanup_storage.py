"""
Comando Django para limpeza geral do storage

Uso:
    python manage.py cleanup_storage --help
    python manage.py cleanup_storage --analyze    # Analisa o storage
    python manage.py cleanup_storage --clean      # Limpa arquivos órfãos
    python manage.py cleanup_storage --stats      # Mostra estatísticas
"""

import os
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import models
from django.apps import apps


class Command(BaseCommand):
    help = 'Utilitário para análise e limpeza do storage de mídia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analisa o storage e mostra arquivos órfãos',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Remove arquivos órfãos',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostra estatísticas do storage',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Executa limpeza sem pedir confirmação',
        )

    def handle(self, *args, **options):
        if options['stats']:
            self.show_storage_stats()
        elif options['analyze']:
            self.analyze_storage()
        elif options['clean']:
            self.clean_storage(options['confirm'])
        else:
            self.stdout.write(
                self.style.ERROR('Especifique uma ação: --analyze, --clean ou --stats')
            )

    def show_storage_stats(self):
        """Mostra estatísticas do storage"""
        self.stdout.write(
            self.style.SUCCESS('📊 Estatísticas do Storage\n')
        )

        # Contar arquivos referenciados por modelo
        total_referenced = 0
        model_stats = {}

        for model in apps.get_models():
            file_fields = []
            for field in model._meta.fields:
                if isinstance(field, (models.ImageField, models.FileField)):
                    file_fields.append(field.name)

            if file_fields:
                count = model.objects.count()
                if count > 0:
                    model_stats[model.__name__] = {
                        'count': count,
                        'fields': file_fields
                    }
                    total_referenced += count

        self.stdout.write(f'📁 Modelos com arquivos de mídia:')
        for model_name, stats in model_stats.items():
            self.stdout.write(f'  • {model_name}: {stats["count"]} registros')
            for field in stats['fields']:
                self.stdout.write(f'    - Campo: {field}')

        self.stdout.write(f'\n📊 Total de registros com mídia: {total_referenced}')

    def analyze_storage(self):
        """Analisa o storage e identifica problemas"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Analisando Storage...\n')
        )

        # Coletar arquivos referenciados
        referenced_files = self.get_referenced_files()
        self.stdout.write(f'📊 Arquivos referenciados no banco: {len(referenced_files)}')

        # Coletar arquivos físicos
        physical_files = self.get_physical_files()
        self.stdout.write(f'📁 Arquivos físicos encontrados: {len(physical_files)}')

        # Identificar órfãos
        orphaned = physical_files - referenced_files
        if orphaned:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Arquivos órfãos encontrados: {len(orphaned)}')
            )
            
            # Mostrar alguns exemplos
            for i, file_path in enumerate(list(orphaned)[:10], 1):
                self.stdout.write(f'  {i}. {file_path}')
            
            if len(orphaned) > 10:
                self.stdout.write(f'  ... e mais {len(orphaned) - 10} arquivos')
                
            self.stdout.write(
                self.style.SUCCESS('\n💡 Use --clean para remover os arquivos órfãos')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('🎉 Nenhum arquivo órfão encontrado!')
            )

    def clean_storage(self, confirm=False):
        """Remove arquivos órfãos do storage"""
        self.stdout.write(
            self.style.SUCCESS('🧹 Limpando Storage...\n')
        )

        # Coletar arquivos órfãos
        referenced_files = self.get_referenced_files()
        physical_files = self.get_physical_files()
        orphaned_files = physical_files - referenced_files

        if not orphaned_files:
            self.stdout.write(
                self.style.SUCCESS('🎉 Nenhum arquivo órfão para remover!')
            )
            return

        self.stdout.write(f'🗑️  Encontrados {len(orphaned_files)} arquivos órfãos')

        if not confirm:
            response = input('Deseja continuar? (sim/não): ')
            if response.lower() not in ['sim', 's', 'yes', 'y']:
                self.stdout.write('❌ Operação cancelada')
                return

        # Remover arquivos
        removed_count = 0
        for file_path in orphaned_files:
            try:
                if default_storage.exists(file_path):
                    default_storage.delete(file_path)
                    removed_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao remover {file_path}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'✅ {removed_count} arquivos órfãos removidos!')
        )

    def get_referenced_files(self):
        """Coleta arquivos referenciados no banco"""
        referenced_files = set()

        for model in apps.get_models():
            file_fields = []
            for field in model._meta.fields:
                if isinstance(field, (models.ImageField, models.FileField)):
                    file_fields.append(field.name)

            if file_fields:
                try:
                    for obj in model.objects.all():
                        for field_name in file_fields:
                            field_value = getattr(obj, field_name, None)
                            if field_value and hasattr(field_value, 'name'):
                                normalized_path = field_value.name.replace('\\', '/')
                                referenced_files.add(normalized_path)
                except Exception:
                    continue

        return referenced_files

    def get_physical_files(self):
        """Coleta arquivos físicos do storage"""
        physical_files = set()

        try:
            # Para storage local
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            if os.path.exists(media_root):
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, media_root)
                        normalized_path = relative_path.replace('\\', '/')
                        physical_files.add(normalized_path)
            else:
                # Para storage remoto
                self.collect_remote_files(physical_files)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao listar arquivos físicos: {e}')
            )

        return physical_files

    def collect_remote_files(self, file_set):
        """Coleta arquivos de storage remoto"""
        try:
            if hasattr(default_storage, 'listdir'):
                dirs, files = default_storage.listdir('/')
                for file in files:
                    file_set.add(file)
        except Exception:
            pass
