from django.apps import AppConfig

class AutenticacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'autenticacion'

    def ready(self):
        from .startup import reset_root_password
        reset_root_password()