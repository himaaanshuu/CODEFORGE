from fastapi import FastAPI

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