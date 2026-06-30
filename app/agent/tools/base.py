class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._declarations = {}

    def register(self, declaration, func):
        name = declaration["name"]
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = func
        self._declarations[name] = declaration

    def names(self):
        return list(self._tools.keys())

    def declarations(self):
        return list(self._declarations.values())

    async def execute(self, name, args, conversation_id=None):
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        return await self._tools[name](conversation_id=conversation_id, **args)
