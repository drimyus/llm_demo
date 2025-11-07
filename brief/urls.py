from django.urls import path
from .views import generate_brief_endpoint

urlpatterns = [
    path('generate_brief', generate_brief_endpoint, name='generate_brief'),
    path('generate_brief/', generate_brief_endpoint),
]
