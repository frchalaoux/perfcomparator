from perfcomparator.apple_models import apple_model_year


def test_known_apple_model_identifier_has_commercial_year() -> None:
    assert apple_model_year("MacBookPro18,3") == 2021


def test_reused_identifier_needs_sku_to_determine_year() -> None:
    assert apple_model_year("MacBookPro15,1") is None
    assert apple_model_year("MacBookPro15,1", "MR942FN/A") == 2018
    assert apple_model_year("MacBookPro15,1", "MV902FN/A") == 2019


def test_unknown_apple_model_identifier_has_no_guessed_year() -> None:
    assert apple_model_year("Mac99,99") is None
