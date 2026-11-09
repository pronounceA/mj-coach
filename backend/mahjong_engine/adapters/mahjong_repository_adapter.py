from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
from mahjong.meld import Meld as LibMeld
from mahjong.tile import TilesConverter

from mahjong_engine.adapters.base import MahjongEngineAdapter
from mahjong_engine.domain.meld import Meld, MeldType
from mahjong_engine.domain.tile import PhysicalTile, Suit, TileType


def _tile_type_to_136(tile_type: TileType) -> int:
    """TileType を mahjong ライブラリの136形式インデックスに変換する。"""
    suit_offset = {Suit.MAN: 0, Suit.PIN: 36, Suit.SOU: 72, Suit.HONOR: 108}
    return suit_offset[tile_type.suit] + (tile_type.rank - 1) * 4


def _hand_to_34(tiles: list[PhysicalTile]) -> list[int]:
    """手牌を34形式（牌種ごとの枚数配列）に変換する。"""
    counts = [0] * 34
    for tile in tiles:
        idx = _tile_type_to_136(tile.tile_type) // 4
        counts[idx] += 1
    return counts


def _hand_to_136(tiles: list[PhysicalTile]) -> list[int]:
    """手牌を136形式（物理牌インデックスのリスト）に変換する。
    同じ牌種が複数ある場合は +1 ずつずらして重複を避ける。
    """
    counts: dict[int, int] = {}
    result = []
    for tile in tiles:
        base = _tile_type_to_136(tile.tile_type)
        offset = counts.get(base, 0)
        counts[base] = offset + 1
        result.append(base + offset)
    return result


class MahjongRepositoryAdapter(MahjongEngineAdapter):
    def __init__(self) -> None:
        self._calculator = HandCalculator()

    def calculate_shanten(
        self, hand: list[PhysicalTile], melds: list[Meld]
    ) -> int:
        from mahjong.shanten import Shanten
        shanten = Shanten()
        tiles_34 = _hand_to_34(hand)
        return shanten.calculate_shanten(tiles_34)

    def calculate_ukeire(
        self, hand: list[PhysicalTile], melds: list[Meld], remaining: dict
    ) -> list[dict]:
        from mahjong.shanten import Shanten
        shanten_calc = Shanten()
        tiles_34 = _hand_to_34(hand)
        current_shanten = shanten_calc.calculate_shanten(tiles_34)

        ukeire = []
        for suit in [Suit.MAN, Suit.PIN, Suit.SOU]:
            max_rank = 9
            for rank in range(1, max_rank + 1):
                tile_type = TileType(suit=suit, rank=rank)
                remaining_count = remaining.get(str(tile_type), 0)
                if remaining_count <= 0:
                    continue
                idx = _tile_type_to_136(tile_type) // 4
                tiles_34[idx] += 1
                new_shanten = shanten_calc.calculate_shanten(tiles_34)
                tiles_34[idx] -= 1
                if new_shanten < current_shanten:
                    ukeire.append({
                        "tile_type": str(tile_type),
                        "remaining_count": remaining_count,
                    })
        return ukeire

    def calculate_score(
        self,
        hand: list[PhysicalTile],
        win_tile: PhysicalTile,
        melds: list[Meld],
        context: dict,
    ) -> dict:
        tiles_136 = _hand_to_136(hand + [win_tile])
        win_tile_136 = tiles_136[-1]

        lib_melds = []
        for meld in melds:
            meld_tiles = _hand_to_136(list(meld.tiles))
            if meld.meld_type == MeldType.CHI:
                lib_melds.append(LibMeld(meld_type=LibMeld.CHI, tiles=meld_tiles))
            elif meld.meld_type == MeldType.PON:
                lib_melds.append(LibMeld(meld_type=LibMeld.PON, tiles=meld_tiles))
            elif meld.meld_type in (MeldType.KAN_OPEN, MeldType.KAN_ADDED):
                lib_melds.append(LibMeld(meld_type=LibMeld.KAN, tiles=meld_tiles, opened=True))
            elif meld.meld_type == MeldType.KAN_CLOSED:
                lib_melds.append(LibMeld(meld_type=LibMeld.KAN, tiles=meld_tiles, opened=False))

        dora_indicators_136 = [
            _tile_type_to_136(TileType(suit=d["suit"], rank=d["rank"]))
            for d in context.get("dora_indicators", [])
        ]

        config = HandConfig(
            is_tsumo=context.get("is_tsumo", False),
            is_riichi=context.get("is_riichi", False),
            player_wind=context.get("player_wind"),
            round_wind=context.get("round_wind"),
            options=OptionalRules(
                has_aka_dora=True,
                aka_dora_count=context.get("aka_dora_count", 0),
            ),
        )

        result = self._calculator.estimate_hand_value(
            tiles=tiles_136,
            win_tile=win_tile_136,
            melds=lib_melds or None,
            dora_indicators=dora_indicators_136 or None,
            config=config,
        )

        if result.error:
            return {"error": result.error}

        return {
            "han": result.han,
            "fu": result.fu,
            "cost": result.cost,
            "yaku": [{"name": y.name, "han": y.han_closed} for y in (result.yaku or [])],
        }
