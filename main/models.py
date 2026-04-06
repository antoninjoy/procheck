from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
import shutil

class Project(models.Model):
    # Choices for the status dropdown
    STATUS_CHOICES = [
        ('PENDING', 'Pending Mentor Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    # Link the project to a specific Student (User)
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_mentor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentored_projects')
    # The core data
    title = models.CharField(max_length=200)
    abstract = models.TextField()
    
    # Tracking the process
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    mentor_comment = models.TextField(blank=True, null=True) # If rejected, why?
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"
@receiver(post_delete, sender=Project)
def sync_faiss_on_delete(sender, instance, **kwargs):
    """
    This function runs automatically EVERY TIME a project is deleted.
    If the deleted project was 'APPROVED', it rebuilds the FAISS index.
    """
    if instance.status == 'APPROVED':
        print(f"🗑️ Approved project '{instance.title}' deleted. Rebuilding AI Brain...")
        
        # We have to import these inside the function to avoid circular import errors
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
        from dotenv import load_dotenv
        
        load_dotenv()
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        
        # 1. Get all currently approved projects
        approved_projects = Project.objects.filter(status='APPROVED')
        
        # 2. If there are no approved projects left, delete the FAISS folder entirely
        if not approved_projects.exists():
            if os.path.exists("faiss_index"):
                shutil.rmtree("faiss_index")
                print("🧹 AI Brain wiped completely (No approved projects left).")
            return

        # 3. If there are projects, gather them all up
        docs = []
        for p in approved_projects:
            combined_text = f"Title: {p.title}\nAbstract: {p.abstract}"
            metadata = {
                "student_name": p.student.username,
                "status": "APPROVED",
                "original_title": p.title
            }
            docs.append(Document(page_content=combined_text, metadata=metadata))
            
        # 4. Rebuild the index from scratch
        try:
            embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
            
            # FAISS.from_documents creates a BRAND NEW index, overwriting the old memory
            vector_db = FAISS.from_documents(docs, embeddings) 
            vector_db.save_local("faiss_index")
            print("✅ AI Brain successfully synced with database!")
            
        except Exception as e:
            print(f"❌ Error rebuilding FAISS: {e}")
    