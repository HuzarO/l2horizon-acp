from django.core.management.base import BaseCommand
from apps.media_storage.models import MediaCategory


class Command(BaseCommand):
    help = 'Cria categorias padrão para o sistema de mídia'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📁 Criando categorias padrão...'))
        
        # Categorias padrão
        default_categories = [
            {
                'name': 'Imagens',
                'description': 'Imagens gerais, fotos, ilustrações e gráficos'
            },
            {
                'name': 'Documentos',
                'description': 'PDFs, documentos de texto e arquivos de escritório'
            },
            {
                'name': 'Vídeos',
                'description': 'Vídeos promocionais, tutoriais e conteúdo audiovisual'
            },
            {
                'name': 'Áudios',
                'description': 'Arquivos de áudio, música e podcasts'
            },
            {
                'name': 'Notícias',
                'description': 'Imagens e arquivos relacionados a notícias e artigos'
            },
            {
                'name': 'Banners',
                'description': 'Banners promocionais e imagens de destaque'
            },
            {
                'name': 'Avatares',
                'description': 'Fotos de perfil e avatares de usuários'
            },
            {
                'name': 'Logos',
                'description': 'Logotipos e identidade visual'
            },
            {
                'name': 'Arquivos',
                'description': 'Arquivos compactados e downloads diversos'
            }
        ]
        
        created_count = 0
        existing_count = 0
        
        for category_data in default_categories:
            category, created = MediaCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ Criada: {category.name}')
            else:
                existing_count += 1
                self.stdout.write(f'  ⚠️  Já existe: {category.name}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'🎉 Processo concluído!'))
        self.stdout.write(f'📊 Categorias criadas: {created_count}')
        self.stdout.write(f'📊 Já existiam: {existing_count}')
        self.stdout.write(f'📊 Total disponível: {MediaCategory.objects.count()}')
        
        if created_count > 0:
            self.stdout.write('')
            self.stdout.write('🚀 Agora você pode:')
            self.stdout.write('   1. Acessar http://localhost:8000/app/media/ para fazer uploads')
            self.stdout.write('   2. Usar as categorias criadas para organizar seus arquivos')
            self.stdout.write('   3. Criar mais categorias no admin se necessário')
