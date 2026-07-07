"""Thin async wrapper around Grok via OpenAI-compatible API."""

import time
from openai import AsyncOpenAI
from app.config import settings


class GroqClient:
    def __init__(self):
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY not set")

        self._client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.x.ai/v1",
        )

    async def generate_with_tools(self, system_instruction: str, history: list, tool_declarations: list):
        tools = [{"type": "function", "function": t} for t in tool_declarations]

        messages = [{"role": "system", "content": system_instruction}]
        messages.extend(history)

        start = time.perf_counter()
        response = await self._client.chat.completions.create(
            model="groq-4-fast",
            messages=messages,
            tools=tools,
        )
        response.latency_ms = int((time.perf_counter() - start) * 1000)
        return response
