import asyncio
import getpass
import os
import pwd
import subprocess
from typing import Optional

from .core import AbstractInteractionContext, Message, UserInfo


class CliUserInfo(UserInfo):
    def __init__(self):
        self.user: str = getpass.getuser()
        self.user_id: str = str(os.getuid())

    async def get_full_name(self) -> Optional[str]:
        """Get the full name of the user."""
        return pwd.getpwnam(self.user).pw_gecos.split(",")[0]


class CliMessage(Message):
    def __init__(self, content: str) -> None:
        self.user: UserInfo = CliUserInfo()
        self.content: str = content

    def __str__(self) -> str:
        return self.content


class CliInteractionContext(AbstractInteractionContext):
    """The abstract super type of the context used for interacting with the user."""

    def __init__(self) -> None:
        pass

    async def tell(self, message: str) -> None:
        """Send a message to the user."""
        print(message)

    async def listen(self) -> CliMessage:
        """Listen for a message from the user."""
        return CliMessage(input())

    async def ask(self, message: str) -> CliMessage:
        return CliMessage(input(message))
