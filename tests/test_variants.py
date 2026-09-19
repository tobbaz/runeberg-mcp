"""Unit tests for historical name and place spelling variant generator."""

from runeberg_mcp.search import generate_historical_variants


def test_place_suffix_hausen():
    variants = generate_historical_variants("Hilpershausen")
    assert "Hilperhaussen" in variants
    assert "Hilpershaussen" in variants
    assert "Hilpershusen" in variants


def test_noble_suffix_stierna():
    variants = generate_historical_variants("Ekenstierna")
    assert "Ekenstjerna" in variants

    variants_rev = generate_historical_variants("Ekenstjerna")
    assert "Ekenstierna" in variants_rev


def test_noble_suffix_hielm():
    variants = generate_historical_variants("Drakenhielm")
    assert "Drakenhjelm" in variants


def test_noble_suffix_skold():
    variants = generate_historical_variants("Natt och Dag")
    assert isinstance(variants, list)

    variants_skold = generate_historical_variants("Silfversköld")
    assert "Silfverskiöld" in variants_skold


def test_place_suffix_torp_borg_berg():
    assert "Normestorff" in generate_historical_variants("Normestorp")
    assert "Piiksborgh" in generate_historical_variants("Piiksborg")
    assert "Västerbergh" in generate_historical_variants("Västerberg")
    assert "Ströhm" in generate_historical_variants("Ström")


def test_first_names():
    carl_vars = generate_historical_variants("Carl Fredrik")
    assert "Karl Fredrik" in carl_vars
    assert "Carl Fredric" in carl_vars

    gustaf_vars = generate_historical_variants("Gustaf Adolf")
    assert "Gustav Adolf" in gustaf_vars
