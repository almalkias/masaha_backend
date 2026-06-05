from django.utils import translation


class LanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = request.headers.get("X-Language", "ar")
        translation.activate(language)
        request.LANGUAGE_CODE = language

        response = self.get_response(request)

        translation.deactivate()
        return response
