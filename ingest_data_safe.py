import os
import csv
import time
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# 1. Load API Key
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    print("❌ Error: GOOGLE_API_KEY not found.")
    exit()

print("✅ API Key found.")

# 2. Use the NEWER Model
embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

# 3. Read CSV
projects = []
try:
    with open("past_projects.csv", newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            combined_text = f"Title: {row['Title']}\nAbstract: {row['Abstract']}"
            
            # --- FIX IS HERE: Added 'original_title' back to metadata ---
            metadata = {
                "student_name": row['Student_Name'],
                "year": row['Year'],
                "status": row['Status'],
                "original_title": row['Title'] 
            }
            # ------------------------------------------------------------
            
            doc = Document(page_content=combined_text, metadata=metadata)
            projects.append(doc)
    print(f"✅ Loaded {len(projects)} projects.")
except FileNotFoundError:
    print("❌ Error: past_projects.csv not found.")
    exit()

# 4. Slow Ingestion (One by One)
print("⏳ Processing vectors one by one to avoid rate limits...")
vector_db = None

for i, doc in enumerate(projects):
    # This print statement will now work correctly too
    print(f"   Processing project {i+1}/{len(projects)}: {doc.metadata['original_title']}")
    
    if vector_db is None:
        vector_db = FAISS.from_documents([doc], embeddings)
    else:
        vector_db.add_documents([doc])
    
    time.sleep(2) # Wait to keep Google happy

# 5. Save
vector_db.save_local("faiss_index")
print("🎉 Success! Database created with TITLES in 'faiss_index' folder.")