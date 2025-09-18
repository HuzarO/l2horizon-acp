from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.media_storage.models import MediaFile
import os


class Command(BaseCommand):
    help = 'Limpa arquivos de mídia não utilizados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra os arquivos que seriam deletados, sem deletar',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a remoção sem confirmação',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧹 Iniciando limpeza de arquivos de mídia...'))
        
        # Encontrar arquivos não utilizados
        unused_files = MediaFile.objects.filter(usages__isnull=True, is_active=True)
        count = unused_files.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum arquivo não utilizado encontrado!'))
            return
        
        self.stdout.write(f'📊 Encontrados {count} arquivos não utilizados:')
        
        total_size = 0
        for media_file in unused_files:
            size_mb = media_file.file_size / 1024 / 1024
            total_size += size_mb
            self.stdout.write(f'  - {media_file.title} ({size_mb:.2f} MB)')
        
        self.stdout.write(f'💾 Total a liberar: {total_size:.2f} MB')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 Modo dry-run ativo - nenhum arquivo foi deletado'))
            return
        
        # Confirmação
        if not options['force']:
            confirm = input(f'\n❓ Deseja deletar {count} arquivos? (s/N): ')
            if confirm.lower() not in ['s', 'sim', 'y', 'yes']:
                self.stdout.write(self.style.WARNING('❌ Operação cancelada'))
                return
        
        # Deletar arquivos
        deleted_count = 0
        with transaction.atomic():
            for media_file in unused_files:
                try:
                    file_path = media_file.file.path if media_file.file else None
                    media_file.delete()
                    
                    # Deletar arquivo físico se existir
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    
                    deleted_count += 1
                    self.stdout.write(f'  ✅ {media_file.title} deletado')
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Erro ao deletar {media_file.title}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 Limpeza concluída! {deleted_count} arquivos deletados.')
        )
