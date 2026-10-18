"""Domain errors raised by services and turned into HTTP responses in main.py."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFound(DomainError):
    # Also used for other organisations' data, so its existence isn't leaked
    status_code = 404


class Conflict(DomainError):
    status_code = 409


class InvalidRequest(DomainError):
    status_code = 422
