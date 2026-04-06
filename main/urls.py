# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 1. The Homepage is now the Traffic Cop
    path('', views.dashboard_redirect, name='dashboard_redirect'), 
    
    # 2. Student chat gets its own dedicated URL
    path('student/', views.student_chat, name='student_chat'),     
    
    # 3. Mentor dashboard stays the same
    path('mentor/', views.mentor_dashboard, name='mentor_dashboard'),
    
    # 4. Signup stays the same
    path('signup/', views.signup, name='signup'),

    path('mentor/approved/', views.approved_projects, name='approved_projects'),
]