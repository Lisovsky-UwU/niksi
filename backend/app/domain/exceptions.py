class DomainError(Exception):
    """Base class for all business-logic errors raised by use cases."""


class NotFoundError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class AuthenticationError(DomainError):
    pass
