from django.urls import path
from .views import analyze_area

urlpatterns = [
    path('analyze/', analyze_area, name='analyze-area'),
]
