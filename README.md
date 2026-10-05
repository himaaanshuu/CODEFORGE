# CodeForge AI
# Autonomous AI software engineering agent for Nebius × NVIDIA Global AI Hackathon 2026

# Project Status
The project is currently in the initial infrastructure/setup phase. Core backend
foundation and Nebius/NVIDIA model integration preparation have been implemented.
Full AI coding agent capabilities will be added in subsequent stages.

# Vision
CodeForge AI will be an autonomous AI software engineering agent capable of
understanding repositories, diagnosing coding problems, implementing fixes, running
tests, and explaining its changes.

# Planned Architecture
The backend will follow a modular design with separate components for:
- Agent orchestration
- LLM integration (NVIDIA open-source models via Nebius)
- Repository analysis and tooling
- Test generation and execution
- Safe code execution sandbox

# Technology Stack
- Backend: FastAPI (Python)
- HTTP Client: httpx
- Environment: python-dotenv
- Runtime: Uvicorn

# Development Setup
1. Create a Python virtual environment: python3 -m venv .venv
2. Activate the environment: source .venv/bin/activate
3. Install dependencies: pip install -r backend/requirements.txt
4. Copy .env.example to .env and configure your Nebius credentials
5. Run the backend: uvicorn backend.app.main:app --reload

# Environment Variables
- NEBIUS_API_KEY: Your Nebius API key (required for LLM integration)
- NEBIUS_BASE_URL: Nebius API base URL (default: https://api.nebius.ai/v1)
- NEBIUS_MODEL: Default model name (default: nemotron)
- DEBUG: Enable debug mode (default: False)

# Running the Backend
uvicorn backend.app.main:app --reload

# Hackathon
Nebius × NVIDIA Global AI Hackathon 2026

# License
MIT