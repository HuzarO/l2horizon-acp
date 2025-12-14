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
        Usa signal post_migrate para evitar warning de acesso ao banco durante inicialização
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
        
        # Usa signal post_migrate para executar após as migrations estarem prontas
        # Isso evita o warning de acesso ao banco durante inicialização
        from django.db.models.signals import post_migrate
        
        def populate_resources_handler(sender, **kwargs):
            """Handler que executa após as migrations"""
            global _populate_resources_executed
            if _populate_resources_executed:
                return
            
            try:
                logger.info("🔄 Populando recursos do sistema...")
                call_command('populate_resources', verbosity=0)
                _populate_resources_executed = True
                logger.info("✅ Recursos do sistema populados com sucesso!")
            except Exception as e:
                logger.error(f"❌ Erro ao popular recursos do sistema: {e}")
        
        # Conecta o signal apenas uma vez
        if not hasattr(ResourcesConfig, '_signal_connected'):
            post_migrate.connect(populate_resources_handler, sender=self, weak=False)
            ResourcesConfig._signal_connected = True
        
        # Para servidores já rodando (não em modo de migração), executa imediatamente
        # mas apenas se não estiver em um contexto de migração
        if 'runserver' in sys.argv or 'daphne' in sys.argv[0] or 'gunicorn' in sys.argv[0]:
            # Usa threading para executar após um pequeno delay, quando o Django já estiver pronto
            import threading
            def delayed_populate():
                import time
                time.sleep(1)  # Aguarda 1 segundo para garantir que tudo está pronto
                if not _populate_resources_executed:
                    try:
                        # Verifica se o banco está disponível
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT 1")
                        # Se chegou aqui, o banco está pronto
                        populate_resources_handler(sender=self)
                    except (OperationalError, Exception):
                        pass  # Ignora se o banco ainda não estiver pronto
            
            thread = threading.Thread(target=delayed_populate, daemon=True)
            thread.start()
