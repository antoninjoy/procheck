import os
import django
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# 1. Setup Django Environment
# This allows us to access the SQL Database from this script
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procheck_web.settings')
django.setup()

from main.models import Project

# 2. Load API Key
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    print("❌ Error: GOOGLE_API_KEY not found.")
    exit()

print("🔄 Connecting to SQL Database...")

# 3. Fetch ONLY Approved projects
approved_projects = Project.objects.filter(status='APPROVED')
print(f"✅ Found {approved_projects.count()} APPROVED projects in SQL.")

if approved_projects.count() == 0:
    print("⚠️ No approved projects found. Brain will be empty.")
    exit()

# 4. Prepare Documents for the AI
documents = []
for proj in approved_projects:
    combined_text = f"Title: {proj.title}\nAbstract: {proj.abstract}"
    metadata = {
        "student_name": proj.student.username,
        "year": str(proj.created_at.year),
        "status": "APPROVED",
        "original_title": proj.title
    }
    doc = Document(page_content=combined_text, metadata=metadata)
    documents.append(doc)

# 5. Rebuild the Brain
print("🧠 Rebuilding FAISS Index (This calls Google API, please wait)...")

try:
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    
    # Create fresh DB
    vector_db = FAISS.from_documents(documents, embeddings)
    
    # Save (Overwrite old index)
    vector_db.save_local("faiss_index")
    print("🎉 Success! The AI Brain is now 100% in sync with the SQL Database.")

except Exception as e:
    print(f"❌ Error rebuilding brain: {e}")