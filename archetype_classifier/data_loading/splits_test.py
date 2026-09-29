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

def test_a_salt_reshuffles_the_held_out_hashes() -> None:
    unsalted = [assign_split(20, fake_hash(i), DEFAULT) for i in range(5000)]
    explicitly_unsalted = [assign_split(20, fake_hash(i), SplitScheme('same', salt='')) for i in range(5000)]
    salted = [assign_split(20, fake_hash(i), SplitScheme('salted', salt='2')) for i in range(5000)]
    assert unsalted == explicitly_unsalted
    assert unsalted != salted

def test_a_scheme_survives_being_stored_as_params() -> None:
    scheme = SplitScheme('custom', train_seasons=frozenset({1, 2}), validation_seasons=frozenset({3}), test_seasons=frozenset({4, 5}), held_out_percent=20, salt='x')
    assert SplitScheme.from_params('custom', scheme.to_params()) == scheme

def test_a_scheme_stored_before_a_parameter_existed_gets_its_default() -> None:
    assert SplitScheme.from_params('old', {'test_seasons': [40, 41, 42]}) == SplitScheme('old')

def test_seasons_outside_the_scheme_get_no_split() -> None:
    assert assign_split(43, A_HASH, DEFAULT) is None
