from django.core.management.base import BaseCommand
from apps.media_storage.models import MediaFile


class Command(BaseCommand):
    help = 'Gera thumbnails para imagens existentes que não possuem'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenera thumbnails mesmo se já existirem',
        )
        parser.add_argument(
            '--size',
            type=int,
            default=300,
            help='Tamanho do thumbnail (padrão: 300px)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🖼️  Gerando thumbnails...'))
        
        force = options.get('force', False)
        size = options.get('size', 300)
        thumbnail_size = (size, size)
        
        # Buscar imagens
        if force:
            images = MediaFile.objects.filter(file_type='image', is_active=True)
            self.stdout.write(f'📊 Processando {images.count()} imagens (forçando regeneração)...')
        else:
            images = MediaFile.objects.filter(
                file_type='image', 
                is_active=True, 
                thumbnail__isnull=True
            )
            self.stdout.write(f'📊 Encontradas {images.count()} imagens sem thumbnail...')
        
        if images.count() == 0:
            self.stdout.write(self.style.SUCCESS('✅ Todas as imagens já possuem thumbnails!'))
            return
        
        success_count = 0
        error_count = 0
        
        for image in images:
            try:
                # Limpar thumbnail existente se forçando
                if force and image.thumbnail:
                    image.delete_thumbnail()
                    image.thumbnail = None
                    image.thumbnail_width = None
                    image.thumbnail_height = None
                
                # Criar thumbnail
                if image.create_thumbnail(size=thumbnail_size):
                    image.save(update_fields=['thumbnail', 'thumbnail_width', 'thumbnail_height'])
                    success_count += 1
                    self.stdout.write(f'  ✅ {image.title}')
                else:
                    error_count += 1
                    self.stdout.write(f'  ❌ Erro: {image.title}')
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(f'  ❌ Erro em {image.title}: {e}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🎉 Processo concluído!'))
        self.stdout.write(f'✅ Thumbnails criados: {success_count}')
        self.stdout.write(f'❌ Erros: {error_count}')
        self.stdout.write(f'📏 Tamanho usado: {size}x{size}px')
        
        if success_count > 0:
            self.stdout.write('')
            self.stdout.write('🚀 Agora a listagem de mídias será muito mais rápida!')
            self.stdout.write('   Acesse http://localhost:8000/app/media/ para ver o resultado')
