class DomainError(Exception):
    """Business-rule failure raised by services and translated to HTTP in the API layer."""

    status_code = 400

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    status_code = 404


class ConflictError(DomainError):
    status_code = 409


class BusinessRuleError(DomainError):
    status_code = 422


class PermissionDeniedError(DomainError):
    status_code = 403


class ServiceUnavailableError(DomainError):
    status_code = 503
