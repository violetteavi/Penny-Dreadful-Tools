import hashlib

from archetype_classifier.data_loading.splits import Split, SplitScheme, assign_split

DEFAULT = SplitScheme('default')
A_HASH = 'a' * 40


def test_seasons_map_to_splits() -> None:
    assert assign_split(1, A_HASH, DEFAULT) in {Split.TRAIN, Split.HELD_OUT}
    assert assign_split(39, A_HASH, DEFAULT) == Split.VALIDATION
    assert assign_split(40, A_HASH, DEFAULT) == Split.TEST
    assert assign_split(42, A_HASH, DEFAULT) == Split.TEST

def fake_hash(i: int) -> str:
    return hashlib.sha1(str(i).encode()).hexdigest()

def test_about_ten_percent_of_training_hashes_are_held_out_in_any_training_season() -> None:
    early = [assign_split(5, fake_hash(i), DEFAULT) for i in range(5000)]
    late = [assign_split(38, fake_hash(i), DEFAULT) for i in range(5000)]
    assert early == late
    assert 9 <= 100 * early.count(Split.HELD_OUT) / 5000 <= 11

def test_seasons_outside_the_scheme_get_no_split() -> None:
    assert assign_split(43, A_HASH, DEFAULT) is None
