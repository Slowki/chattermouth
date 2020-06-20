import abc
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator, Optional


class UserInfo(abc.ABC):
    """Information about the user."""

    @abc.abstractmethod
    async def get_full_name(self) -> Optional[str]:
        """Get the full name of the user."""
        ...

    async def get_first_name(self) -> Optional[str]:
        """Get the first name of the user."""
        full_name = await self.get_full_name()
        if full_name:
            return full_name.split()[0]
        return None

    async def get_last_name(self) -> Optional[str]:
        """Get the last name of the user."""
        full_name = await self.get_full_name()
        if full_name:
            return full_name.split()[-1]
        return None

    async def get_email(self) -> Optional[str]:
        """Get the email address of the user."""
        return None


class Message:
    user: UserInfo
    content: str

    def __str__(self) -> str:
        return self.content

    def __len__(self) -> int:
        return len(self.content)


class AbstractInteractionContext(abc.ABC):
    """The abstract super type of the context used for interacting with the user."""

    @abc.abstractmethod
    async def tell(self, message: str) -> None:
        """Send a message to the user.

        Args:
            message: The message to send to the user.
        """
        ...

    @abc.abstractmethod
    async def listen(self) -> Message:
        """Listen for a message from the user.

        Returns:
            The first message the user reponds with.
        """
        ...

    async def ask(self, message: str) -> Message:
        """Send a message to the user and listen for a response.

        Args:
            message: The message to send to the user.

        Returns:
            The first message the user responds with.
        """
        await self.tell(message)
        return await self.listen()


_context: ContextVar[Optional[AbstractInteractionContext]] = ContextVar("context", default=None)


def get_interaction_context() -> Optional[AbstractInteractionContext]:
    """Get the current `AbstractInteractionContext`."""
    return _context.get()


def interaction_context() -> AbstractInteractionContext:
    """Get the current `AbstractInteractionContext`.

    Raises:
        AssertionError: If the context is not set.
    """
    context = get_interaction_context()
    assert context is not None
    return context


def set_interaction_context(context: Optional[AbstractInteractionContext] = None,) -> None:
    """Set the current `AbstractInteractionContext`."""
    _context.set(context)


@contextmanager
def enter_interaction_context(context: Optional[AbstractInteractionContext] = None) -> Generator[None, None, None]:
    """Set the current `AbstractInteractionContext` for a scope.

    >>> import chattermouth.cli
    >>> context = chattermouth.cli.CliInteractionContext()
    >>> with enter_interaction_context(context):
    ...     interaction_context() is context
    True
    """
    token = _context.set(context)
    yield
    _context.reset(token)


async def tell(message: str) -> None:
    """Send a message to the user.

    Args:
        message: The message to send to the user.
    """
    return await interaction_context().tell(message)


async def listen() -> Message:
    """Listen for a message from the user.

    Returns:
        The first message the user reponds with.
    """
    return await interaction_context().listen()


async def ask(message: str) -> Message:
    """Send a message to the user and listen for a response.

    Args:
        message: The message to send to the user.

    Returns:
        The first message the user responds with.
    """
    return await interaction_context().ask(message)
