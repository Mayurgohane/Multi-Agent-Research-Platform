"""Domain exceptions."""


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, *, code: str = "app_error") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found")


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict") -> None:
        super().__init__(message, code="conflict")


class ExternalServiceError(AppError):
    def __init__(self, message: str, *, service: str) -> None:
        super().__init__(message, code=f"{service}_error")
        self.service = service


class JobStateError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="job_state_error")
