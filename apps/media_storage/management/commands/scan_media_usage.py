from django.core.management.base import BaseCommand
from apps.media_storage.utils import (
    scan_and_register_media_usage, 
    get_media_usage_stats,
    cleanup_orphaned_files,
    find_orphaned_files
)


class Command(BaseCommand):
    help = 'Escaneia o projeto e registra automaticamente o uso de arquivos de mídia'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scan',
            action='store_true',
            help='Escaneia modelos e registra usos de mídia',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Mostra estatísticas de uso de mídia',
        )
        parser.add_argument(
            '--orphaned',
            action='store_true',
            help='Lista arquivos órfãos (físicos sem registro)',
        )
        parser.add_argument(
            '--cleanup-orphaned',
            action='store_true',
            help='Remove arquivos órfãos do sistema de arquivos',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas simula as ações sem executar',
        )

    def handle(self, *args, **options):
        if options['scan']:
            self.scan_media_usage()
        
        if options['stats']:
            self.show_stats()
        
        if options['orphaned']:
            self.list_orphaned_files()
        
        if options['cleanup_orphaned']:
            self.cleanup_orphaned_files(options['dry_run'])
        
        if not any([options['scan'], options['stats'], options['orphaned'], options['cleanup_orphaned']]):
            self.stdout.write(self.style.WARNING('Use --help para ver as opções disponíveis'))

    def scan_media_usage(self):
        self.stdout.write(self.style.SUCCESS('🔍 Escaneando uso de arquivos de mídia...'))
        
        stats = scan_and_register_media_usage()
        
        self.stdout.write('')
        self.stdout.write(f'📊 Modelos escaneados: {stats["models_scanned"]}')
        self.stdout.write(f'📁 Arquivos encontrados: {stats["files_found"]}')
        self.stdout.write(f'✅ Usos registrados: {stats["usages_registered"]}')
        
        if stats['errors']:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f'⚠️  {len(stats["errors"])} erros encontrados:'))
            for error in stats['errors'][:10]:  # Mostrar apenas os primeiros 10
                self.stdout.write(f'  - {error}')
            
            if len(stats['errors']) > 10:
                self.stdout.write(f'  ... e mais {len(stats["errors"]) - 10} erros')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🎉 Escaneamento concluído!'))

    def show_stats(self):
        self.stdout.write(self.style.SUCCESS('📈 Estatísticas de Uso de Mídia'))
        self.stdout.write('=' * 50)
        
        stats = get_media_usage_stats()
        
        # Estatísticas gerais
        self.stdout.write(f'📁 Total de arquivos: {stats["total_files"]}')
        self.stdout.write(f'✅ Arquivos utilizados: {stats["used_files"]}')
        self.stdout.write(f'❌ Arquivos não utilizados: {stats["unused_files"]}')
        self.stdout.write(f'📊 Percentual de uso: {stats["usage_percentage"]:.1f}%')
        self.stdout.write(f'👻 Arquivos órfãos: {stats["orphaned_files"]}')
        
        # Uso por tipo de conteúdo
        if stats['usage_by_type']:
            self.stdout.write('')
            self.stdout.write('📋 Uso por tipo de conteúdo:')
            for content_type, count in stats['usage_by_type'].items():
                self.stdout.write(f'  • {content_type}: {count} usos')
        
        # Top arquivos mais utilizados
        if stats['top_used_files']:
            self.stdout.write('')
            self.stdout.write('🏆 Arquivos mais utilizados:')
            for i, file_info in enumerate(stats['top_used_files'], 1):
                self.stdout.write(
                    f'  {i}. {file_info["title"]} '
                    f'({file_info["file_type"]}) - {file_info["usage_count"]} usos'
                )

    def list_orphaned_files(self):
        self.stdout.write(self.style.SUCCESS('👻 Arquivos Órfãos (físicos sem registro)'))
        self.stdout.write('=' * 50)
        
        orphaned_files = find_orphaned_files()
        
        if not orphaned_files:
            self.stdout.write(self.style.SUCCESS('✅ Nenhum arquivo órfão encontrado!'))
            return
        
        self.stdout.write(f'📊 Encontrados {len(orphaned_files)} arquivos órfãos:')
        self.stdout.write('')
        
        for file_path in orphaned_files[:20]:  # Mostrar apenas os primeiros 20
            self.stdout.write(f'  📄 {file_path}')
        
        if len(orphaned_files) > 20:
            self.stdout.write(f'  ... e mais {len(orphaned_files) - 20} arquivos')
        
        self.stdout.write('')
        self.stdout.write(self.style.WARNING(
            '💡 Use --cleanup-orphaned para remover estes arquivos'
        ))

    def cleanup_orphaned_files(self, dry_run=True):
        action = 'Simulando' if dry_run else 'Executando'
        self.stdout.write(self.style.SUCCESS(f'🧹 {action} limpeza de arquivos órfãos...'))
        
        stats = cleanup_orphaned_files(dry_run=dry_run)
        
        self.stdout.write('')
        self.stdout.write(f'📊 Arquivos órfãos encontrados: {stats["found"]}')
        
        if not dry_run:
            self.stdout.write(f'✅ Arquivos deletados: {stats["deleted"]}')
            
            if stats['errors']:
                self.stdout.write(f'❌ Erros: {len(stats["errors"])}')
                for error in stats['errors'][:5]:
                    self.stdout.write(f'  - {error}')
        else:
            self.stdout.write(self.style.WARNING(
                '🔍 Modo dry-run ativo - nenhum arquivo foi deletado'
            ))
            self.stdout.write('💡 Use sem --dry-run para executar a limpeza')
        
        self.stdout.write('')
        if stats['found'] > 0:
            if dry_run:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  {stats["found"]} arquivos órfãos podem ser removidos'
                ))
            else:
                self.stdout.write(self.style.SUCCESS('🎉 Limpeza de órfãos concluída!'))
