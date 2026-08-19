# WEB DNA - Hackathon MVP

> See how companies evolve on the web.

Web DNA is an agentic company-intelligence platform that continuously observes a company's public web presence using Bright Data, converts objective observations into a structured digital genome, detects meaningful mutations, and uses a bounded LangGraph research agent to investigate those mutations.

## 🚀 Quick Start Demo

### 1. Start the Backend
The backend runs on FastAPI and uses a local SQLite database for this MVP demo. It's already seeded with NVIDIA.
```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

### 2. Start the Frontend
The frontend runs on Next.js.
```bash
cd frontend
npm run dev
```

### 3. Run the Intelligence Loop
1. Open `http://localhost:3000` in your browser.
2. You will see NVIDIA's dashboard with a baseline genome loaded from "yesterday".
3. Click the **Force Sequence** button. 
4. **Watch the magic happen:**
   - The backend triggers Bright Data collectors (mocked via CLI).
   - The data is normalized into Evidence.
   - A new Genome is built.
   - The Mutation engine detects a massive spike in **Robotics** (a critical mutation).
   - This automatically wakes up the **LangGraph Agent** in the background.
5. In the UI, you will see the Genome chart update, the mutation appear in the Recent Mutations feed, and the Agent Activity feed will show the investigation in progress until it completes and renders a grounded analysis report.
6. Under Data Sources Health, click **Simulate Failure** on a collector to watch it break, and then click **Approve Healing** to execute the Bright Data self-healing workflow.

## Tech Stack
- **Data Collection**: Bright Data CLI
- **Backend**: Python, FastAPI, SQLAlchemy (Async), Alembic, SQLite (MVP)
- **Agent Intelligence**: LangGraph, LangChain, Gemma-2-9b (via OpenRouter)
- **Frontend**: Next.js, Tailwind CSS, Recharts, Lucide React
