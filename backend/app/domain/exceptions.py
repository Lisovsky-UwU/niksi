class DomainError(Exception):
    """Base class for all business-logic errors raised by use cases."""


class NotFoundError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass


class ForbiddenError(DomainError):
    """The user is authenticated but may not touch this record (e.g. the partner's grey zone)."""
