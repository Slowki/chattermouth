"""A library for text based bot interactions."""

from .core import ask, enter_interaction_context, interaction_context, listen, tell

__all__ = ["ask", "enter_interaction_context", "interaction_context", "listen", "tell"]

try:
    from .nlp import ask_yes_or_no, enter_spacy_pipeline, enter_default_spacy_pipeline

    __all__ += ["ask_yes_or_no", "enter_spacy_pipeline", "enter_default_spacy_pipeline"]
except ImportError:
    pass
