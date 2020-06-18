#!/usr/bin/env python3

import asyncio

import chattermouth
import chattermouth.cli


async def run() -> None:
    message = await chattermouth.ask("gimme some input: ")
    name = await message.user.get_full_name()
    print(f"{name} said {str(message)}")


if __name__ == "__main__":
    with chattermouth.enter_interaction_context(chattermouth.cli.CliInteractionContext()):
        asyncio.run(run())
