# app/agent/tools/base.py

class ToolRegistry:
    _tools = {}

    @classmethod
    def register(cls, declaration: dict, handler):
        name = declaration["name"]
        cls._tools[name] = {
            "declaration": declaration,
            "handler": handler,
        }

    @classmethod
    def get_handler(cls, name: str):
        tool = cls._tools.get(name)
        if not tool:
            raise ValueError(f"No tool registered with name '{name}'")
        return tool["handler"]

    @classmethod
    def get_all_declarations(cls):
        return [t["declaration"] for t in cls._tools.values()]
