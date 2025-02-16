
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path
from .views import home 

urlpatterns = [
    path('', home, name='home'),  # Bosh sahifaga kirganda home funksiyasini chaqiramiz
]

if settings.DEBUG:  # Faqat local development uchun
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
