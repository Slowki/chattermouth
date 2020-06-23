# `chattermouth`

[![Documentation](https://img.shields.io/badge/Documentation-chattermouth-blue)](https://slowki.github.io/chattermouth)
![CI](https://github.com/Slowki/chattermouth/workflows/CI/badge.svg)

A library for text based bot interactions.

## Example

```python
async def maybe_apply_change(change_id: str) -> None:
    try:
        if await ask_yes_or_no("Do you want to apply that change now?"):
            # We got a "yes" type response.
            apply_change(change_id)
        else:
            # We got a "no" type response.
            await tell(f"Okay, if you want to apply it later run 'corp-apply-change {change_id}'.")
    except NoClassificationError:
        # We got something that wasn't a "yes" or a "no" type of message.
        await tell("Sorry, I didn't understand that")
```

## Supported Backends

- CLI
- Slack
