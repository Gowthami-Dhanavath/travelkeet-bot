from functools import lru_cache

from app.agent.tools.base import ToolRegistry

from app.agent.tools.campervan import (
    SEARCH_CAMPERVANS_DECLARATION,
    search_campervans,
)

from app.agent.tools.packages import (
    GET_PACKAGE_DETAILS_DECLARATION,
    get_package_details,
)


@lru_cache(maxsize=1)
def build_registry() -> ToolRegistry:
    registry = ToolRegistry()

    # -----------------------------
    # Campervan tools
    # -----------------------------
    registry.register(
        SEARCH_CAMPERVANS_DECLARATION,
        search_campervans,
    )

    # -----------------------------
    # Package tools
    # -----------------------------
    registry.register(
        GET_PACKAGE_DETAILS_DECLARATION,
        get_package_details,
    )

    return registry