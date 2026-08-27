"""Public error names for application and provider boundaries."""


class TTSCLIError(Exception):
	"""Base exception for expected CLI failures."""


class RetryExhaustedError(TTSCLIError, RuntimeError):
	"""Raised when an operation fails after all configured retry attempts."""

	def __init__(self, attempts: int, cause: Exception):
		self.attempts = attempts
		self.cause = cause
		super().__init__(f"Operation thất bại sau {attempts} lần thử: {cause}")


__all__ = ["RetryExhaustedError", "TTSCLIError"]