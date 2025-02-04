class YayError(Exception):
    pass


class AuthenticationError(YayError):
    pass


class ForbiddenError(YayError):
    pass


class RateLimitError(YayError):
    pass


class ExceedCallQuotaError(YayError):
    pass


class InvalidSignedInfo(YayError):
    pass


class UnknownError(YayError):
    pass
