class ManagerException(Exception):
    """Base exception for this script.

    :note: This exception should not be raised directly."""

class ChallengeRequiredException(ManagerException):
    pass

class NoUserIdException(ManagerException):
    pass
class OopsException(ManagerException):
    pass

class FeedbackRequired(ManagerException):
    pass

class LamadavaServerError(ManagerException):
    pass
class RapidApiError(ManagerException):
    pass
class NoFreeAccountError(LamadavaServerError):
    pass
class InstagramServerError(LamadavaServerError):
    pass

class InstaJSONDecodeError(ManagerException):
    pass
class RequestTimeOut(ManagerException):
    pass
class RequestProxyError(ManagerException):
    pass
class UnloadableParticipant(ManagerException):
    pass
class MessageLimitToday(ManagerException):
    pass

class WaitUntilException(ManagerException):
    pass

class CheckPointChallengeRequiedException(ManagerException):
    pass

class InstagramLoginError(ManagerException):
    pass
class UnDefinedException(ManagerException):
    pass

class LamadavaException(Exception):
    """Base exception for this script.

    :note: This exception should not be raised directly."""
class NoFreeAccounts(LamadavaException):
    pass


class UserIdsException(Exception):
    """Base exception for this script.

    :note: This exception should not be raised directly."""
class NotValidUserIds(Exception):
    pass

class AccountException(Exception):
    """Base exception for this script.

    :note: This exception should not be raised directly."""

class MessageLimitException(AccountException):
    """
    계정의 메세지 발송수가 한도를 초과할 때 발생하는에러
    """
    pass

class AccountRetryExcessException(AccountException):
    """
    계정 로그인 재시도 횟수가 한도를 초과할 때 발생하는에러
    """

class NoAvailableAccount(AccountException):
    """
    사용할 수 있는 계정이 없을때
    """
    pass