class ManagerException(Exception):
    """Base exception for this script.

    :note: This exception should not be raised directly."""

class ChallengeRequiredException(ManagerException):
    pass

class NoUserIdException(ManagerException):
    pass

class WaitUntilException(ManagerException):
    pass

class CheckPointChallengeRequiedException(ManagerException):
    pass

class UnDefinedException(ManagerException):
    pass