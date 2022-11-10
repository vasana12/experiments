class InstabotException(Exception):

    pass

class QueryReturnedBadRequestException(InstabotException):
    pass


class QueryReturnedForbiddenException(InstabotException):
    pass


class ProfileNotExistsException(InstabotException):
    pass

class LocationNotExistsException(InstabotException):
    pass
class PrivateProfileNotFollowedException(InstabotException):
    pass


class LoginRequiredException(InstabotException):
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


class QueryReturnedNotFoundException(ConnectionException):
    pass


class TooManyRequestsException(ConnectionException):
    pass

class IPhoneSupportDisabledException(InstabotException):
    pass


