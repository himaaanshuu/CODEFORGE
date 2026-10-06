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

# NVIDIA + Nebius Integration
CodeForge AI uses Nebius Token Factory to access NVIDIA open-source models.
The project is designed to use an NVIDIA open-source model (Nemotron family)
through the Nebius platform. The model is configured using the NEBIUS_MODEL
environment variable. The API key is stored locally in .env and is never committed
to the repository.

Planned Architecture:
- LLM integration (NVIDIA open-source models via Nebius Token Factory)
- Agent orchestration
- Repository analysis and tooling
- Test generation and execution
- Safe code execution sandbox

# Technology Stack
- Backend: FastAPI (Python)
- HTTP Client: httpx
- Environment: python-dotenv
- Runtime: Uvicorn
- API: Nebius Token Factory (OpenAI-compatible interface)

# Development Setup
1. Create a Python virtual environment: python3 -m venv .venv
2. Activate the environment: source .venv/bin/activate
3. Install dependencies: pip install -r backend/requirements.txt
4. Copy .env.example to .env and configure your Nebius credentials
5. Run the backend: uvicorn backend.app.main:app --reload

# Environment Variables
- NEBIUS_API_KEY: Your Nebius API key (required for LLM integration)
  Store this in backend/.env - never commit the actual key to the repo
- NEBIUS_BASE_URL: Nebius API base URL (default: https://api.tokenfactory.nebius.com/v1)
- NEBIUS_MODEL: Default model name (default: nebius/Nemotron-3_5-Lightning)
  Choose from NVIDIA Nemotron family available through Token Factory
- DEBUG: Enable debug mode (default: False)

# Running the Backend
uvicorn backend.app.main:app --reload

# Hackathon
Nebius × NVIDIA Global AI Hackathon 2026

# License
MIT