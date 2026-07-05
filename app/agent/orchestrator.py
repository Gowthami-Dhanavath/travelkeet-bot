import json
import logging
import time

from app.agent.slots import SlotExtractor
from app.agent.tools.registry import ToolRegistry
from app.db.models import ToolCall
from app.db.repositories import ConversationRepo, MessageRepo
from app.integrations.groq import GroqClient
from prompts.system_prompt import build_system_prompt

logger = logging.getLogger(__name__)


def _message_to_history(message):
    return {
        "role": message.role,
        "content": message.content or "",
    }


def _tool_call_to_openai(call):
    return {
        "id": call.id,
        "type": "function",
        "function": {
            "name": call.function.name,
            "arguments": call.function.arguments,
        },
    }


class AgentOrchestrator:
    def __init__(
        self,
        client: GroqClient,
        conv_repo: ConversationRepo,
        msg_repo: MessageRepo,
        tools: ToolRegistry,
    ):
        self.client = client
        self.conv_repo = conv_repo
        self.msg_repo = msg_repo
        self.tools = tools
        self.slot_extractor = SlotExtractor()

    async def handle_message(
        self,
        session_id: str,
        user_message: str,
        history: list[dict],
    ) -> dict:
        conversation = await self.conv_repo.get_or_create(session_id=session_id)

        await self.msg_repo.append(
            conversation_id=conversation.id,
            role="user",
            content=user_message,
        )

        stored_messages = await self.msg_repo.get_window(conversation.id)
        model_history = [
            _message_to_history(message)
            for message in stored_messages
            if message.role in {"user", "assistant"}
        ]

        slots = conversation.collected_slots or {}
        system_prompt = build_system_prompt(slots)
        tool_declarations = self.tools.declarations()

        response = await self.client.generate_with_tools(
            system_instruction=system_prompt,
            history=model_history,
            tool_declarations=tool_declarations,
        )

        assistant_message = response.choices[0].message
        raw_tool_calls = assistant_message.tool_calls or []
        executed_tool_calls = []

        if raw_tool_calls:
            model_history.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [_tool_call_to_openai(call) for call in raw_tool_calls],
                }
            )

        for call in raw_tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if not isinstance(args, dict):
                logger.warning(
                    "Tool arguments were not a JSON object",
                    extra={"tool_name": name},
    )
                args = {}
            # Fix numeric arguments that LLM returns as strings
            if name == "generate_booking_link":
                if "num_travellers" in args:
                    try:
                        args["num_travellers"] = int(args["num_travellers"])
                    except (TypeError, ValueError):
                        pass

            start = time.perf_counter()
            success = True
            error_message = None
            try:
                result = await self.tools.execute(name, args, str(conversation.id))
            except Exception as exc:
                logger.exception(
                    "Tool execution failed",
                    extra={"tool_name": name, "conversation_id": str(conversation.id)},
                )
                success = False
                error_message = str(exc)
                result = {"success": False, "error": error_message}

            latency_ms = int((time.perf_counter() - start) * 1000)
            executed_tool_calls.append(
                {
                    "id": call.id,
                    "name": name,
                    "arguments": args,
                    "result": result,
                    "success": success,
                    "error_message": error_message,
                    "latency_ms": latency_ms,
                }
            )
            model_history.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                }
            )

        if raw_tool_calls:
            response = await self.client.generate_with_tools(
                system_instruction=system_prompt,
                history=model_history,
                tool_declarations=tool_declarations,
            )
            assistant_message = response.choices[0].message

        final_text = assistant_message.content or ""
        final_state = model_history + [{"role": "assistant", "content": final_text}]
        final_state_text = "\n".join(
            f"{message['role']}: {message.get('content') or ''}"
            for message in final_state
        )
        final_slots = await self.slot_extractor.extract(final_state_text, slots)
        await self.conv_repo.update_slots(conversation.id, final_slots)

        assistant_db_message = await self.msg_repo.append(
            conversation_id=conversation.id,
            role="assistant",
            content=final_text,
            tool_calls=executed_tool_calls,
            model="llama-3.3-70b-versatile",
            latency_ms=getattr(response, "latency_ms", None),
        )

        for item in executed_tool_calls:
            db_tool_call = ToolCall(
                conversation_id=conversation.id,
                message_id=assistant_db_message.id,
                tool_name=item["name"],
                arguments=item["arguments"],
                result=item["result"],
                success=item["success"],
                error_message=item["error_message"],
                latency_ms=item["latency_ms"],
            )
            self.msg_repo.session.add(db_tool_call)
            await self.msg_repo.session.flush()
            logger.info(
                "DB tool call written",
                extra={
                    "conversation_id": str(conversation.id),
                    "message_id": str(assistant_db_message.id),
                    "tool_name": item["name"],
                },
            )

        return {
            "reply": final_text,
            "tool_calls": executed_tool_calls,
            "slots": final_slots or {},
            "conversation_id": str(conversation.id),
            "message_id": str(assistant_db_message.id),
        }
    async def stream_message(
        self,
        session_id: str,
        user_message: str,
    ):
        """
        Streaming version of handle_message().
        Used only by /v1/chat/stream.

        Text-only streaming.
        Tool calling continues to use handle_message().
        """

        # Load or create conversation
        conversation = await self.conv_repo.get_or_create(
            session_id=session_id
        )

        # Store user message
        await self.msg_repo.append(
            conversation_id=conversation.id,
            role="user",
            content=user_message,
        )

        # Load recent history
        stored_messages = await self.msg_repo.get_window(conversation.id)

        model_history = [
            _message_to_history(message)
            for message in stored_messages
            if message.role in {"user", "assistant"}
        ]

        # Existing slots
        slots = conversation.collected_slots or {}

        system_prompt = build_system_prompt(slots)

        # Stream response
        streamed_parts = []

        async for token in self.client.stream_reply(
            system_instruction=system_prompt,
            history=model_history,
        ):
            streamed_parts.append(token)
            yield token

        # Final assistant text
        final_text = "".join(streamed_parts)

        # Update slots
        final_state = model_history + [
            {
                "role": "assistant",
                "content": final_text,
            }
        ]

        final_state_text = "\n".join(
            f"{message['role']}: {message.get('content') or ''}"
            for message in final_state
        )

        final_slots = await self.slot_extractor.extract(
            final_state_text,
            slots,
        )

        await self.conv_repo.update_slots(
            conversation.id,
            final_slots,
        )

        # Save assistant response
        await self.msg_repo.append(
            conversation_id=conversation.id,
            role="assistant",
            content=final_text,
            tool_calls=[],
            model="llama-3.3-70b-versatile",
            latency_ms=None,
        )
