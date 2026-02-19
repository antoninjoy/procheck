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

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from langchain_google_genai import ChatGoogleGenerativeAI # <--- NEW IMPORT
from langchain_core.messages import HumanMessage

# Load API Key once when server starts
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log them in immediately
            return redirect('student_chat')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

# main/views.py

# ... imports ...

@login_required
def student_chat(request):
    response_message = None
    message_class = ""
    similar_project = None
    similarity_score = 0
    suggestions = None # <--- NEW VARIABLE
    my_projects = Project.objects.filter(student=request.user).order_by('-created_at')

    if request.method == 'POST':
        user_title = request.POST.get('title')
        user_abstract = request.POST.get('abstract')
        full_text = f"Title: {user_title}\nAbstract: {user_abstract}"

        if Project.objects.filter(title__iexact=user_title).exists():
             response_message = f"⚠️ Hold on! A project with the title '{user_title}' already exists."
             message_class = "warning"
        else:
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
                vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
                
                results = vector_db.similarity_search_with_score(full_text, k=1)
                
                if results:
                    best_match = results[0][0]
                    score = results[0][1]
                    similarity_score = round(score, 4)
                    
                    # --- DUPLICATE DETECTED LOGIC ---
                    # ... inside the "if score < 0.50" block ...
                    if score < 0.50: 
                        similar_project = best_match.metadata.get('original_title', 'Unknown Project')
                        response_message = f"⚠️ Duplicate Detected! Your idea is too similar to: '{similar_project}'"
                        message_class = "warning"
                        
                        # --- NEW: ASK GEMINI (With "Anti-Duplicate" & "No-Markdown" Rules) ---
                        try:
                            llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", google_api_key=GOOGLE_API_KEY)
                            
                            # 1. STRICTER PROMPT
                            prompt_text = f"""
                            The student proposed a project: "{user_title}" ({user_abstract}).
                            It was rejected because it duplicates: "{similar_project}".
                            
                            Generate 3 alternative, advanced project ideas based on the student's interest.
                            
                            CRITICAL RULES:
                            1. The new ideas must be DIFFERENT from "{similar_project}".
                            2. Output ONLY an HTML list (<ul><li>...</li></ul>).
                            3. Use <b> tags for titles.
                            4. DO NOT use Markdown characters like ** or ### or *.
                            5. Do not include introductory text like "Here are suggestions".
                            """
                            
                            # 2. GET RESPONSE
                            ai_response = llm.invoke([HumanMessage(content=prompt_text)])
                            
                            # 3. UNWRAP & CLEAN CONTENT
                            raw_content = ai_response.content
                            suggestions = ""

                            # Handle List vs String (The "Envelope" Fix)
                            if isinstance(raw_content, list):
                                for part in raw_content:
                                    if isinstance(part, dict) and 'text' in part:
                                        suggestions += part['text']
                                    elif isinstance(part, str):
                                        suggestions += part
                            else:
                                suggestions = raw_content

                            # 4. FINAL SCRUB (Remove any leftover artifacts)
                            suggestions = suggestions.replace("```html", "").replace("```", "") # Remove code blocks
                            suggestions = suggestions.replace("**", "")  # Remove bold markdown
                            suggestions = suggestions.replace("###", "") # Remove header markdown
                            suggestions = suggestions.replace("* ", "")  # Remove bullet markdown (if any)
                            
                        except Exception as ai_e:
                            print(f"Error generating suggestions: {ai_e}")
                        # ----------------------------------------------------------------------

                    else:
                        # (Success Logic remains the same)
                        Project.objects.create(
                            student=request.user,
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
        'similarity_score': similarity_score,
        'my_projects': my_projects,
        'suggestions': suggestions # <--- Pass to Template
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
                embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
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