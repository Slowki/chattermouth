import random
from typing import Any, Dict, Iterable, Sequence, Set, Tuple

import spacy
from spacy.util import compounding, minibatch

from .categories import CATEGORIES, Category

TRAINING_DATA: Sequence[Tuple[str, Set[Category]]] = [
    # Yes
    ("absolutely", {Category.YES}),
    ("Affirmative", {Category.YES}),
    ("I agree", {Category.YES}),
    ("I think so", {Category.YES}),
    ("it does", {Category.YES}),
    ("it doesn't", {Category.YES}),
    ("sure", {Category.YES}),
    ("yea", {Category.YES}),
    ("yeah", {Category.YES}),
    ("yep", {Category.YES}),
    ("yeppers", {Category.YES}),
    ("yes 🙂", {Category.YES}),
    ("yes it does", {Category.YES}),
    ("yes it does", {Category.YES}),
    ("yes", {Category.YES}),
    ("yup", {Category.YES}),
    ("👍", {Category.YES}),
    # No
    ("I disagree", {Category.NO}),
    ("I don't think so", {Category.NO}),
    ("it does not", {Category.NO}),
    ("it doesn't", {Category.NO}),
    ("nah", {Category.NO}),
    ("naw", {Category.NO}),
    ("negative", {Category.NO}),
    ("no 🙁", {Category.NO}),
    ("no but it might have made it a bit better", {Category.NO}),
    ("no thanks", {Category.NO}),
    ("no", {Category.NO}),
    ("nope", {Category.NO}),
    ("not really", {Category.NO}),
    ("👎", {Category.NO}),
    # Questions
    ("Do you think that's a good idea", {Category.QUESTION}),
    ("how do I do that?", {Category.QUESTION}),
    ("how", {Category.QUESTION}),
    ("like, why though?", {Category.QUESTION}),
    ("what?", {Category.QUESTION}),
    ("what", {Category.QUESTION}),
    ("where is that?", {Category.QUESTION}),
    ("where", {Category.QUESTION}),
    ("who", {Category.QUESTION}),
    ("why", {Category.QUESTION}),
    ("wut", {Category.QUESTION}),
    ("Yes but how?", {Category.QUESTION, Category.YES}),
    # Unaligned
    ("I don't know", set()),
    ("I like both coffee and donuts", set()),
    ("It's all on fire!", set()),
    ("maybe", set()),
    ("The quick dog jumped over the angry fox", set()),
]
"""Some (very basic) training data."""


def _create_training_entry(message: str, categories: Sequence[Category]) -> Tuple[str, Dict[str, Any]]:
    cats = {}
    for cat in categories:
        assert cat in CATEGORIES
        cats[cat.value] = 1.0
    for cat in CATEGORIES:
        if cat not in categories:
            cats[cat.value] = 0.0
    return (message, {"cats": cats})


def get_classification_training_data() -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Get text classification training data."""
    return (_create_training_entry(*pair) for pair in TRAINING_DATA)  # type: ignore


TEXTCAT = "textcat"


def train_pipeline(nlp: spacy.language.Language) -> None:
    """Train a `spacy.language.Language` instance."""
    if TEXTCAT not in nlp.pipe_names:
        textcat = nlp.create_pipe(TEXTCAT, config={"exclusive_classes": False})
        nlp.add_pipe(textcat, last=True)
    else:
        textcat = nlp.get_pipe(TEXTCAT)

    for category in CATEGORIES:
        textcat.add_label(category.value)

    pipe_exceptions = {TEXTCAT, "trf_wordpiecer", "trf_tok2vec"}
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    with nlp.disable_pipes(*other_pipes):  # only train textcat
        all_data = list(get_classification_training_data())
        random.shuffle(all_data)

        training_data = all_data[: len(all_data) - 2]
        validation_data = all_data[len(all_data) - 2 :]

        optimizer = nlp.begin_training()
        for itn in range(20):
            losses: Dict[str, Any] = {}
            random.shuffle(training_data)
            batches = minibatch(training_data, size=compounding(4.0, 32.0, 1.001))

            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, drop=0.2, losses=losses)
