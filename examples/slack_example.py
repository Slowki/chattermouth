#!/usr/bin/env python3

import asyncio
import logging
import os
import sys

import chattermouth
import chattermouth.slack
import slack


async def on_message() -> None:
    message = await chattermouth.listen()

    if "pie" in message.content:
        likes_apple_pie = await chattermouth.ask_yes_or_no("Do you like apple pie?")

        if likes_apple_pie:
            await chattermouth.tell(":apple: :pie:")
        else:
            await chattermouth.tell(":cherries: :pie:")


async def run() -> None:
    client = slack.RTMClient(
        token=os.environ["SLACK_API_TOKEN"], headers={"cookie": os.environ.get("SLACK_COOKIE")}, run_async=True,
    )

    logging.info("Training...")
    with chattermouth.enter_default_spacy_pipeline():
        chattermouth.slack.SlackInteractionFactory(client, callback=on_message)

        logging.info("Ready")
        await client.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
