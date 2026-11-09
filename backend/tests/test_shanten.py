import pytest
from mahjong_engine.adapters.mahjong_repository_adapter import MahjongRepositoryAdapter
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType, TileVariant
from mahjong_engine.efficiency.shanten_calculator import ShantenCalculator


def make_tile(suit: str, rank: int, variant: str = "normal") -> PhysicalTile:
    return PhysicalTile(
        tile_type=TileType(suit=Suit(suit), rank=rank),
        variant=TileVariant(variant),
    )


@pytest.fixture
def calc() -> ShantenCalculator:
    return ShantenCalculator(MahjongRepositoryAdapter())


def test_tenpai_shanten(calc):
    # 1m2m3m 4m5m6m 7m8m 1p1p 2s3s （テンパイ）
    hand = [
        make_tile("m", 1), make_tile("m", 2), make_tile("m", 3),
        make_tile("m", 4), make_tile("m", 5), make_tile("m", 6),
        make_tile("m", 7), make_tile("m", 8),
        make_tile("p", 1), make_tile("p", 1),
        make_tile("s", 2), make_tile("s", 3),
        make_tile("s", 5),
    ]
    assert calc.calculate(hand, []) == 0


def test_iishanten(calc):
    # 1m2m 4m5m 7m8m 1p2p 1s2s 3z3z3z （1シャンテン）
    hand = [
        make_tile("m", 1), make_tile("m", 2),
        make_tile("m", 4), make_tile("m", 5),
        make_tile("m", 7), make_tile("m", 8),
        make_tile("p", 1), make_tile("p", 2),
        make_tile("s", 1), make_tile("s", 2),
        make_tile("z", 3), make_tile("z", 3), make_tile("z", 3),
    ]
    assert calc.calculate(hand, []) == 1


def test_agari_shanten(calc):
    # 完成形：1m2m3m 4m5m6m 7m8m9m 1p1p 2s3s4s
    hand = [
        make_tile("m", 1), make_tile("m", 2), make_tile("m", 3),
        make_tile("m", 4), make_tile("m", 5), make_tile("m", 6),
        make_tile("m", 7), make_tile("m", 8), make_tile("m", 9),
        make_tile("p", 1), make_tile("p", 1),
        make_tile("s", 2), make_tile("s", 3), make_tile("s", 4),
    ]
    assert calc.calculate(hand, []) == -1
