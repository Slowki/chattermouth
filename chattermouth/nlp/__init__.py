"""General NLP based utilities based on [spaCy](https://spacy.io/)."""

from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from typing import Any, ContextManager, Dict, Generator, Optional, Sequence

import spacy
from spacy.util import compounding, minibatch

from ..core import Message, ask
from .categories import Category
from .training import train_pipeline

_spacy_pipeline: ContextVar[Optional[spacy.language.Language]] = ContextVar("spacy_pipeline", default=None)


class NoClassificationError(Exception):
    """A piece of text could not be classified."""

    def __init__(self, text: str, classifications: Sequence[Category]) -> None:
        self.text: str = text
        """The text which could not be classified."""

        super().__init__(f"Could not classify {text} as any of {classifications}")


async def ask_yes_or_no(question: str, threshold: float = 0.75) -> bool:
    """Ask a yes or no question.

    ## Example
    ```python
    try:
        if ask_yes_or_no("Do you want to apply that change now?"):
            # We got a "yes" type response.
            apply_change(change_id)
        else:
            # We got a "no" type response.
            tell(f"Okay, if you want to apply it later run 'corp-apply-change {change_id}'.")
    except NoClassificationError:
        # We got something that wasn't a "yes" or a "no" type of message.
        tell("Sorry, I didn't understand that")
    ```

    Args:
        question: The question to ask the user.
        threshold: The confidence threshold for the classification.

    Raises:
        NoClassificationError: If the response cannot be classifed as a "yes" or a "no".

    Returns:
        `True` if the response was similiar to yes, eg. "Yep, it does." or `False` if if the statement is similiar to
        a no, eg. "No, I don't.".
    """
    return classify_yes_no(str(await ask(question)), threshold=threshold)


def classify_yes_no(text: str, threshold: float) -> bool:
    """Classify a piece of text as either a "yes" response or a "no" response.

    >>> with enter_default_spacy_pipeline():
    ...     classify_yes_no("yeah", threshold=0.75)
    True

    Args:
        text: The text to classify.
        threshold: The confidence threshold for the classification.

    Raises:
        NoClassificationError: If the text cannot be classifed as a "yes" or a "no".

    Returns:
        `True` if the response was similiar to yes, eg. "Yep, it does." or `False` if the statement is similiar to
        a no, eg. "No, I don't.".
    """
    assert 0.0 < threshold < 1.0
    doc = spacy_pipeline()(text)
    if doc.cats[Category.YES.value] >= threshold and doc.cats[Category.YES.value] >= doc.cats[Category.NO.value]:
        return True
    elif doc.cats[Category.NO.value] >= threshold:
        return False

    raise NoClassificationError(str(text), [Category.YES, Category.NO])


def process_message(message: Message) -> spacy.tokens.doc.Doc:
    """Run a `Message` through the spaCy pipeline."""
    return spacy_pipeline()(str(message))


def get_spacy_pipeline() -> Optional[spacy.language.Language]:
    """Get the current `spacy.language.Language`."""
    return _spacy_pipeline.get()


def spacy_pipeline() -> spacy.language.Language:
    """Get the current `spacy.language.Language`.

    Raises:
        AssertionError: If the context is not set.
    """
    context = get_spacy_pipeline()
    assert context is not None
    return context


def set_spacy_pipeline(context: Optional[spacy.language.Language] = None,) -> None:
    """Set the current `spacy.language.Language`."""
    _spacy_pipeline.set(context)


@contextmanager
def enter_spacy_pipeline(context: Optional[spacy.language.Language] = None) -> Generator[None, None, None]:
    """Set the current spaCy pipeline for a scope."""
    token = _spacy_pipeline.set(context)
    yield
    _spacy_pipeline.reset(token)


def enter_default_spacy_pipeline() -> ContextManager:
    """Set the current spaCy pipeline for a scope to a default."""
    return enter_spacy_pipeline(get_default_spacy_pipeline())


_spacy_model_sizes = ["lg", "md", "sm"]
_spacy_languages = ["en"]


@lru_cache(1)
def get_default_spacy_pipeline() -> spacy.language.Language:
    """Get a default spaCy pipeline."""
    nlp = None

    for language in _spacy_languages:
        for size in _spacy_model_sizes:
            try:
                nlp = spacy.load(f"{language}_core_web_{size}")
                break
            except OSError:
                pass

    if nlp is None:
        raise Exception("Failed to find any models")

    train_pipeline(nlp)
    return nlp
