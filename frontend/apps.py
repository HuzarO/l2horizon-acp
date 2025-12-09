from django.apps import AppConfig
from pathlib import Path


class FrontendConfig(AppConfig):
    """Configuração do app frontend"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend'
    # Especificar explicitamente o caminho para evitar conflitos no Windows
    # quando há diferença de case no drive letter (D:\ vs d:\)
    path = Path(__file__).parent.resolve()

