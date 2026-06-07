class AutoForgeError(Exception):
    """Base exception for service-level failures."""


class ToolNotFoundError(AutoForgeError):
    """Raised when a requested tool is not registered."""


class ToolExecutionError(AutoForgeError):
    """Raised when a tool fails after retry handling."""


class PlanValidationError(AutoForgeError):
    """Raised when a plan cannot be executed safely."""


class RateLimitExceeded(AutoForgeError):
    """Raised when a caller exceeds local rate limits."""

