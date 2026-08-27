"""Small application buses shared by CLI and desktop clients."""

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

from tts_cli.core.events import ApplicationNotice, OperationCompleted, OperationFailed, ProgressUpdated

Event = ApplicationNotice | ProgressUpdated | OperationCompleted | OperationFailed
EventType = TypeVar("EventType", bound=Event)
EventHandler = Callable[[EventType], None]
Command = TypeVar("Command")


class ExecuteOperation:
    def __init__(self, operation: Callable[[], Awaitable[Any]], operation_id: str | None = None) -> None:
        self.operation = operation
        self.operation_id = operation_id


class EventProgress:
    enabled = True

    def __init__(self, total: int, label: str, event_bus: "EventBus", operation_id: str) -> None:
        self.total = max(total, 1)
        self.label = label
        self.event_bus = event_bus
        self.operation_id = operation_id

    def update(self, current: int, detail: str = "") -> None:
        sequence = self.event_bus.next_sequence(self.operation_id)
        self.event_bus.publish(ProgressUpdated(
            self.operation_id, sequence, min(max(current, 0), self.total),
            self.total, detail or self.label,
        ))

    def finish(self) -> None:
        return None


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[Callable[[Any], None]]] = defaultdict(list)
        self._sequence_counters: dict[str, int] = {}
        self._last_sequence: dict[str, int] = {}
        self._completed: set[str] = set()

    def next_sequence(self, operation_id: str) -> int:
        sequence = self._sequence_counters.get(operation_id, 0) + 1
        self._sequence_counters[operation_id] = sequence
        return sequence

    def subscribe(self, event_type: type[EventType], handler: EventHandler[EventType]) -> None:
        self._handlers[cast(type[Event], event_type)].append(handler)

    def publish(self, event: Event) -> None:
        operation_id = getattr(event, "operation_id", None)
        if operation_id is not None:
            if operation_id in self._completed:
                return
            if isinstance(event, ProgressUpdated):
                last_sequence = self._last_sequence.get(operation_id, 0)
                if event.sequence <= last_sequence:
                    return
                self._last_sequence[operation_id] = event.sequence
            elif isinstance(event, (OperationCompleted, OperationFailed)):
                self._completed.add(operation_id)
        for handler in tuple(self._handlers[type(event)]):
            handler(event)


class CommandBus:
    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._handlers: dict[type[Any], Callable[[object], Awaitable[Any]]] = {}
        self.event_bus = event_bus
        self.register(ExecuteOperation, self._execute_operation)

    async def _execute_operation(self, command: ExecuteOperation) -> Any:
        try:
            result = await command.operation()
        except Exception as error:
            if self.event_bus is not None and command.operation_id is not None:
                self.event_bus.publish(OperationFailed(command.operation_id, error))
            raise
        if self.event_bus is not None and command.operation_id is not None:
            self.event_bus.publish(OperationCompleted(command.operation_id, result))
        return result

    def register(self, command_type: type[Command], handler: Callable[[Command], Awaitable[Any]]) -> None:
        self._handlers[command_type] = cast(Callable[[object], Awaitable[Any]], handler)

    async def dispatch(self, command: object) -> Any:
        try:
            handler = self._handlers[type(command)]
        except KeyError as error:
            raise LookupError(f"Chưa đăng ký command: {type(command).__name__}") from error
        return await handler(command)
