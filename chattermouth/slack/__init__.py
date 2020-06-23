import asyncio
import traceback
import weakref
from typing import Any, Awaitable, Callable, Dict, Optional, Set

import slack

from ..core import AbstractInteractionContext, Message, UserInfo, enter_interaction_context


class SlackInteractionFactory:
    """A `AbstractInteractionContext` producer using a `slack.RTMClient`.

    ## Example
    ```python
    async def on_message():
        print("Someone said", str(await chattermouth.listen()))

    client = slack.RTMClient(token = "xoxb-1234ABC...", run_async = True)
    chattermouth.slack.SlackInteractionFactory(client, callback = on_message)
    await client.start()
    ```

    Args:
        rtm_client: An RTM client constructed with `run_async` enabled.
        callback: The callback to call for each new message.
    """

    def __init__(self, rtm_client: slack.RTMClient, callback: Callable[[], Any]) -> None:
        slack.RTMClient.on(event="message", callback=self._on_message)
        self.callback = callback
        self._interactions: Dict[str, weakref.WeakValueDictionary[str, SlackInteractionContext]] = {}

    def _get_interaction(self, user: str, ts: str) -> Optional["SlackInteractionContext"]:
        interaction_map: weakref.WeakValueDictionary[str, SlackInteractionContext]
        if user in self._interactions:
            interaction_map = self._interactions[user]
        else:
            interaction_map = weakref.WeakValueDictionary()
            self._interactions[user] = interaction_map
        return interaction_map.get(ts)

    async def _on_message(self, web_client: slack.WebClient, data: dict, **payload) -> None:
        subtype = data.get("subtype")
        if subtype == "message_deleted":
            interaction = self._get_interaction(
                data["previous_message"]["user"], data["previous_message"].get("thread_ts", data["ts"])
            )
            if interaction:
                interaction.deleted_message.add(data["deleted_ts"])

        if subtype is None:
            thread = data.get("thread_ts", data["ts"])
            user = data["user"]
            interaction = self._get_interaction(user, thread)
            if interaction is not None:
                await interaction.message_queue.put(data)
                return

            context = SlackInteractionContext(web_client=web_client, data=data)
            self._interactions[user][thread] = context
            with enter_interaction_context(context):
                callback_result = self.callback()
                if asyncio.iscoroutine(callback_result):
                    asyncio.create_task(callback_result)


class SlackUserInfo(UserInfo):
    def __init__(self, web_client: slack.WebClient, id: str):
        self.id = id
        """The ID of the user."""

        self._web_client: slack.WebClient = web_client
        self._cached_info: Optional[dict] = None

    async def _user_info(self) -> dict:
        if self._cached_info is None:
            self._cached_info = (await self._web_client.users_info(user=self.id))["user"]  # type: ignore
        return self._cached_info

    async def _get_profile(self) -> dict:
        return (await self._user_info())["profile"]

    async def get_full_name(self) -> Optional[str]:
        return (await self._get_profile())["real_name"]

    async def get_first_name(self) -> Optional[str]:
        return (await self._get_profile())["first_name"]

    async def get_last_name(self) -> Optional[str]:
        return (await self._get_profile())["last_name"]

    async def get_email(self) -> str:
        return (await self._get_profile())["email"]


class SlackMessage(Message):
    """A message from the CLI."""

    def __init__(self, user: SlackUserInfo, content: str) -> None:
        self.user: SlackUserInfo = user
        """The user associated with this `Message`."""

        self.content: str = content
        """The content of the message."""

    def __str__(self) -> str:
        return self.content


class SlackInteractionContext(AbstractInteractionContext):
    """An interaction context for Slack."""

    def __init__(self, web_client: slack.WebClient, data: dict) -> None:
        self.web_client: slack.WebClient = web_client
        """The web client used to access Slack."""

        self.ts = data["ts"]
        """The `ts` of the original entry."""

        self.thread_ts = data.get("thread_ts") or self.ts
        """The `ts` of the associated thread."""

        self.channel = data["channel"]
        """The channel the original message was posted in."""

        self.user = SlackUserInfo(web_client, data["user"])
        """The user who posted the message."""

        self._send_lock = asyncio.Lock()

        self.message_queue: asyncio.Queue[dict] = asyncio.Queue()
        self.message_queue.put_nowait(data)
        self.deleted_message: Set[str] = set()

    def _create_message(self, data: dict) -> SlackMessage:
        return SlackMessage(user=self.user, content=data["text"])

    async def tell(self, message: str) -> None:
        async with self._send_lock:
            result = await self.web_client.chat_postMessage(  # type: ignore
                text=message, channel=self.channel, thread_ts=self.thread_ts
            )
            self.deleted_message.add(result["message"]["ts"])

    async def listen(self) -> SlackMessage:
        while True:
            data = await self.message_queue.get()

            async with self._send_lock:
                if data["ts"] in self.deleted_message:
                    self.deleted_message.remove(data["ts"])
                    continue
            return self._create_message(data)
