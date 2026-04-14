# 🎓 ProCheck - AI-Powered Academic Project Originality Checker

ProCheck is an intelligent academic project approval system designed to streamline the evaluation of student project proposals. Built with **Django** and powered by **Google Gemini** and **FAISS**, the platform automates duplication detection using Retrieval-Augmented Generation (RAG) and Semantic Similarity Search to ensure absolute project originality.

Unlike traditional plagiarism checkers that rely on exact keyword matching, ProCheck understands the *meaning* of the abstract. If a student tries to submit a highly paraphrased version of a previously approved project, the "AI Brain" catches it and dynamically suggests unique alternatives.

## ✨ Key Features

* **Semantic Duplicate Detection:** Utilizes `GoogleGenerativeAIEmbeddings` to map student abstracts into high-dimensional vectors, comparing them against a local FAISS vector database to detect conceptually identical ideas.
* **Smart RAG Suggestions:** If a duplicate is found, the system uses the Gemini Flash LLM to asynchronously stream 3 customized, non-conflicting project alternatives back to the student using a ChatGPT-style typing effect.
* **Interactive Student Portal:** A chat-based UI where students can securely submit their project Titles and Abstracts for instant AI evaluation.
* **Mentor Governance Dashboard:** A secure dashboard where mentors can review pending projects. Approving a project automatically ingests its vector data into the FAISS "AI Brain" to protect the idea from future duplication.
* **Concurrency Protection:** Includes backend double-check mechanisms to prevent race conditions when multiple mentors process projects simultaneously.

## 🛠️ Tech Stack

* **Backend:** Python, Django (MVT Architecture)
* **AI & Machine Learning:** Google Gemini API (Flash LLM & Embeddings), LangChain
* **Databases:** * **Relational:** SQLite (Stores Users, Project Status, Mentor Feedback)
  * **Vector:** FAISS (Stores mathematical representations of approved abstracts)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API for asynchronous AI streaming)

## 🚀 Installation & Setup

Follow these steps to run ProCheck locally on your machine.

### 1. Clone the repository
```bash
git clone [https://github.com/antoninjoy/procheck.git](https://github.com/antoninjoy/procheck.git)
cd procheck
2. Set up a Virtual Environment
Bash
python -m venv venv
Activate the environment (Choose one based on your OS):

Windows:

Bash
venv\Scripts\activate
Mac/Linux:

Bash
source venv/bin/activate
3. Install Dependencies
Bash
pip install django langchain langchain-google-genai faiss-cpu python-dotenv
4. Configure Environment Variables
Create a file named .env in the root folder and paste this inside:

Code snippet
GOOGLE_API_KEY=your_gemini_api_key_here
5. Run Database Migrations
Bash
python manage.py makemigrations
python manage.py migrate
6. Create a Superuser (Admin/Mentor)
Bash
python manage.py createsuperuser
7. Run the Development Server
Bash
python manage.py runserver
