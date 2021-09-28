from django.urls import path, include
from .views import ocr

app_name = 'core'

urlpatterns = [
    path('ocr/', ocr, name='home_view'),
]
