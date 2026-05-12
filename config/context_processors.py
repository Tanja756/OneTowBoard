from django.conf import settings

def site_settings(request):
    return {
        'site_name': settings.SITE_NAME,
        'site_description': settings.SITE_DESCRIPTION,
        'site_keywords': settings.SITE_KEYWORDS,
        'site_address': getattr(settings, 'SITE_ADDRESS', ''),
        'site_phone': getattr(settings, 'SITE_PHONE', ''),
        'site_email': getattr(settings, 'SITE_EMAIL', ''),
        'site_working_hours': getattr(settings, 'SITE_WORKING_HOURS', ''),
        'enable_google_auth': settings.ENABLE_GOOGLE_AUTH,
    }