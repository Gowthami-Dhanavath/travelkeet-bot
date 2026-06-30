from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

ToolHandler = Callable[..., Awaitable[Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[dict, ToolHandler]] = {}

    def register(self, declaration: dict, handler: ToolHandler) -> None:
        name = declaration["name"]

        if name in self._tools:
            raise ValueError(f"Tool {name!r} already registered")

        self._tools[name] = (declaration, handler)

    def declarations(self) -> list[dict]:
        return [d for d, _ in self._tools.values()]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    async def execute(
        self,
        name: str,
        args: dict,
        *,
        conversation_id: UUID,
    ) -> dict:

        if name not in self._tools:
            return {
                "error": f"Unknown tool {name}",
                "success": False,
            }

        _, handler = self._tools[name]

        try:
            result = await handler(
                conversation_id=conversation_id,
                **args,
            )

            if not isinstance(result, dict):
                return {
                    "error": "Tool must return dict",
                    "success": False,
                }

            return {
                **result,
                "success": True,
            }

        except Exception as e:
            return {
                "error": str(e),
                "success": False,
            }