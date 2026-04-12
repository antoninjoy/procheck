import os
from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomSignUpForm
from django.contrib.admin.views.decorators import staff_member_required
from .models import Project
from django.contrib.auth.models import User

# AI Libraries
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document 
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Load API Key once when server starts
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def signup(request):
    if request.method == 'POST':
        # --- UPDATED: Using your custom form with email/phone ---
        form = CustomSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Log them in immediately
            return redirect('dashboard_redirect')
    else:
        # --- UPDATED: Using your custom form for GET requests ---
        form = CustomSignUpForm()
    
    # NOTE: Ensure your HTML file is located at templates/registration/signup.html
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def dashboard_redirect(request):
    if request.user.is_staff:
        return redirect('mentor_dashboard')
    else:
        return redirect('student_chat')

@login_required
def student_chat(request):
    response_message = None
    message_class = ""
    similar_project = None
    similarity_score = 0
    suggestions = None 
    my_projects = Project.objects.filter(student=request.user).order_by('-created_at')
    
    # Fetch all mentors (staff members) to show in the dropdown
    mentors = User.objects.filter(is_staff=True)

    # --- NEW VARIABLES FOR JAVASCRIPT ---
    needs_suggestions = False
    failed_title = ""
    failed_abstract = ""
    similar_project_name = ""

    if request.method == 'POST':
        user_title = request.POST.get('title')
        user_abstract = request.POST.get('abstract')
        
        # Get the chosen mentor's ID from the form
        mentor_id = request.POST.get('mentor_id')
        chosen_mentor = User.objects.filter(id=mentor_id).first() if mentor_id else None
        
        full_text = f"Title: {user_title}\nAbstract: {user_abstract}"

        # 0. Basic exact title check
        if Project.objects.filter(title__iexact=user_title).exists():
             response_message = f"⚠️ Hold on! A project with the exact title '{user_title}' already exists."
             message_class = "warning"
        else:
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
                is_duplicate = False

                # --- STEP 1: CHECK APPROVED PROJECTS (Permanent FAISS) ---
                if os.path.exists("faiss_index"):
                    vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
                    results = vector_db.similarity_search_with_score(full_text, k=1)
                    
                    if results and results[0][1] < 0.50:
                        is_duplicate = True
                        similar_project = results[0][0].metadata.get('original_title', 'Unknown Project')
                        similarity_score = round(results[0][1], 4)
                        response_message = f"⚠️ Duplicate Detected! Your idea is too similar to an already approved project: '{similar_project}'"
                        message_class = "warning"

                # --- STEP 2: THE FAIRNESS LOCK (In-Memory Pending Projects) ---
                if not is_duplicate:
                    # Get all projects that are currently waiting for a mentor
                    pending_projects = Project.objects.filter(status='PENDING')
                    
                    if pending_projects.exists():
                        pending_docs = []
                        for p in pending_projects:
                            doc_text = f"Title: {p.title}\nAbstract: {p.abstract}"
                            pending_docs.append(Document(page_content=doc_text, metadata={"original_title": p.title}))

                        # Create a temporary AI Brain just for pending projects
                        temp_vector_db = FAISS.from_documents(pending_docs, embeddings)
                        temp_results = temp_vector_db.similarity_search_with_score(full_text, k=1)

                        if temp_results and temp_results[0][1] < 0.50:
                            is_duplicate = True
                            similar_project = temp_results[0][0].metadata.get('original_title', 'Unknown Project')
                            similarity_score = round(temp_results[0][1], 4)
                            # Custom message for the Fairness Lock
                            response_message = f"⏳ Fairness Lock! Another student submitted a similar project ('{similar_project}') before you. It is currently in the queue for a mentor. First come, first served!"
                            message_class = "warning"

                # --- STEP 3: TRIGGER SUGGESTIONS OR SAVE ---
                if is_duplicate:
                    # If it failed either Step 1 or Step 2, trigger the Javascript AI loader
                    needs_suggestions = True
                    failed_title = user_title
                    failed_abstract = user_abstract
                    similar_project_name = similar_project
                else:
                    # It is 100% unique. Save it to the database.
                    Project.objects.create(
                        student=request.user,
                        assigned_mentor=chosen_mentor, 
                        title=user_title,
                        abstract=user_abstract,
                        status='PENDING'
                    )
                    response_message = "✅ Success! Your project is unique and has been submitted to your Mentor."
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
        'suggestions': suggestions,
        'mentors': mentors,
        
        # --- NEW VARIABLES PASSED TO HTML ---
        'needs_suggestions': needs_suggestions,
        'failed_title': failed_title,
        'failed_abstract': failed_abstract,
        'similar_project_name': similar_project_name,
    })

@staff_member_required 
def mentor_dashboard(request):
    # Filter pending projects so the mentor ONLY sees ones assigned to them
    pending_projects = Project.objects.filter(status='PENDING', assigned_mentor=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        action = request.POST.get('action') 
        mentor_comment = request.POST.get('comment', '')
        
        project = get_object_or_404(Project, id=project_id)
        
        if action == 'approve':
            project.status = 'APPROVED'
            project.mentor_comment = mentor_comment
            project.save()
            
            # --- Add to AI Brain (FAISS) ---
            try:
                embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GOOGLE_API_KEY)
                
                combined_text = f"Title: {project.title}\nAbstract: {project.abstract}"
                metadata = {
                    "student_name": project.student.username,
                    "year": str(project.created_at.year),
                    "status": "APPROVED",
                    "original_title": project.title
                }
                new_doc = Document(page_content=combined_text, metadata=metadata)
                
                # Check if we are adding to an existing brain, or making a new one
                if os.path.exists("faiss_index"):
                    vector_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
                    vector_db.add_documents([new_doc])
                else:
                    vector_db = FAISS.from_documents([new_doc], embeddings)

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

@staff_member_required
def approved_projects(request):
    # This remains unfiltered so all mentors can see the global database of approved projects
    projects = Project.objects.filter(status='APPROVED').order_by('-created_at')
    return render(request, 'main/approved_projects.html', {'projects': projects})

@login_required
def generate_suggestions_api(request):
    if request.method == 'POST':
        user_title = request.POST.get('title')
        user_abstract = request.POST.get('abstract')
        similar_project = request.POST.get('similar_project')
        
        try:
            llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", google_api_key=GOOGLE_API_KEY)
            
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
            
            ai_response = llm.invoke([HumanMessage(content=prompt_text)])
            raw_content = ai_response.content
            suggestions = ""

            if isinstance(raw_content, list):
                for part in raw_content:
                    if isinstance(part, dict) and 'text' in part:
                        suggestions += part['text']
                    elif isinstance(part, str):
                        suggestions += part
            else:
                suggestions = raw_content

            # Clean up formatting
            suggestions = suggestions.replace("```html", "").replace("```", "")
            
            return JsonResponse({'status': 'success', 'suggestions': suggestions})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'invalid request'}, status=400)