from django.conf import settings

class AdminSessionCookieMiddleware:
    """
    Use a different session cookie for /admin/ so admin and main site sessions don't conflict.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            request.session_cookie_name = 'sessionid_admin'
            # Patch the session cookie name for this request
            settings.SESSION_COOKIE_NAME = 'sessionid_admin'
        else:
            settings.SESSION_COOKIE_NAME = 'sessionid_main'
        response = self.get_response(request)
        return response
