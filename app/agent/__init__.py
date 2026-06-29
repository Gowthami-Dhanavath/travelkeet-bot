# app/agent/__init__.py
"""Agent orchestrator package.

OWNERSHIP NOTE: in the original two-engineer plan, this package is owned
by Person A. In this solo build, Person B (you) maintains it. When/if
Person A shares their real implementation, replace orchestrator.py and
schemas.py with theirs; the rest of the stack interfaces to this folder
only via AgentOrchestrator.handle_message().
"""