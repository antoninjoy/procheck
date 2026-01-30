from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    # Choices for the status dropdown
    STATUS_CHOICES = [
        ('PENDING', 'Pending Mentor Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    # Link the project to a specific Student (User)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # The core data
    title = models.CharField(max_length=200)
    abstract = models.TextField()
    
    # Tracking the process
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    mentor_comment = models.TextField(blank=True, null=True) # If rejected, why?
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"