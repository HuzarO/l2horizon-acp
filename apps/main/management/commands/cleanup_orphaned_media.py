"""
Comando Django para limpar arquivos de mídia órfãos (não referenciados no banco de dados)

Uso:
    python manage.py cleanup_orphaned_media --dry-run  # Apenas mostra o que seria removido
    python manage.py cleanup_orphaned_media --delete   # Remove os arquivos órfãos
    python manage.py cleanup_orphaned_media --delete --confirm  # Remove sem confirmação
"""

import os
from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from django.db import models
from django.apps import apps
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Remove arquivos de mídia órfãos (não referenciados no banco de dados)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra quais arquivos seriam removidos, sem deletar',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Remove os arquivos órfãos encontrados',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Remove arquivos sem pedir confirmação',
        )
        parser.add_argument(
            '--path',
            type=str,
            help='Caminho específico para limpar (ex: media/social/posts/)',
        )
        parser.add_argument(
            '--exclude',
            type=str,
            nargs='+',
            help='Caminhos para excluir da limpeza (ex: media/static/ media/admin/)',
            default=['media/static/', 'media/admin/', 'media/default/']
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostra informações detalhadas sobre cada arquivo',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_files = options['delete']
        confirm = options['confirm']
        specific_path = options['path']
        exclude_paths = options['exclude']
        verbose = options['verbose']

        # Validar argumentos
        if not dry_run and not delete_files:
            raise CommandError(
                'Você deve especificar --dry-run (para simular) ou --delete (para remover)'
            )

        self.stdout.write(
            self.style.SUCCESS('🔍 Iniciando busca por arquivos de mídia órfãos...\n')
        )

        # Coletar todos os arquivos de mídia referenciados no banco
        referenced_files = self.get_referenced_media_files()

        if verbose:
            self.stdout.write(f'📊 Total de arquivos referenciados no banco: {len(referenced_files)}')

        # Buscar arquivos físicos
        all_physical_files = self.get_physical_media_files(specific_path, exclude_paths)

        if verbose:
            self.stdout.write(f'📁 Total de arquivos físicos encontrados: {len(all_physical_files)}')

        # Identificar arquivos órfãos
        orphaned_files = []
        for file_path in all_physical_files:
            if file_path not in referenced_files:
                orphaned_files.append(file_path)

        # Mostrar resultados
        self.display_results(orphaned_files, dry_run, verbose)

        # Executar remoção se solicitado
        if delete_files and orphaned_files:
            self.delete_orphaned_files(orphaned_files, confirm, verbose)

    def get_referenced_media_files(self):
        """Coleta todos os arquivos de mídia referenciados no banco de dados"""
        referenced_files = set()

        # Percorrer todos os modelos registrados
        for model in apps.get_models():
            # Verificar se o modelo tem campos de arquivo
            file_fields = []
            for field in model._meta.fields:
                if isinstance(field, (models.ImageField, models.FileField)):
                    file_fields.append(field.name)

            if file_fields:
                # Buscar arquivos referenciados para este modelo
                try:
                    for obj in model.objects.all():
                        for field_name in file_fields:
                            field_value = getattr(obj, field_name, None)
                            if field_value and hasattr(field_value, 'name'):
                                # Normalizar caminho para comparação
                                normalized_path = field_value.name.replace('\\', '/')
                                referenced_files.add(normalized_path)
                except Exception as e:
                    # Ignorar erros de acesso ao modelo (pode ser abstrato, etc.)
                    continue

        return referenced_files

    def get_physical_media_files(self, specific_path=None, exclude_paths=None):
        """Coleta todos os arquivos físicos de mídia"""
        physical_files = set()

        # Determinar caminhos para verificar
        if specific_path:
            paths_to_check = [specific_path]
        else:
            # Verificar diretório de mídia padrão
            media_root = getattr(settings, 'MEDIA_ROOT', 'media')
            if os.path.exists(media_root):
                paths_to_check = [media_root]
            else:
                # Se não há MEDIA_ROOT, verificar storage
                try:
                    # Para S3 ou outros storages, usar default_storage
                    if hasattr(default_storage, 'listdir'):
                        paths_to_check = ['/']  # Root do storage
                    else:
                        self.stdout.write(
                            self.style.WARNING('⚠️  Não foi possível determinar o diretório de mídia')
                        )
                        return physical_files
                except Exception:
                    return physical_files

        # Coletar arquivos
        for path in paths_to_check:
            self.collect_files_from_path(path, physical_files, exclude_paths or [])

        return physical_files

    def collect_files_from_path(self, path, file_set, exclude_paths):
        """Coleta arquivos de um caminho específico"""
        try:
            # Verificar se é storage local ou remoto
            if os.path.exists(path):
                # Storage local
                self.collect_files_from_local_path(path, file_set, exclude_paths)
            else:
                # Storage remoto (S3, etc.)
                self.collect_files_from_remote_storage(path, file_set, exclude_paths)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao acessar caminho {path}: {e}')
            )

    def collect_files_from_local_path(self, path, file_set, exclude_paths):
        """Coleta arquivos de storage local"""
        for root, dirs, files in os.walk(path):
            # Verificar se o diretório deve ser excluído
            relative_root = os.path.relpath(root, path)
            should_exclude = False
            for exclude_path in exclude_paths:
                if relative_root.startswith(exclude_path.replace('media/', '')):
                    should_exclude = True
                    break
            
            if should_exclude:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, path)
                # Normalizar caminho
                normalized_path = relative_path.replace('\\', '/')
                file_set.add(normalized_path)

    def collect_files_from_remote_storage(self, path, file_set, exclude_paths):
        """Coleta arquivos de storage remoto (S3, etc.)"""
        try:
            # Usar default_storage para listar arquivos
            if hasattr(default_storage, 'listdir'):
                dirs, files = default_storage.listdir(path)
                
                # Adicionar arquivos
                for file in files:
                    file_path = f"{path}{file}" if path.endswith('/') else f"{path}/{file}"
                    normalized_path = file_path.replace('\\', '/')
                    
                    # Verificar se deve ser excluído
                    should_exclude = False
                    for exclude_path in exclude_paths:
                        if normalized_path.startswith(exclude_path):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        file_set.add(normalized_path)

                # Recursivamente verificar subdiretórios
                for dir_name in dirs:
                    sub_path = f"{path}{dir_name}" if path.endswith('/') else f"{path}/{dir_name}"
                    self.collect_files_from_remote_storage(sub_path, file_set, exclude_paths)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao listar storage remoto: {e}')
            )

    def display_results(self, orphaned_files, dry_run, verbose):
        """Exibe os resultados da busca por arquivos órfãos"""
        if not orphaned_files:
            self.stdout.write(
                self.style.SUCCESS('🎉 Nenhum arquivo órfão encontrado! Seu storage está limpo.')
            )
            return

        self.stdout.write(
            self.style.WARNING(f'\n⚠️  Encontrados {len(orphaned_files)} arquivos órfãos:')
        )

        # Calcular tamanho total
        total_size = 0
        for file_path in orphaned_files:
            try:
                if default_storage.exists(file_path):
                    size = default_storage.size(file_path)
                    total_size += size
            except Exception:
                pass

        # Mostrar tamanho total
        if total_size > 0:
            size_mb = total_size / (1024 * 1024)
            self.stdout.write(f'📊 Tamanho total: {size_mb:.2f} MB')

        # Mostrar arquivos
        for i, file_path in enumerate(orphaned_files[:50], 1):  # Limitar a 50 arquivos
            if verbose:
                try:
                    size = default_storage.size(file_path) if default_storage.exists(file_path) else 0
                    size_kb = size / 1024
                    self.stdout.write(f'  {i:3d}. {file_path} ({size_kb:.1f} KB)')
                except Exception:
                    self.stdout.write(f'  {i:3d}. {file_path}')
            else:
                self.stdout.write(f'  {i:3d}. {file_path}')

        if len(orphaned_files) > 50:
            self.stdout.write(f'  ... e mais {len(orphaned_files) - 50} arquivos')

        # Mostrar ação que será executada
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n🔍 Modo DRY-RUN: Nenhum arquivo foi removido')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n🗑️  Use --delete para remover estes arquivos')
            )

    def delete_orphaned_files(self, orphaned_files, confirm, verbose):
        """Remove os arquivos órfãos"""
        if not confirm:
            self.stdout.write(
                self.style.WARNING('\n⚠️  Você está prestes a remover arquivos permanentemente!')
            )
            response = input('Digite "CONFIRMAR" para continuar: ')
            if response != 'CONFIRMAR':
                self.stdout.write(
                    self.style.ERROR('❌ Operação cancelada pelo usuário')
                )
                return

        self.stdout.write(
            self.style.SUCCESS(f'\n🗑️  Removendo {len(orphaned_files)} arquivos órfãos...')
        )

        deleted_count = 0
        failed_count = 0

        for file_path in orphaned_files:
            try:
                if default_storage.exists(file_path):
                    default_storage.delete(file_path)
                    deleted_count += 1
                    if verbose:
                        self.stdout.write(f'  ✅ Removido: {file_path}')
                else:
                    if verbose:
                        self.stdout.write(f'  ⚠️  Não encontrado: {file_path}')
            except Exception as e:
                failed_count += 1
                if verbose:
                    self.stdout.write(f'  ❌ Erro ao remover {file_path}: {e}')

        # Mostrar resumo
        self.stdout.write(
            self.style.SUCCESS(f'\n📊 Resumo da remoção:')
        )
        self.stdout.write(f'  ✅ Arquivos removidos: {deleted_count}')
        if failed_count > 0:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Falhas na remoção: {failed_count}')
            )

        # Calcular espaço liberado
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'🎉 {deleted_count} arquivos órfãos foram removidos com sucesso!')
            )
