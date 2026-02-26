# GEMINI.md - AI Agent Development Guide

## 📋 Project Overview

**ACM-AI** is an intelligent, privacy-first platform for Asbestos Containing Material (ACM) compliance management. It automates data extraction from complex PDF documents like School Asbestos Management Plans (SAMPs), transforms unstructured content into a structured database, and enables powerful AI-driven search and analysis.

The system is designed to be run entirely on local infrastructure, ensuring sensitive compliance data remains private.

### Key Capabilities
- ✅ Automated data extraction from PDFs into a hierarchical structure (School → Building → Room → ACM Item).
- ✅ Natural language chat interface for querying ACM data.
- ✅ Support for a wide array of LLM and embedding providers (>16), including OpenAI, Google, Anthropic, and Groq.
- ✅ **Privacy-First Local AI**: First-class support for running 100% offline with Ollama (CPU and GPU).
- ✅ Structured and auditable data with every record linked back to its source PDF and page number.
- ✅ Background job processing for robust, asynchronous document analysis.
- ✅ Comprehensive REST API for programmatic access.

---

## 🛠️ Tech Stack

### Frontend Stack
- **Framework**: Next.js 15 (with Turbopack) / React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: shadcn/ui (built on Radix UI)
- **State Management**: Zustand
- **Testing**: Playwright for End-to-End testing

### Backend & Infrastructure
- **Framework**: Python 3.11+ with FastAPI & Pydantic
- **AI Orchestration**: LangChain & LangGraph
- **Database**: SurrealDB (v2)
- **Workflow Engine**: Docker for service orchestration
- **AI/LLM**: Multi-provider support including OpenAI, Google, Anthropic, Groq, and local Ollama.

### Development Tools
- **Package Managers**: `npm` for frontend, `uv` for Python
- **Linting**: ESLint for frontend, `ruff` for backend
- **Code Quality**: TypeScript and `mypy`
- **Automation**: `make`, Windows Batch (`.bat`), and Shell scripts for simplified environment management.

---

## 📁 Project Structure

```
acm-ai/
├── api/                  # Python FastAPI Backend
├── frontend/             # Next.js Frontend Application
│   ├── app/              # Main application pages and layouts
│   ├── components/       # React components
│   └── lib/              # Utility functions and API clients
├── scripts/              # Automation and utility scripts
├── tests/                # E2E tests (Playwright)
├── docker-compose.yml    # Main Docker Compose file for services
├── Makefile              # 'make' commands for easy script access
├── start-all.bat         # 1-click start script for Windows
├── start-all.sh          # 1-click start script for Linux/macOS
└── README.md             # Main project documentation
```

---

## 🏗️ Building and Running

ACM-AI provides a streamlined setup process using helper scripts for all major operating systems.

### Prerequisites
- Docker Desktop (must be running)
- Python 3.11+ (install `uv` with `pip install uv`)
- Node.js 18+

### 1-Click Development Start

**Windows:**
Open a terminal and run:
```batch
# Start all services (DB, Backend, Frontend)
start-all.bat
```

**macOS / Linux / WSL:**
Open a terminal and run:
```bash
# Use the smart-start make command (recommended)
make smart-start
```
or
```bash
# Use the shell script directly
./start-all.sh
```

**Access the application at: [http://localhost:8503](http://localhost:8503)**

### Manual Service Start
If you prefer to run each service manually:

1.  **Start Database**:
    ```bash
    docker compose up -d surrealdb
    ```
2.  **Start Backend API**:
    ```bash
    uv run run_api.py # Starts on http://localhost:5055
    ```
3.  **Start Frontend**:
    ```bash
    cd frontend
    npm run dev # Starts on http://localhost:8503
    ```

### Running with Local AI (Ollama)

For 100% private, offline AI processing:

1.  **Start Ollama Service**:
    *   **CPU Only**: `docker compose --profile ollama-cpu up -d`
    *   **With NVIDIA GPU**: `docker compose --profile ollama-gpu up -d`

2.  **Pull Models**:
    ```bash
    docker exec acm-ai-ollama ollama pull qwen3
    docker exec acm-ai-ollama ollama pull mxbai-embed-large
    ```

3.  **Configure Environment**:
    *   Add `OLLAMA_API_BASE=http://ollama:11434` to your `.env` file.

---

## 🧪 Testing

The project uses **Playwright** for End-to-End tests.

-   **Run all tests (headless)**:
    ```bash
    npm run test:e2e
    ```
-   **Run tests with UI**:
    ```bash
    npm run test:e2e:ui
    ```
-   **View test report**:
    ```bash
    npm run test:show-report
    ```
