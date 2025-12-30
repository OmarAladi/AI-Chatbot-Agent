<div align="center">

# 🤖 AI Chatbot Agent

### Intelligent Multi-Route Conversational Agent

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge&logo=chainlink&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

*A production-ready chatbot with intelligent routing, RAG-powered knowledge base, booking system, and human handoff capabilities.*

[🚀 Quick Start](#-quick-start) • [✨ Features](#-features) • [🏗️ Architecture](#️-architecture) • [📖 Documentation](#-documentation)

---

</div>

## ✨ Features

<table>
<tr>
<td width="50%">

### 🎯 Smart Routing
Automatically routes conversations to the right handler:
- **General Chat** - Direct AI responses
- **Knowledge Base (RAG)** - Grounded answers from your docs
- **Booking System** - Appointment management
- **Human Handoff** - Escalation when needed

</td>
<td width="50%">

### 🔍 RAG-Powered Knowledge Base
- ChromaDB vector storage
- Google Gemini embeddings
- JSON-based knowledge management
- Grounded, accurate responses

</td>
</tr>
<tr>
<td width="50%">

### 📅 Booking System
- SQLite-backed appointments
- Check availability
- Book & manage appointments
- Tool-using agent architecture

</td>
<td width="50%">

### 🛡️ Production Ready
- Comprehensive logging (SRE-ready)
- Pydantic request validation
- Error classification & handling
- Clean, debuggable execution flow

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────────┐
│   Streamlit  │────▶│   FastAPI    │────▶│          LangGraph Agent         │
│   Chat UI    │     │   Backend    │     │                                  │
└──────────────┘     └──────────────┘     │  ┌─────────┐    ┌────────────┐  │
                                          │  │ Router  │───▶│  General   │  │
                                          │  │  Node   │    │   Chat     │  │
                                          │  │         │───▶│  RAG/KB    │  │
                                          │  │         │───▶│  Booking   │  │
                                          │  │         │───▶│  Handoff   │  │
                                          │  └─────────┘    └────────────┘  │
                                          └──────────────────────────────────┘
```

<details>
<summary>📊 View Detailed Architecture Diagram</summary>

![Architecture](images/COB_Agent.png)

</details>

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Description |
|------------|-------------|
| **Python** | Version 3.13 or higher |
| **uv** | Python package manager ([install guide](https://github.com/astral-sh/uv)) |
| **API Key** | Google Gemini API key |

### Step 1: Clone & Navigate

```bash
git clone https://github.com/OmarAladi/AI-Chatbot-Agent.git
cd AI-Chatbot-Agent
```

### Step 2: Create Virtual Environment

```bash
uv venv
```

**Activate the environment:**

<details>
<summary>🪟 Windows (PowerShell)</summary>

```powershell
.\.venv\Scripts\Activate.ps1
```
</details>

<details>
<summary>🪟 Windows (CMD)</summary>

```cmd
.\.venv\Scripts\activate.bat
```
</details>

<details>
<summary>🐧 macOS / Linux</summary>

```bash
source .venv/bin/activate
```
</details>

### Step 3: Install Dependencies

```bash
uv sync
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Required - Your Google API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional - Separate keys for different models
ROUTER_API_KEY=your_router_model_key_here
RAG_API_KEY=your_rag_model_key_here
BOOKING_API_KEY=your_booking_model_key_here
HANDOFF_API_KEY=your_handoff_model_key_here
```

<details>
<summary>⚙️ Advanced Configuration (Optional)</summary>

```env
# Paths
COB_LOGS_DIR=./logs
COB_DATA_DIR=./data
COB_DB_PATH=./data/appointments.db
COB_KB_JSON_PATH=./data/cob_kb.json
COB_PERSIST_DIR=./data/chroma_langchain_db

# Safety Limits
COB_MAX_RETRIES=1
COB_MAX_TOOL_STEPS=4
```
</details>

> ⚠️ **Security:** Never commit your `.env` file to version control!

### Step 5: Run the Application

You need **two terminals** - one for the backend and one for the frontend.

**Terminal 1 - Start Backend (FastAPI):**
```bash
uvicorn main_api:app --reload
```

**Terminal 2 - Start Frontend (Streamlit):**
```bash
streamlit run streamlit_chat.py
```

### 🎉 You're Ready!

| Service | URL |
|---------|-----|
| **Chat UI** | http://localhost:8501 |
| **API Health** | http://127.0.0.1:8000/health |
| **API Docs** | http://127.0.0.1:8000/docs |

---

## 📖 Documentation

### API Usage

**Chat Endpoint:**
```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to book a haircut on 2025-12-30 at 10:00", "thread_id": "123456"}'
```

### Data Configuration

<details>
<summary>📚 Knowledge Base (RAG) Setup</summary>

Place your knowledge base at `./data/cob_kb.json`:

```json
[
  {
    "id": "chunk_001",
    "title": "Pricing",
    "category": "FAQ",
    "source_file": "faq.md",
    "paragraph_index": 1,
    "lang": "en",
    "text": "Your KB chunk text here..."
  }
]
```
</details>

<details>
<summary>📅 Booking Database Setup</summary>

SQLite database at `./data/appointments.db` with an `appointments` table:

| Column | Type | Description |
|--------|------|-------------|
| `service` | TEXT | Service name |
| `date` | TEXT | Date (YYYY-MM-DD) |
| `time` | TEXT | Time (HH:MM) |
| `status` | TEXT | free / booked |
| `customer_name` | TEXT | Customer name |
| `phone` | TEXT | Phone number |
| `created_at` | TEXT | Timestamp |

</details>

### Logging

All logs are written to `./logs/app.log`:
- Node entry/exit events
- Tool call traces
- Error classifications (quota limits, timeouts, etc.)

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Missing API Key** | Ensure `.env` exists with `GOOGLE_API_KEY` |
| **Empty RAG Results** | Check `COB_KB_JSON_PATH` points to valid JSON |
| **Booking DB Not Found** | Verify `COB_DB_PATH` and `appointments` table exist |

---

## 🗺️ Roadmap

- [ ] Seed scripts for DB and KB initialization
- [ ] Request ID correlation in logs
- [ ] Prometheus metrics (latency, error rate)
- [ ] Redis/Postgres persistence (replace InMemorySaver)
- [ ] API authentication & rate limiting
- [ ] Admin dashboard for handoff tickets
- [ ] Multi-service booking policies
- [ ] RAG citations in UI

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ using LangGraph, FastAPI, and Streamlit**

</div>
