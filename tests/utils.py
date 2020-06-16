from django.http import HttpResponse


class WrapperResponse(HttpResponse):
    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
