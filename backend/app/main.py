from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="CodeForge AI",
    description="Autonomous AI software engineering agent",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "CodeForge AI is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "message": "CodeForge AI is running"}


class GenerateRequest(BaseModel):
    prompt: str
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    top_p: float = 1.0


@app.post("/api/v1/llm/generate")
async def llm_generate(request: GenerateRequest) -> dict:
    """Generate a response from the NVIDIA model via Nebius Token Factory.

    This is a development/testing endpoint for LLM integration verification.
    It does not expose any API keys or provider-specific secrets.
    """
    from .llm.client import get_client, is_configured

    if not is_configured():
        return {
            "success": False,
            "model": request.model or "nebius/Nemotron-3_5-Lightning",
            "response": "",
            "error": "NEBIUS_API_KEY not configured. Set it in .env file.",
        }

    client = get_client()

    response = await client.generate(
        prompt=request.prompt,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=request.stream,
        top_p=request.top_p,
    )

    return response.model_dump()