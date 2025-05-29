# 🤖 Nestlé AI Chatbot

An AI-powered chatbot built for the [Made with Nestlé](https://www.madewithnestle.ca/) website.  
This project uses:

- 🧠 FastAPI (Python backend)
- ⚛️ React + TypeScript (frontend UI with Vite)
- 💬 Floating chat UI over a screenshot background
- 🧪 Returns user related response, based on the query

---

## 📁 Project Structure

```
nestle-chatbot/
├── frontend/                # React + TypeScript (Vite)
│   ├── public/NestleBG.jpg
│   ├── src/components/Chatbot.tsx
│   ├── src/components/Chatbot.css
│   ├── src/App.tsx
│   ├── .env
│   └── ...
├── backend/                 # FastAPI server
│   ├── main.py                  # FastAPI main entrypoint
|   ├── openai_service.py        # Azure OpenAI chat + embeddings
|   ├── scraper.py               # Playwright or requests-based website scraper
|   ├── indexer_service.py       # Indexes scraped documents into Azure AI Search
|   ├── search_service.py        # Queries Azure AI Search
|   ├── graphRAG.py              # Optional graph-based RAG pipeline
|   ├── .env                     # Environment variables
|   ├── Scraped/
|   │   └── chat_history.json    # Message history persistence
|   └── requirements.txt
```

---

## 🚀 How to Run the Project Locally

---

### 🔹 1. Start the Backend (FastAPI)

#### 📍 Navigate to the backend directory:

```bash
cd backend
```

#### 🐍 (Optional) Create and activate virtual environment:

```bash
python -m venv venv
venv\Scripts\activate        # On Windows
# OR
source venv/bin/activate     # On macOS/Linux
```

#### 📦 Install dependencies:

```bash
pip install -r requirements.txt
```

Or manually install if no `requirements.txt`:

```bash
pip install fastapi uvicorn python-dotenv
```

#### ▶️ Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The backend will run at:

```
http://localhost:8000
```

---

### 🔹 2. Start the Frontend (React + Vite)

#### 📍 Navigate to the frontend directory:

```bash
cd nestle-chatbot-frontend
```

#### 📦 Install Node dependencies:

```bash
npm install
```

#### 🧪 Create a `.env` file with your backend API URL:

```bash
touch .env
```

Paste this inside:

```
VITE_API_URL=http://localhost:8000
```

#### ▶️ Start the React development server:

```bash
npm run dev
```

The frontend will run at:

```
http://localhost:5173
```

## 🤝 Assistant Behaviour

The assistant operates with the following guidelines:

- Maintains a friendly yet professional tone.
- Provides concise answers (1–2 paragraphs).
- Avoids making health claims.
- Always refers to Canadian product names.
- Advises users to check product packaging if uncertain.
- Recommends contacting Nestlé Canada support for unresolved questions.
- Persists the past 3 user interactions locally in `Scraped/chat_history.json`.

---

## 🛠️ Features

- Floating chatbot in bottom-right corner
- Screenshot background of the Nestlé website
- Pop-out chat interface with real-time backend requests
- Styled user and bot messages
- Easy to extend with RAG/FAISS/Neo4j in backend

---

## ⚠️ Important Notes

- You must have access to Azure OpenAI and Azure Cognitive Search services to enable advanced features.
- The backend uses a permissive CORS policy (`*`) for development; update this to restrict origins before deploying to production.
- The scraper saves data locally by default and can optionally upload to Azure Blob Storage.
