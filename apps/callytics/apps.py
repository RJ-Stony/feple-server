from django.apps import AppConfig


class CallyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    # name 을 전체 경로로 지정해서 config의 settings.py에서 앱을 찾을 수 있도록
    name = 'apps.callytics'
