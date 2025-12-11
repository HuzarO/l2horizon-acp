from django.apps import AppConfig
from django.core.management import call_command
from django.db import connection
from django.db.utils import OperationalError
import logging
import sys
import os

logger = logging.getLogger(__name__)

# Flag global para evitar execução múltipla
_populate_resources_executed = False


class ResourcesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.main.resources'
    verbose_name = 'Recursos do Sistema'

    def ready(self):
        """
        Executa o comando populate_resources automaticamente quando a aplicação inicia
        """
        global _populate_resources_executed
        
        # Evita execução múltipla (reload do servidor de desenvolvimento)
        if _populate_resources_executed:
            return
        
        # Evita executar durante migrations, makemigrations, collectstatic, test, etc.
        excluded_commands = [
            'migrate', 'makemigrations', 'collectstatic', 'test', 
            'shell', 'shell_plus', 'dbshell', 'sqlmigrate', 'showmigrations'
        ]
        
        if any(cmd in sys.argv for cmd in excluded_commands):
            return
        
        # Evita executar em processos de worker do Celery
        if 'celery' in sys.argv[0] or 'celery' in ' '.join(sys.argv):
            return
        
        # Verifica se está rodando em ambiente de teste
        if os.environ.get('DJANGO_SETTINGS_MODULE', '').endswith('.test_settings'):
            return
        
        # Verifica se o banco de dados está disponível
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except (OperationalError, Exception) as e:
            logger.debug(f"Banco de dados não disponível ainda: {e}")
            return
        
        # Executa o comando populate_resources
        try:
            logger.info("🔄 Populando recursos do sistema...")
            call_command('populate_resources', verbosity=0)
            _populate_resources_executed = True
            logger.info("✅ Recursos do sistema populados com sucesso!")
        except Exception as e:
            logger.error(f"❌ Erro ao popular recursos do sistema: {e}")
            # Não interrompe a inicialização da aplicação em caso de erro
            # O comando pode ser executado manualmente depois
