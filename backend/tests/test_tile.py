import pytest
from mahjong_engine.domain.tile import Suit, TileType, TileVariant, PhysicalTile


def test_tile_type_str():
    assert str(TileType(suit=Suit.MAN, rank=1)) == "1m"
    assert str(TileType(suit=Suit.PIN, rank=5)) == "5p"
    assert str(TileType(suit=Suit.SOU, rank=9)) == "9s"


def test_tile_type_invalid_rank():
    with pytest.raises(ValueError):
        TileType(suit=Suit.MAN, rank=0)
    with pytest.raises(ValueError):
        TileType(suit=Suit.MAN, rank=10)
    with pytest.raises(ValueError):
        TileType(suit=Suit.HONOR, rank=8)


def test_physical_tile_variants():
    tile_type = TileType(suit=Suit.PIN, rank=5)
    normal = PhysicalTile(tile_type=tile_type, variant=TileVariant.NORMAL)
    red = PhysicalTile(tile_type=tile_type, variant=TileVariant.RED)
    blue = PhysicalTile(tile_type=tile_type, variant=TileVariant.BLUE)

    assert not normal.is_red()
    assert not normal.is_blue()
    assert red.is_red()
    assert not red.is_blue()
    assert blue.is_blue()
    assert not blue.is_red()


def test_physical_tile_str():
    tile_type = TileType(suit=Suit.SOU, rank=5)
    assert str(PhysicalTile(tile_type=tile_type)) == "5s"
    assert str(PhysicalTile(tile_type=tile_type, variant=TileVariant.RED)) == "r5s"
    assert str(PhysicalTile(tile_type=tile_type, variant=TileVariant.BLUE)) == "b5s"
