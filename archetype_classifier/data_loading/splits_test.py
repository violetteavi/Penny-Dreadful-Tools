from archetype_classifier.data_loading.splits import Split, SplitScheme, assign_split

DEFAULT = SplitScheme('default')
A_HASH = 'a' * 40


def test_seasons_map_to_splits() -> None:
    assert assign_split(1, A_HASH, DEFAULT) in {Split.TRAIN, Split.HELD_OUT}
    assert assign_split(39, A_HASH, DEFAULT) == Split.VALIDATION
    assert assign_split(40, A_HASH, DEFAULT) == Split.TEST
    assert assign_split(42, A_HASH, DEFAULT) == Split.TEST

def test_seasons_outside_the_scheme_get_no_split() -> None:
    assert assign_split(43, A_HASH, DEFAULT) is None
