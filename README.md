# 🤖 Nestlé AI Chatbot

An AI-powered chatbot built for the [Made with Nestlé](https://www.madewithnestle.ca/) website.  
This project uses:

- 🧠 FastAPI (Python backend)
- ⚛️ React + TypeScript (frontend UI with Vite)
- 💬 Floating chat UI over a screenshot background
- 🧪 Returns dummy responses (can later connect to RAG, FAISS, or Neo4j)

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
│   ├── main.py
│   ├── requirements.txt
│   ├── .env
│   └── ...
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

✅ You can now type in the chatbot and receive a dummy response from the backend.

---

## 🛠️ Features

- Floating chatbot in bottom-right corner
- Screenshot background of the Nestlé website
- Pop-out chat interface with real-time backend requests
- Styled user and bot messages
- Easy to extend with RAG/FAISS/Neo4j in backend

---

## 🚧 To-Do (Next Steps)

- [ ] Add AI capabilities using OpenAI or GraphRAG
- [ ] Integrate web scraping + FAISS or Azure Cognitive Search
- [ ] Add avatar icons for user/bot
- [ ] Show typing animation
- [ ] Deploy frontend to Vercel / Netlify
- [ ] Deploy backend to Azure / Render / Railway
