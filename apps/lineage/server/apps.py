from django.apps import AppConfig
import threading
import sys


class ServerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.lineage.server'
    verbose_name = 'Servidor'

    def ready(self):
        # Importa signals apenas para registrar handlers
        import apps.lineage.server.signals
        
        # Executa verificação de colunas de forma lazy (em thread separada)
        # para evitar warning de acesso ao banco durante inicialização
        if not any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'test']):
            def delayed_ensure_columns():
                import time
                time.sleep(1)  # Aguarda 1 segundo para garantir que tudo está pronto
                apps.lineage.server.signals.ensure_lineage_columns()
            
            thread = threading.Thread(target=delayed_ensure_columns, daemon=True)
            thread.start()
