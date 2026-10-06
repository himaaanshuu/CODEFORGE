from __future__ import annotations

import json
import time
from typing import Optional

import httpx

from .models import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    HealthCheckResponse,
    is_configured,
    get_model_name,
    get_base_url,
    get_api_key,
)


# Nebius Token Factory API configuration
NEBIUS_API_BASE: str = "https://api.tokenfactory.nebius.com/v1"
NEBIUS_CHAT_COMPLETIONS: str = "/chat/completions"
NEBIUS_TIMEOUT: float = 60.0
NEBIUS_MAX_RETRIES: int = 3
NEBIUS_BACKOFF_FACTOR: float = 1.5


class NebiusClient:
    """Lightweight client for Nebius Token Factory API.

    Uses the OpenAI-compatible interface for chat completions.
    Does not depend on FastAPI - can be used anywhere.
    """

    def __init__(
        self,
        base_url: str = NEBIUS_API_BASE,
        api_key: Optional[str] = None,
        timeout: float = NEBIUS_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Use provided API key or fall back to module-level config
        if api_key:
            self.api_key = api_key
        elif is_configured():
            self.api_key = get_api_key()
        else:
            self.api_key = ""

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self._default_headers(),
        )

    def _default_headers(self) -> dict[str, str]:
        """Return default request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        json: Optional[dict] = None,
        params: Optional[dict] = None,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic for transient failures."""
        url = f"{self.base_url}{path}"
        last_exception: Optional[Exception] = None

        for attempt in range(NEBIUS_MAX_RETRIES):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    headers=self._default_headers(),
                )
                # Retry on network errors or 5xx server errors
                if response.is_error:
                    if response.status_code >= 500:
                        last_exception = Exception(
                            f"Nebius API error {response.status_code}: {response.text}"
                        )
                        time.sleep(NEBIUS_BACKOFF_FACTOR ** attempt)
                        continue
                    # Don't retry 4xx errors (except 429 rate limit)
                    if response.status_code != 429:
                        raise Exception(
                            f"Nebius API error {response.status_code}: {response.text}"
                        )
                    # Rate limit: retry with backoff
                    last_exception = Exception(
                        f"Rate limited (429). Retry attempt {attempt + 1}."
                    )
                    time.sleep(NEBIUS_BACKOFF_FACTOR ** attempt)
                    continue
                return response

            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as e:
                last_exception = e
                if attempt < NEBIUS_MAX_RETRIES - 1:
                    time.sleep(NEBIUS_BACKOFF_FACTOR ** attempt)
                continue

        if last_exception:
            raise last_exception
        raise Exception("Request failed after all retries")

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        stop: Optional[str] = None,
        top_p: float = 1.0,
    ) -> LLMGenerateResponse:
        """Generate a response from the NVIDIA model via Nebius Token Factory.

        Args:
            prompt: The prompt to send to the model.
            model: Override model name. Uses NEBIUS_MODEL env var if not provided.
            temperature: Sampling temperature (0-2).
            max_tokens: Maximum tokens to generate.
            stream: Whether to stream the response.
            stop: Stop generation on this token.
            top_p: Top-p nucleus sampling.

        Returns:
            LLMGenerateResponse with success flag and the model output.
        """
        model_name = model or get_model_name()

        if not is_configured():
            return LLMGenerateResponse(
                success=False,
                model=model_name,
                response="",
                error="NEBIUS_API_KEY not configured. Set it in .env file.",
            )

        request_data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
            "top_p": top_p,
        }
        if stop is not None:
            request_data["stop"] = stop

        try:
            response = await self._request_with_retry(
                method="POST",
                path=NEBIUS_CHAT_COMPLETIONS,
                json=request_data,
            )

            if response.status_code == 401:
                return LLMGenerateResponse(
                    success=False,
                    model=model_name,
                    response="",
                    error="Authentication failed: invalid or missing NEBIUS_API_KEY.",
                )

            if response.status_code == 429:
                return LLMGenerateResponse(
                    success=False,
                    model=model_name,
                    response="",
                    error="Rate limit exceeded. Please wait before making another request.",
                )

            if response.status_code != 200:
                return LLMGenerateResponse(
                    success=False,
                    model=model_name,
                    response="",
                    error=f"Nebius API returned status {response.status_code}: {response.text[:200]}",
                )

            # Parse the OpenAI-compatible response
            try:
                data = response.json()
                # Extract the response text from the OpenAI-compatible format
                choices = data.get("choices", [])
                if choices and len(choices) > 0:
                    message = choices[0].get("message", {})
                    response_text = message.get("content", "")
                    usage = data.get("usage", {})
                else:
                    response_text = ""
                    usage = {}

                return LLMGenerateResponse(
                    success=True,
                    model=model_name,
                    response=response_text,
                    usage=usage,
                )

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                return LLMGenerateResponse(
                    success=False,
                    model=model_name,
                    response="",
                    error=f"Failed to parse Nebius API response: {str(e)[:200]}",
                )

        except httpx.TimeoutException:
            return LLMGenerateResponse(
                success=False,
                model=model_name,
                response="",
                error="Request to Nebius timed out. Please try again.",
            )
        except httpx.ConnectError:
            return LLMGenerateResponse(
                success=False,
                model=model_name,
                response="",
                error="Connection failed. Check your network and NEBIUS_BASE_URL configuration.",
            )
        except Exception as e:
            # Generic error - don't expose API key
            return LLMGenerateResponse(
                success=False,
                model=model_name,
                response="",
                error=f"Unexpected error during LLM generation: {str(e)[:200]}",
            )

    async def health_check(self) -> HealthCheckResponse:
        """Check the LLM service health by testing connectivity.

        Does NOT make open-ended model requests - just tests the API endpoint.
        Returns "healthy" even if the model is temporarily unavailable,
        as long as the API endpoint is reachable.
        """
        if not is_configured():
            return HealthCheckResponse(
                status="unavailable",
                model=get_model_name(),
                message="NEBIUS_API_KEY not configured.",
            )

        try:
            # Just test connectivity - list models or do a minimal request
            response = await self._request_with_retry(
                method="GET",
                path="/models",
            )

            if response.status_code == 200:
                data = response.json()
                model_names = [
                    m.get("id", "") for m in data.get("data", []) if m
                ]
                current_model = get_model_name()
                # Check if the configured model is available
                model_available = any(
                    current_model in name for name in model_names
                )
                return HealthCheckResponse(
                    status="healthy" if model_available else "unavailable",
                    model=current_model,
                    message=(
                        f"API connection OK. Configured model '{current_model}' "
                        f"{'is available.' if model_available else 'not found in available models.'}"
                    ),
                )
            else:
                return HealthCheckResponse(
                    status="unavailable",
                    model=get_model_name(),
                    message=f"API responded with status {response.status_code}.",
                )

        except httpx.TimeoutException:
            return HealthCheckResponse(
                status="unavailable",
                model=get_model_name(),
                message="Connection timed out.",
            )
        except httpx.ConnectError:
            return HealthCheckResponse(
                status="unavailable",
                model=get_model_name(),
                message="Cannot connect to Nebius API. Check NEBIUS_BASE_URL.",
            )
        except Exception as e:
            return HealthCheckResponse(
                status="error",
                model=get_model_name(),
                message=f"Health check error: {str(e)[:200]}",
            )

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        await self._client.aclose()


# Create a default instance for convenience
_default_client: Optional[NebiusClient] = None


def get_client() -> NebiusClient:
    """Get or create a default NebiusClient instance."""
    global _default_client
    if _default_client is None:
        if is_configured():
            _default_client = NebiusClient()
        else:
            _default_client = NebiusClient(api_key="")
    return _default_client


async def shutdown() -> None:
    """Shut down the default client."""
    global _default_client
    if _default_client is not None:
        await _default_client.close()
        _default_client = None