"""Reference decks for every model (#57; Scenarios.md, "Reference decks for every model"): real season 39 decks, and one hand-made deck, that every model is
checked on, whatever its method.

- Guards are decks every current model gets right. A model must keep them right, so tests assert them.
- Hard cases are decks no current model gets right. They're recorded, never required: a model can be better overall and still fail some.
- Extremes are too far outside the data for "right" to be clear, so they're only recorded.

The four hard cases that stand for a group carry its decks in GROUPS: the season 39 decks that run 8 ranked the same way, with the same top guess. They
were frozen from run 8 on 2026-10-14, so later models don't move the groups.

The extreme, HAND_MADE_ID, isn't a real submission: its maindeck is written out here and it's built in memory, never loaded or stored. Its id is
negative so it can never collide with a real deck.
"""
from dataclasses import dataclass
from enum import Enum

from archetype_classifier.data_loading.dataset import CardCount
from archetype_classifier.evaluation.model import PredictDeck, sorted_lines

HAND_MADE_ID = -1


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
