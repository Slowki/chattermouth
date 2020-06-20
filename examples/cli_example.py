#!/usr/bin/env python3

import asyncio

import chattermouth
import chattermouth.cli


async def run() -> None:
    likes_apple_pie = await chattermouth.ask_yes_or_no("Do you like apple pie? ")

    if likes_apple_pie:
        print("apple")
    else:
        print("peach I guess")


if __name__ == "__main__":
    with chattermouth.enter_interaction_context(chattermouth.cli.CliInteractionContext()):
        with chattermouth.enter_default_spacy_pipeline():
            asyncio.run(run())
