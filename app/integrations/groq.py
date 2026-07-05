"""Thin async wrapper around Groq via OpenAI-compatible API.

Groq provides ultra-fast inference on open-weight models (Llama, Mixtral, etc.)
via their OpenAI-compatible API.
"""

import logging
import time

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqClient:
    """Groq chat client via OpenAI SDK."""

    def __init__(self):
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY not set")

        self._client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    async def generate(
        self,
        prompt: str,
        *,
        model: str = GROQ_MODEL,
    ) -> str:
        """
        Backward-compatible method used by the existing AgentOrchestrator.
        """
        return await self.generate_reply(
            prompt=prompt,
            model=model,
        )

    async def generate_reply(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        model: str = GROQ_MODEL,
    ) -> str:
        """Simple text generation."""

        messages = []

        if system_instruction:
            messages.append(
                {
                    "role": "system",
                    "content": system_instruction,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
        )

        return response.choices[0].message.content or ""

    async def generate_with_tools(
        self,
        *,
        system_instruction: str,
        history: list,
        tool_declarations: list[dict],
        model: str = GROQ_MODEL,
    ):
        """Tool-calling variant."""

        tools = [
            {
                "type": "function",
                "function": tool,
            }
            for tool in tool_declarations
        ]

        messages = [
            {
                "role": "system",
                "content": system_instruction,
            }
        ]

        messages.extend(history)

        start = time.perf_counter()

        response = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )

        response.latency_ms = int((time.perf_counter() - start) * 1000)

        return response

    async def stream_reply(
        self,
        *,
        system_instruction: str,
        history: list,
        model: str ="llama-3.3-70b-versatile",
    ):
        """
        Stream text responses from Groq.
        Text-only streaming for the SSE endpoint.
        """

        messages = [
            {
                "role": "system",
                "content": system_instruction,
            }
        ]

        messages.extend(history)

        stream = await self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


@staticmethod
def get_groq_model():
    return GroqClient()


async def ask_groq(prompt: str) -> str:
    return await GroqClient().generate(prompt)