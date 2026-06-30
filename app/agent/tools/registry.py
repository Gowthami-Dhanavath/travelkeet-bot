from functools import lru_cache

from app.agent.tools.base import ToolRegistry
from app.agent.tools.campervan import (
    SEARCH_CAMPERVANS_DECLARATION,
    search_campervans,
)


@lru_cache(maxsize=1)
def build_registry():

    registry = ToolRegistry()

    registry.register(
        SEARCH_CAMPERVANS_DECLARATION,
        search_campervans,
    )

    return registry