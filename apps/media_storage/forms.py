from django import forms
from django.core.exceptions import ValidationError
from .models import MediaFile, MediaCategory


class MultipleFileInput(forms.FileInput):
    """Widget personalizado para múltiplos arquivos"""
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs['multiple'] = True
        super().__init__(attrs)


class MultipleFileField(forms.FileField):
    """Campo personalizado para múltiplos arquivos"""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Não fazer validação aqui, será feita na view
        return data


class MediaFileForm(forms.ModelForm):
    """Formulário para upload e edição de arquivos de mídia"""
    
    class Meta:
        model = MediaFile
        fields = [
            'title', 'description', 'file', 'category', 
            'is_public', 'tags'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite o título do arquivo'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição opcional do arquivo'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.jpg,.jpeg,.png,.gif,.webp,.svg,.mp4,.avi,.mov,.wmv,.flv,.webm,.mp3,.wav,.ogg,.flac,.aac,.pdf,.doc,.docx,.txt,.rtf,.zip,.rar,.7z,.tar,.gz'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tags separadas por vírgula'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = "Selecione uma categoria"
        self.fields['category'].required = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Verificar tamanho do arquivo (máximo 100MB)
            if file.size > 100 * 1024 * 1024:
                raise ValidationError('O arquivo é muito grande. Tamanho máximo permitido: 100MB')
            
            # Verificar extensão do arquivo
            allowed_extensions = [
                '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',  # Imagens
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',   # Vídeos
                '.mp3', '.wav', '.ogg', '.flac', '.aac',          # Áudios
                '.pdf', '.doc', '.docx', '.txt', '.rtf',          # Documentos
                '.zip', '.rar', '.7z', '.tar', '.gz'              # Arquivos
            ]
            
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f'Extensão de arquivo não permitida: {ext}')
        
        return file

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if tags:
            # Limpar e validar tags
            tag_list = [tag.strip() for tag in tags.split(',')]
            tag_list = [tag for tag in tag_list if tag]  # Remove tags vazias
            return ', '.join(tag_list)
        return tags


class MediaFileFilterForm(forms.Form):
    """Formulário para filtros de busca"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título, descrição ou tags...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=MediaCategory.objects.all(),
        required=False,
        empty_label="Todas as categorias",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    file_type = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + MediaFile.FILE_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_public = forms.ChoiceField(
        choices=[
            ('', 'Todos'),
            ('true', 'Públicos'),
            ('false', 'Privados')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class BulkUploadForm(forms.Form):
    """Formulário para upload em lote"""
    
    files = MultipleFileField(
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'accept': '.jpg,.jpeg,.png,.gif,.webp,.svg,.mp4,.avi,.mov,.wmv,.flv,.webm,.mp3,.wav,.ogg,.flac,.aac,.pdf,.doc,.docx,.txt,.rtf,.zip,.rar,.7z,.tar,.gz'
        }),
        help_text='Selecione múltiplos arquivos para upload em lote',
        required=False  # Validação será feita na view
    )
    
    category = forms.ModelChoiceField(
        queryset=MediaCategory.objects.all(),
        required=False,
        empty_label="Selecione uma categoria (opcional)",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    is_public = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Marque para tornar os arquivos públicos'
    )

    # Validação será feita na view para múltiplos arquivos


class MediaCategoryForm(forms.ModelForm):
    """Formulário para categorias de mídia"""
    
    class Meta:
        model = MediaCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descrição da categoria'
            })
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Verificar se já existe uma categoria com este nome
            existing = MediaCategory.objects.filter(name__iexact=name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('Já existe uma categoria com este nome.')
        
        return name
