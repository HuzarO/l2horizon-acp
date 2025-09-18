from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from .models import MediaFile, MediaCategory
import tempfile
from PIL import Image
import io

User = get_user_model()


class MediaStorageTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.category = MediaCategory.objects.create(
            name='Test Category',
            description='A test category'
        )

    def create_test_image(self):
        """Cria uma imagem de teste"""
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = io.BytesIO()
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        return SimpleUploadedFile(
            'test_image.jpg',
            temp_file.getvalue(),
            content_type='image/jpeg'
        )

    def test_media_file_creation(self):
        """Testa a criação de um arquivo de mídia"""
        image_file = self.create_test_image()
        
        media_file = MediaFile.objects.create(
            title='Test Image',
            description='A test image',
            file=image_file,
            category=self.category,
            uploaded_by=self.user
        )
        
        self.assertEqual(media_file.title, 'Test Image')
        self.assertEqual(media_file.file_type, 'image')
        self.assertTrue(media_file.file_size > 0)
        self.assertEqual(media_file.mime_type, 'image/jpeg')

    def test_media_list_view(self):
        """Testa a view de listagem"""
        response = self.client.get(reverse('media_storage:list'))
        self.assertEqual(response.status_code, 200)

    def test_media_upload_view(self):
        """Testa a view de upload"""
        image_file = self.create_test_image()
        
        response = self.client.post(reverse('media_storage:upload'), {
            'title': 'Test Upload',
            'description': 'Test description',
            'file': image_file,
            'category': self.category.id,
            'is_public': True,
            'tags': 'test, upload'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso
        self.assertTrue(MediaFile.objects.filter(title='Test Upload').exists())

    def test_media_category_str(self):
        """Testa o método __str__ da categoria"""
        self.assertEqual(str(self.category), 'Test Category')

    def test_file_size_human(self):
        """Testa o método file_size_human"""
        image_file = self.create_test_image()
        
        media_file = MediaFile.objects.create(
            title='Test Size',
            file=image_file,
            uploaded_by=self.user
        )
        
        size_human = media_file.file_size_human
        self.assertIn('B', size_human)  # Deve conter a unidade

    def test_file_extension_property(self):
        """Testa a propriedade file_extension"""
        image_file = self.create_test_image()
        
        media_file = MediaFile.objects.create(
            title='Test Extension',
            file=image_file,
            uploaded_by=self.user
        )
        
        self.assertEqual(media_file.file_extension, '.jpg')

    def test_is_image_property(self):
        """Testa as propriedades de tipo de arquivo"""
        image_file = self.create_test_image()
        
        media_file = MediaFile.objects.create(
            title='Test Type',
            file=image_file,
            uploaded_by=self.user
        )
        
        self.assertTrue(media_file.is_image)
        self.assertFalse(media_file.is_video)
        self.assertFalse(media_file.is_audio)
        self.assertFalse(media_file.is_document)
