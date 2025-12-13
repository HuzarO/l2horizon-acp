from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.main.ai_assistant'
    verbose_name = 'Assistente de IA'

    def ready(self):
        import apps.main.ai_assistant.signals  # noqa
