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


# Agent request/response models
class AgentRequest(BaseModel):
    workspace_id: str = "local-project"
    task: str
    max_iterations: int | None = None


class AgentAnalysisResponse(BaseModel):
    success: bool
    status: str
    summary: str
    files_inspected: list
    tools_used: list
    plan: list
    observations: list
    error: str | None
    iteration: int


@app.post("/api/v1/agent/analyze")
async def agent_analyze(request: AgentRequest) -> dict:
    """Run the CodeForge AI read-only coding agent on a task.

    The agent can inspect a repository workspace using read-only tools:
    - list_files: List files and directories
    - read_file: Read file contents with line numbers
    - search_code: Search for text in source files

    The agent does NOT modify files, execute commands, or access
    anything outside the repository workspace.

    Returns a structured analysis including the plan and findings.
    """
    from .agent.agent import run_agent_task
    from .agent.state import AgentState

    # Map workspace_id to actual workspace root
    # For development, we use a controlled workspace mechanism
    workspace_mapping = {
        "local-project": "/Users/himanshu/EDITOR/codeforge-ai",
        "demo-repo": "/Users/himanshu/EDITOR/codeforge-ai",
    }

    workspace_root = workspace_mapping.get(request.workspace_id, request.workspace_id)

    # Validate that the workspace root exists
    import os
    if not os.path.isdir(workspace_root):
        return {
            "success": False,
            "status": "error",
            "summary": f"Workspace root not found: {workspace_root}",
            "files_inspected": [],
            "tools_used": [],
            "plan": [],
            "observations": [],
            "error": f"Workspace root not found: {workspace_root}",
            "iteration": 0,
        }

    # Run the agent
    response = await run_agent_task(
        workspace_root=workspace_root,
        task=request.task,
        max_iterations=request.max_iterations or 10,
    )

    # Convert to API response format
    return {
        "success": response.success,
        "status": response.status,
        "summary": response.summary,
        "files_inspected": response.files_inspected,
        "tools_used": response.tools_used,
        "plan": response.plan,
        "observations": [
            {
                "tool_name": obs.tool_name,
                "tool_success": obs.tool_success,
                "observation": obs.observation,
            }
            for obs in response.observations
        ],
        "error": response.error,
        "iteration": response.iteration,
    }