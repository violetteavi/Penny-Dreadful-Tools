"""Reference decks for every model (#57; Scenarios.md, "Reference decks for every model"): real season 39 decks, and one hand-made deck, that every model is
checked on, whatever its method.

- Guards are decks every current model gets right. A model must keep them right, so tests assert them.
- Hard cases are decks the current models get wrong (only the site's guesser passes one, 269591). They're recorded, never required: a model can be
  better overall and still fail some.
- Extremes are too far outside the data for "right" to be clear, so they're only recorded.

The four hard cases that stand for a group carry its decks in GROUPS: the season 39 decks that run 8 ranked the same way, with the same top guess. They
were frozen from run 8 on 2026-10-14, so later models don't move the groups.

The extreme, HAND_MADE_ID, isn't a real submission: its maindeck is written out here and it's built in memory, never loaded or stored. Its id is
negative so it can never collide with a real deck.
"""
import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.data_loading.slices import Snapshot
from archetype_classifier.evaluation.model import PredictDeck, Prediction, plural, predict_deck, sorted_lines

logger = logging.getLogger(__name__)

HAND_MADE_ID = -1
TOP_FIVE = 5


class Kind(Enum):
    GUARD = 'guard'
    HARD = 'hard case'
    EXTREME = 'extreme'

@dataclass(frozen=True)
class ReferenceDeck:
    deck_id: int
    label: str | None  # The archetype's name, resolved against the snapshot when scored; None for an extreme.
    kind: Kind
    top: int  # Passes if the label is within this many candidates (or is the guess, for a model without candidates); 0 for an extreme.
    why: str
    maindeck: tuple[CardCount, ...] | None = None  # Only for a hand-made deck; a real deck's cards are loaded.

@dataclass(frozen=True)
class ReferenceResult:
    deck_id: int
    rank: int | None  # The label's position among the candidates (1 for a correct guess, for a model without candidates); None if it isn't there.
    passed: bool | None  # None for an extreme, or for a label the snapshot lacks.
    guess_id: int | None
    top_five: tuple[int, ...]  # The first five candidates; empty for a model without candidates.
    missing_label: bool


def lines(*counts: tuple[int, str]) -> tuple[CardCount, ...]:
    return sorted_lines(tuple(CardCount(card, n) for n, card in counts))

# Every card is legal in season 39 and in no season before; no deck from seasons 1-38 plays any of them.
ALL_NEW_SIMIC = lines(
    (4, 'Botanical Sanctum'), (4, 'Breeding Pool'), (4, 'Waterlogged Grove'), (4, 'Daily Bugle Building'), (4, 'Zanarkand, Ancient Metropolis'),
    (4, 'Jidoor, Aristocratic Capital'), (4, 'Genemorph Imago'), (4, "Mysterio's Phantasm"), (4, 'Guy in the Chair'), (4, 'Professional Wrestler'),
    (2, 'The Wandering Minstrel'), (2, 'Spider-Byte, Web Warden'), (2, 'Tributary Instructor'), (4, 'Whoosh!'), (4, 'Kapow!'), (3, 'Amazing Acrobatics'),
    (2, 'Oko, the Ringleader'), (1, 'School Daze'),
)

REFERENCE_DECKS = (
    ReferenceDeck(269508, 'Oops All Lands', Kind.GUARD, 1, 'an exact match: identical to training decks 264496 and 264554'),
    ReferenceDeck(269539, 'Mono Green Stompy', Kind.GUARD, 1, 'a small drift: 4 cards off its closest training deck'),
    ReferenceDeck(269503, 'Selesnya Heroic', Kind.GUARD, 1, 'a larger drift: 12 cards off its closest training deck'),
    ReferenceDeck(269833, 'Azorius Legends Aggro', Kind.GUARD, 1, 'a few new cards: 5 unseen copies'),
    ReferenceDeck(269466, 'Hardened Scales Affinity', Kind.GUARD, 1, 'many new cards: 12 unseen copies'),
    ReferenceDeck(269484, 'Blink', Kind.HARD, 1, 'dilution: Nadu Combo shares its shell'),
    ReferenceDeck(269637, 'Equipment Aggro', Kind.HARD, 1, 'a shell shared with Red Deck Wins'),
    ReferenceDeck(271375, 'Enchantments Matter', Kind.HARD, 1, 'overlapping labels: Enchantress and Zur the Enchanter'),
    ReferenceDeck(269591, 'Izzet Madcap', Kind.HARD, 5, 'a new archetype: 3 training decks'),
    ReferenceDeck(269653, 'Izzet Madcap', Kind.HARD, 5, 'a new archetype with new cards: 5 unseen copies'),
    ReferenceDeck(269940, 'Midrange', Kind.HARD, 1, 'many new cards: 27 unseen copies, the most in season 39'),
    ReferenceDeck(270398, 'Orzhov Midrange', Kind.HARD, 1, 'drift: 20 cards off its closest training deck'),
    ReferenceDeck(HAND_MADE_ID, None, Kind.EXTREME, 0, 'only newly legal cards, lands included', ALL_NEW_SIMIC),
)

GROUPS: dict[int, tuple[int, ...]] = {
    269484: (269484, 269485, 269486, 269502, 270039),
    269637: (269637, 269689, 269705, 269778, 269863, 269867, 269880, 269881, 269904, 269905, 269906, 269911, 269925, 269936, 269958, 269981, 270094, 270105,
             270137, 270194, 270241, 270245, 270265, 270307, 270375, 270392, 270406, 270417, 270418, 270422, 270488, 270548, 270569, 270591, 270616, 270629,
             270631, 270634, 270644, 270655, 270676, 270682, 270704, 270732, 270770, 270776, 270838, 270863, 270902, 270930, 270967, 270982, 271548, 271588,
             271610, 271642, 271677, 271719, 271743, 271753, 271755, 271786, 271791, 271817, 271840, 271873),
    271375: (270348, 271154, 271183, 271233, 271327, 271338, 271375),
    269591: (269591, 269599, 269604, 269608, 269609, 269612, 269616, 269631, 269682, 269699, 269714, 269734, 269768, 269773, 269788, 269791, 269865, 270031,
             270305, 270530, 270558, 270772, 270904, 271522),
}


def build_hand_made_deck() -> PredictDeck:
    return PredictDeck(HAND_MADE_ID, 'League', ALL_NEW_SIMIC, ())

def load_reference_decks(snapshot: Snapshot, decks: Sequence[ReferenceDeck] = REFERENCE_DECKS, groups: Mapping[int, tuple[int, ...]] = GROUPS) -> dict[int, PredictDeck]:
    """Every reference deck and every deck of its groups, ready to predict. Real decks come from the snapshot and the site database; a hand-made deck
    is built from its maindeck and never loaded. A deck the snapshot lacks, or with no cards, is skipped with a warning."""
    wanted = sorted({d.deck_id for d in decks if d.maindeck is None} | {i for group in groups.values() for i in group})
    if lacking := [i for i in wanted if i not in snapshot.decks]:
        logger.warning('Skipped %d reference deck%s the snapshot lacks: %s', len(lacking), plural(lacking), lacking)
    contents = loader.load_contents([i for i in wanted if i in snapshot.decks])
    if empty := sorted(i for i, c in contents.items() if not c.maindeck):
        logger.warning('Skipped %d reference deck%s with no cards: %s', len(empty), plural(empty), empty)
    loaded = {i: predict_deck(snapshot.decks[i], c) for i, c in sorted(contents.items()) if c.maindeck}
    loaded.update({d.deck_id: PredictDeck(d.deck_id, 'League', d.maindeck, ()) for d in decks if d.maindeck is not None})
    return loaded

def build_reference_result(deck: ReferenceDeck, prediction: Prediction, archetype_ids: Mapping[str, int]) -> ReferenceResult:
    """How one model did on one deck: the reference deck itself, or another deck of its group, judged by the reference deck's label and mark.
    A label the snapshot lacks is warned about and recorded, never fatal."""
    top_five = tuple(c.archetype_id for c in prediction.candidates[:TOP_FIVE]) if prediction.candidates is not None else ()
    if deck.label is None:
        return ReferenceResult(prediction.deck_id, None, None, prediction.guess_id, top_five, False)
    if deck.label not in archetype_ids:
        logger.warning('No archetype named %r for reference deck %d', deck.label, deck.deck_id)
        return ReferenceResult(prediction.deck_id, None, None, prediction.guess_id, top_five, True)
    label_id = archetype_ids[deck.label]
    if prediction.candidates is None:
        rank = 1 if prediction.guess_id == label_id else None
    else:
        rank = next((k for k, c in enumerate(prediction.candidates, start=1) if c.archetype_id == label_id), None)
    return ReferenceResult(prediction.deck_id, rank, rank is not None and rank <= deck.top, prediction.guess_id, top_five, False)

def build_reference_table(results: Mapping[str, Mapping[int, ReferenceResult]], names: Mapping[int, str], decks: Sequence[ReferenceDeck] = REFERENCE_DECKS,
                          groups: Mapping[int, tuple[int, ...]] = GROUPS) -> str:
    """The Markdown a write-up carries: each model's result for each reference deck, then each group's pass rate. Results are by model, then deck id."""
    models = list(results)
    out = [f'| Deck | Kind | Label | Pass if | {" | ".join(models)} |', '|---|---|---|---|' + '---|' * len(models)]
    for deck in decks:
        mark = '—' if deck.kind == Kind.EXTREME else 'candidate 1' if deck.top == 1 else f'top {deck.top}'
        cells = [result_cell(results[m].get(deck.deck_id), names) for m in models]
        out.append(f'| {deck.deck_id} | {deck.kind.value} | {deck.label or "—"} | {mark} | {" | ".join(cells)} |')
    by_id = {d.deck_id: d for d in decks}
    if groups:
        out += ['', f'| Group of | Label | Decks | {" | ".join(models)} |', '|---|---|---|' + '---|' * len(models)]
        for deck_id, group in groups.items():
            rates = []
            for m in models:
                scored = [results[m][i] for i in group if i in results[m]]
                rates.append(f'{sum(1 for r in scored if r.passed)} / {len(scored)}')
            out.append(f'| {deck_id} | {by_id[deck_id].label} | {len(group)} | {" | ".join(rates)} |')
    return '\n'.join(out) + '\n'

def result_cell(result: ReferenceResult | None, names: Mapping[int, str]) -> str:
    if result is None:
        return 'not predicted'
    if result.missing_label:
        return 'label missing'
    if result.passed is None:  # An extreme: what the model did, with no mark.
        guess = 'no guess' if result.guess_id is None else f'guess {names.get(result.guess_id, str(result.guess_id))}'
        top = f'top 5: {", ".join(names.get(i, str(i)) for i in result.top_five)}' if result.top_five else 'no candidates'
        return f'{guess}; {top}'
    return f'{result.rank if result.rank is not None else "not ranked"}, {"pass" if result.passed else "fail"}'
