import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Project
from django.contrib.auth.models import User

# AI Libraries
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document # Needed to add new projects to the brain
from dotenv import load_dotenv

# Load API Key once when server starts
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def student_chat(request):
    response_message = None
    message_class = ""
    similar_project = None
    similarity_score = 0

    if request.method == 'POST':
        user_title = request.POST.get('title')
        user_abstract = request.POST.get('abstract')
        full_text = f"Title: {user_title}\nAbstract: {user_abstract}"

        # --- NEW: "Spam Stopper" Check (SQL Look up) ---
        # Before asking the AI, check if we simply already have this project pending or approved
        if Project.objects.filter(title__iexact=user_title).exists():
             response_message = f"⚠️ Hold on! A project with the title '{user_title}' already exists in the database (Pending or Approved)."
             message_class = "warning"
        
        # --- END NEW CHECK ---
        
        else:
            # 1. Load the AI Brain (FAISS)
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GOOGLE_API_KEY)
                vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
                
                # 2. Perform Similarity Search
                results = vector_db.similarity_search_with_score(full_text, k=1)
                
                if results:
                    best_match = results[0][0]
                    score = results[0][1]
                    similarity_score = round(score, 4)
                    
                    if score < 0.85:
                        response_message = f"⚠️ Duplicate Detected! Your idea is too similar to: '{best_match.metadata.get('original_title', 'Unknown')}'"
                        similar_project = best_match.metadata.get('original_title', 'Unknown Project')
                        message_class = "warning"
                    else:
                        # 3. Success! Save to Database
                        student_user = User.objects.first() 
                        Project.objects.create(
                            student=student_user,
                            title=user_title,
                            abstract=user_abstract,
                            status='PENDING'
                        )
                        response_message = "✅ Success! Your project is unique and has been submitted for Mentor Review."
                        message_class = "success"
                        
            except Exception as e:
                response_message = f"Error: {str(e)}"
                message_class = "warning"

    return render(request, 'main/student_chat.html', {
        'response_message': response_message,
        'message_class': message_class,
        'similar_project': similar_project,
        'similarity_score': similarity_score
    })

# --- NEW: Mentor Dashboard View ---
@staff_member_required # Only admins/mentors can see this
def mentor_dashboard(request):
    # Get all projects that are waiting for review
    pending_projects = Project.objects.filter(status='PENDING').order_by('-created_at')
    
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        action = request.POST.get('action') # 'approve' or 'reject'
        mentor_comment = request.POST.get('comment', '')
        
        project = get_object_or_404(Project, id=project_id)
        
        if action == 'approve':
            project.status = 'APPROVED'
            project.save()
            
            # --- CRITICAL: Add to AI Brain (FAISS) ---
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GOOGLE_API_KEY)
                vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
                
                # Prepare the new document
                combined_text = f"Title: {project.title}\nAbstract: {project.abstract}"
                metadata = {
                    "student_name": project.student.username,
                    "year": str(project.created_at.year),
                    "status": "APPROVED",
                    "original_title": project.title
                }
                new_doc = Document(page_content=combined_text, metadata=metadata)
                
                # Add and Save
                vector_db.add_documents([new_doc])
                vector_db.save_local("faiss_index")
                print(f"✅ Project '{project.title}' added to FAISS index.")
                
            except Exception as e:
                print(f"❌ Error updating FAISS: {e}")
                
        elif action == 'reject':
            project.status = 'REJECTED'
            project.mentor_comment = mentor_comment
            project.save()
            
        return redirect('mentor_dashboard')

    return render(request, 'main/mentor_dashboard.html', {'projects': pending_projects})