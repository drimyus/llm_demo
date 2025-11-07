from django.contrib import admin
from django.urls import path, include
from brief.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('brief.urls')),
    path('', home, name='home'),
]
