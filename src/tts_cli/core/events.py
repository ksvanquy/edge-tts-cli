"""Framework-independent events emitted by application workflows."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressUpdated:
    operation_id: str
    sequence: int
    current: int
    total: int
    stage: str


@dataclass(frozen=True)
class ApplicationNotice:
    operation_id: str | None
    level: str
    message: str


@dataclass(frozen=True)
class OperationCompleted:
    operation_id: str
    result: object


@dataclass(frozen=True)
class OperationFailed:
    operation_id: str
    error: Exception
