import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

# 1. Load API Key
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    print("❌ Error: GOOGLE_API_KEY not found.")
    exit()

# 2. Initialize Embeddings (Must be same model as ingestion!)
print("🔄 Loading the brain (FAISS Index)...")
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# 3. Load the Database
try:
    # "allow_dangerous_deserialization" is needed for local files (it's safe here)
    new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    print("✅ Database loaded successfully.")
except Exception as e:
    print(f"❌ Error loading database: {e}")
    exit()

# 4. The "Student's" New Idea
student_idea = "I want to build a software to manage books in a library. It will help students borrow books and check return dates."
print(f"\n👤 Student Proposed: '{student_idea}'\n")

# 5. Perform the Search
# k=3 means "Find the top 3 most similar projects"
print("🔍 Searching for duplicates...")
results = new_db.similarity_search_with_score(student_idea, k=3)

# 6. Show Results
for doc, score in results:
    # FAISS scores are "L2 Distance" (Lower is better/more similar)
    # 0 = Exact Match
    # > 1 = Very different
    print(f"------------------------------------------------")
    print(f"📄 Found Project: {doc.metadata['original_title']}")
    print(f"📊 Similarity Distance: {score:.4f}")
    print(f"📝 Abstract Snippet: {doc.page_content[:100]}...")