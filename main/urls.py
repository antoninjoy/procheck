from django.urls import path
from . import views

urlpatterns = [
    # The default home page (Student Chat)
    path('', views.student_chat, name='student_chat'),
    
    # The new route for the Mentor Dashboard
    path('mentor/', views.mentor_dashboard, name='mentor_dashboard'),
]