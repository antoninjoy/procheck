import os
import csv
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS  # <--- We are using FAISS now
from langchain_core.documents import Document

# 1. Load the API Key
load_dotenv()
if "GOOGLE_API_KEY" not in os.environ:
    print("❌ Error: GOOGLE_API_KEY not found in .env file")
    exit()

print("✅ API Key found. Starting ingestion...")

# 2. Initialize Embeddings
# This translates text into numbers
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# 3. Read CSV
projects = []
csv_file_path = "past_projects.csv"

try:
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Combine Title and Abstract for the "Searchable" text
            combined_text = f"Title: {row['Title']}\nAbstract: {row['Abstract']}"
            
            # Keep the details separate for when we need to display them
            metadata = {
                "student_name": row['Student_Name'],
                "year": row['Year'],
                "status": row['Status'],
                "original_title": row['Title']
            }
            
            # Create a Document object
            doc = Document(page_content=combined_text, metadata=metadata)
            projects.append(doc)

    print(f"✅ Loaded {len(projects)} projects from CSV.")

except FileNotFoundError:
    print("❌ Error: past_projects.csv not found. Please create it first.")
    exit()

# 4. Save to FAISS Database
print("⏳ Generating vectors and saving to FAISS database... (This takes a few seconds)")

# Create the vector database from our documents
vector_db = FAISS.from_documents(
    documents=projects,
    embedding=embeddings
)

# Save the database to a folder named 'faiss_index'
vector_db.save_local("faiss_index")

print("🎉 Success! Database created in 'faiss_index' folder.")
print("You can now run the search script.")