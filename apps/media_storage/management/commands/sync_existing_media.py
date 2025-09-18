from django.core.management.base import BaseCommand
from django.conf import settings
from apps.media_storage.models import MediaFile, MediaCategory
import os
import mimetypes
from PIL import Image


class Command(BaseCommand):
    help = 'Sincroniza arquivos existentes na pasta media com o banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--folder',
            type=str,
            help='Pasta específica dentro de media/ para sincronizar',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Nome da categoria para os arquivos importados',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Apenas mostra os arquivos que seriam importados',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔄 Sincronizando arquivos existentes...'))
        
        media_root = settings.MEDIA_ROOT
        folder = options.get('folder', '')
        category_name = options.get('category')
        dry_run = options.get('dry_run', False)
        
        # Obter ou criar categoria
        category = None
        if category_name:
            category, created = MediaCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': f'Categoria criada automaticamente para {category_name}'}
            )
            if created:
                self.stdout.write(f'📁 Categoria "{category_name}" criada')
        
        # Pasta base para buscar arquivos
        search_path = os.path.join(media_root, folder) if folder else media_root
        
        if not os.path.exists(search_path):
            self.stdout.write(self.style.ERROR(f'❌ Pasta não encontrada: {search_path}'))
            return
        
        imported_count = 0
        skipped_count = 0
        
        # Extensões suportadas
        supported_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',  # Imagens
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',   # Vídeos
            '.mp3', '.wav', '.ogg', '.flac', '.aac',          # Áudios
            '.pdf', '.doc', '.docx', '.txt', '.rtf',          # Documentos
            '.zip', '.rar', '.7z', '.tar', '.gz'              # Arquivos
        ]
        
        for root, dirs, files in os.walk(search_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, media_root)
                
                # Verificar extensão
                ext = os.path.splitext(file)[1].lower()
                if ext not in supported_extensions:
                    continue
                
                # Verificar se já existe no banco
                if MediaFile.objects.filter(file=relative_path).exists():
                    skipped_count += 1
                    continue
                
                if dry_run:
                    self.stdout.write(f'  📄 Seria importado: {relative_path}')
                    imported_count += 1
                    continue
                
                # Criar registro no banco
                try:
                    # Gerar título baseado no nome do arquivo
                    title = os.path.splitext(file)[0].replace('_', ' ').replace('-', ' ').title()
                    
                    # Obter informações do arquivo
                    file_size = os.path.getsize(file_path)
                    mime_type = mimetypes.guess_type(file_path)[0] or ''
                    
                    # Criar MediaFile
                    media_file = MediaFile(
                        title=title,
                        file=relative_path,
                        category=category,
                        file_size=file_size,
                        mime_type=mime_type,
                        is_public=True,
                        is_active=True
                    )
                    
                    # Definir tipo de arquivo
                    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
                        media_file.file_type = 'image'
                        # Obter dimensões para imagens (exceto SVG)
                        if ext != '.svg':
                            try:
                                with Image.open(file_path) as img:
                                    media_file.width, media_file.height = img.size
                            except Exception:
                                pass
                    elif ext in ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']:
                        media_file.file_type = 'video'
                    elif ext in ['.mp3', '.wav', '.ogg', '.flac', '.aac']:
                        media_file.file_type = 'audio'
                    elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                        media_file.file_type = 'document'
                    else:
                        media_file.file_type = 'other'
                    
                    media_file.save()
                    imported_count += 1
                    self.stdout.write(f'  ✅ Importado: {title}')
                    
                except Exception as e:
                    self.stdout.write(f'  ❌ Erro ao importar {file}: {e}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'🔍 Modo dry-run: {imported_count} arquivos seriam importados')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'🎉 Sincronização concluída! {imported_count} arquivos importados, {skipped_count} ignorados')
            )
