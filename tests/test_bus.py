import asyncio

import pytest

from tts_cli.application.bus import CommandBus, EventBus, EventProgress, ExecuteOperation
from tts_cli.core.events import ApplicationNotice, OperationCompleted, ProgressUpdated


def test_event_bus_orders_progress_and_rejects_late_events():
    bus = EventBus()
    received = []
    bus.subscribe(ProgressUpdated, received.append)
    bus.subscribe(OperationCompleted, received.append)
    progress = EventProgress(100, "Generate", bus, "op-1")

    progress.update(70, "TTS")
    bus.publish(ProgressUpdated("op-1", 1, 10, 100, "late"))
    bus.publish(OperationCompleted("op-1", 1))
    progress.update(100, "late progress")

    assert [type(event) for event in received] == [ProgressUpdated, OperationCompleted]
    assert received[0].sequence == 1


def test_command_bus_publishes_one_completion_event():
    async def operation() -> str:
        return "done"

    async def run() -> tuple[str, list[object]]:
        bus = EventBus()
        events: list[object] = []
        bus.subscribe(OperationCompleted, events.append)
        result = await CommandBus(bus).dispatch(ExecuteOperation(operation, "op-2"))
        return result, events

    result, events = asyncio.run(run())
    assert result == "done"
    assert len(events) == 1
    assert isinstance(events[0], OperationCompleted)


def test_event_bus_delivers_notices():
    bus = EventBus()
    received: list[ApplicationNotice] = []
    bus.subscribe(ApplicationNotice, received.append)

    bus.publish(ApplicationNotice("op-3", "debug", "ready"))

    assert received[0].message == "ready"
