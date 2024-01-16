from django.urls import path
from . import views

urlpatterns = [

    path('', views.chat, name='chat'),
    path('ai-response/', views.ai_response, name='ai_response'),
]