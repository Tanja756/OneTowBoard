from django.shortcuts import redirect
from django.urls import reverse

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Не редиректим со страниц, которые нужны для завершения процесса
            exempt_urls = [
                reverse('users:complete_social_profile'),
                reverse('users:logout'),
                reverse('users:login'),
                '/accounts/',  # все URL allauth
            ]
            current_path = request.path
            if not any(current_path.startswith(url) for url in exempt_urls):
                if request.session.get('require_profile_completion'):
                    return redirect('users:complete_social_profile')
        response = self.get_response(request)
        return response