from src.prepare_data import prepare_data


def test_prepare_data_trims_and_drops_empty_values():
    assert prepare_data(["  freshcart ", "", "  ", 42]) == ["freshcart", "42"]


def test_prepare_data_accepts_generators():
    assert prepare_data(value for value in [" a ", "b "]) == ["a", "b"]

