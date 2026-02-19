# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_chat, name='student_chat'),
    path('signup/', views.signup, name='signup'),
    path('mentor/', views.mentor_dashboard, name='mentor_dashboard'),
]