from dataclasses import dataclass, field
from django.http import JsonResponse

# Duck typing a request.
@dataclass
class DummyRequest:
    headers: dict = field(default_factory=dict)
    GET: dict = field(default_factory=dict)


def get_response(_request):
    return JsonResponse({"message": "OK"})
