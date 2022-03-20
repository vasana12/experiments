class InstabotException(Exception):
    """Base exception for this script.

    :note: This exception should not be raised directly."""
    pass


class QueryReturnedBadRequestException(InstabotException):
    pass


class QueryReturnedForbiddenException(InstabotException):
    pass


class ProfileNotExistsException(InstabotException):
    pass


class PrivateProfileNotFollowedException(InstabotException):
    pass


class LoginRequiredException(InstabotException):
    pass

class LoginFailedException(InstabotException):
    pass

class TwoFactorAuthRequiredException(InstabotException):
    pass


class InvalidArgumentException(InstabotException):
    pass


class BadResponseException(InstabotException):
    pass


class BadCredentialsException(InstabotException):
    pass


class ConnectionException(InstabotException):
    pass


class PostChangedException(InstabotException):
    pass


class QueryReturnedNotFoundException(InstabotException):
    pass


class TooManyRequestsException(ConnectionException):
    pass

class IPhoneSupportDisabledException(InstabotException):
    pass

class AbortDownloadException(Exception):
    pass