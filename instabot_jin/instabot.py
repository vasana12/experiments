from typing import Callable,List, Optional
from .instabotcontext import InstabotContext
class InstaBot:

    def __init__(self,
                 sleep: bool = True,
                 quiet: bool = False,
                 user_agent: Optional[str] = None,
                 max_connection_attempts: int = 3,
                 request_timeout: float = 300.0,

                 fatal_status_codes: Optional[List[int]] = None,
                 iphone_support: bool = True):
        self.context = InstabotContext(sleep, quiet, user_agent, max_connection_attempts,
                                          request_timeout, fatal_status_codes,
                                          iphone_support)


    def test_login(self) -> Optional[str]:
        return self.context.test_login()

    def login(self, user: str, passwd: str) -> None:

        self.context.login(user, passwd)
