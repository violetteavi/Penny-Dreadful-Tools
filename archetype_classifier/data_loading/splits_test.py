import hashlib

from archetype_classifier.data_loading.labels import LabelStatus
from archetype_classifier.data_loading.splits import ExclusionReason, Split, SplitDecision, SplitScheme, assign_split

DEFAULT = SplitScheme('default')
A_HASH = 'a' * 40
KEPT_HASH = 'b6589fc6ab0dc82cf12099d1c2d40ab994e8410c'  # Falls outside the held-out 10% with no salt.
HELD_OUT_HASH = 'ca3512f4dfa95a03169c5a670a4c91a19b3077b4'  # Falls inside it.
TYPICAL = SplitScheme('typical')  # Seasons 1-38 / 39 / 40-42 with 10% held out; train and eval {VERIFIED}; twins off.


def split(season_id: int, status: LabelStatus, maindeck_hash: str | None = KEPT_HASH, maindeck_cards: int = 60, scheme: SplitScheme = TYPICAL) -> SplitDecision:
    return assign_split(deck_id=1, season_id=season_id, maindeck_hash=maindeck_hash, maindeck_cards=maindeck_cards, status=status, scheme=scheme)


# Scenario: a deck's split follows its role and its status (Scenarios.md, "Splitting decks").

def test_a_verified_deck_from_a_training_season_is_trained_on() -> None:
    assert split(30, LabelStatus.VERIFIED) == SplitDecision(Split.TRAIN, None)

def test_a_training_season_deck_whose_status_isnt_trained_on_is_excluded() -> None:
    assert split(30, LabelStatus.UNVERIFIED) == SplitDecision(Split.EXCLUDED, ExclusionReason.STATUS_NOT_TRAINED_ON)
    assert split(30, LabelStatus.UNLABELLED) == SplitDecision(Split.EXCLUDED, ExclusionReason.STATUS_NOT_TRAINED_ON)

def test_a_held_out_deck_is_scored_only_if_its_status_is_evaluated() -> None:
    assert split(30, LabelStatus.VERIFIED, HELD_OUT_HASH) == SplitDecision(Split.HELD_OUT, None)
    assert split(30, LabelStatus.UNVERIFIED, HELD_OUT_HASH) == SplitDecision(Split.EXCLUDED, ExclusionReason.STATUS_NOT_EVALUATED)


def test_seasons_map_to_splits() -> None:
    assert split(1, LabelStatus.VERIFIED, A_HASH, scheme=DEFAULT).split in {Split.TRAIN, Split.HELD_OUT}
    assert split(39, LabelStatus.VERIFIED, A_HASH, scheme=DEFAULT).split == Split.VALIDATION
    assert split(40, LabelStatus.VERIFIED, A_HASH, scheme=DEFAULT).split == Split.TEST
    assert split(42, LabelStatus.VERIFIED, A_HASH, scheme=DEFAULT).split == Split.TEST

def fake_hash(i: int) -> str:
    return hashlib.sha1(str(i).encode()).hexdigest()

def test_about_ten_percent_of_training_hashes_are_held_out_in_any_training_season() -> None:
    early = [split(5, LabelStatus.VERIFIED, fake_hash(i), scheme=DEFAULT).split for i in range(5000)]
    late = [split(38, LabelStatus.VERIFIED, fake_hash(i), scheme=DEFAULT).split for i in range(5000)]
    assert early == late
    assert 9 <= 100 * early.count(Split.HELD_OUT) / 5000 <= 11

def test_a_salt_reshuffles_the_held_out_hashes() -> None:
    unsalted = [split(20, LabelStatus.VERIFIED, fake_hash(i), scheme=DEFAULT).split for i in range(5000)]
    explicitly_unsalted = [split(20, LabelStatus.VERIFIED, fake_hash(i), scheme=SplitScheme('same', salt='')).split for i in range(5000)]
    salted = [split(20, LabelStatus.VERIFIED, fake_hash(i), scheme=SplitScheme('salted', salt='2')).split for i in range(5000)]
    assert unsalted == explicitly_unsalted
    assert unsalted != salted

def test_a_scheme_survives_being_stored_as_params() -> None:
    scheme = SplitScheme('custom', train_seasons=frozenset({1, 2}), validation_seasons=frozenset({3}), test_seasons=frozenset({4, 5}), held_out_percent=20, salt='x')
    assert SplitScheme.from_params('custom', scheme.to_params()) == scheme

def test_a_scheme_stored_before_a_parameter_existed_gets_its_default() -> None:
    assert SplitScheme.from_params('old', {'test_seasons': [40, 41, 42]}) == SplitScheme('old')

def test_seasons_outside_the_scheme_are_excluded_as_reserved() -> None:
    assert split(43, LabelStatus.VERIFIED, A_HASH, scheme=DEFAULT) == SplitDecision(Split.EXCLUDED, ExclusionReason.RESERVED_SEASON)
