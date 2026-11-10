from __future__ import annotations

import random
from dataclasses import dataclass

from mahjong_engine.simulation.opponent_model import OpponentStats


@dataclass
class RoundOutcome:
    winner_seat: int | None
    score_changes: list[int]
    next_dealer: int
    next_honba: int
    next_riichi_sticks: int


def simulate_round(
    player_seat: int,
    p_win: float,
    expected_win_score: int,
    p_deal_in: float,
    opp_stats: list[OpponentStats],
    dealer: int,
    honba: int,
    riichi_sticks: int,
    rng: random.Random,
) -> RoundOutcome:
    """1局の結果をサンプリングする。

    Returns:
        RoundOutcome — スコア変化と次局の局面情報
    """
    n = 4
    opp_seats = [i for i in range(n) if i != player_seat]

    # 相手統計を3要素に正規化
    stats: list[OpponentStats] = (opp_stats + [opp_stats[-1]] * 3)[:3]

    honba_bonus = honba * 300
    riichi_bonus = riichi_sticks * 1000

    score_changes = [0] * n
    r = rng.random()

    if r < p_win:
        # ---- 自家和了 ----
        total = expected_win_score + honba_bonus + riichi_bonus
        per_opp = total // 3
        for s in opp_seats:
            score_changes[s] = -per_opp
        score_changes[player_seat] = per_opp * 3

        winner_seat = player_seat
        if player_seat == dealer:
            next_dealer, next_honba = dealer, honba + 1
        else:
            next_dealer, next_honba = (dealer + 1) % n, 0
        next_riichi = 0

    elif r < p_win + p_deal_in:
        # ---- 自家放銃 ----
        idx = rng.randrange(3)
        winner_seat = opp_seats[idx]
        payment = stats[idx].avg_win_score + honba_bonus + riichi_bonus
        score_changes[player_seat] = -payment
        score_changes[winner_seat] = payment

        if winner_seat == dealer:
            next_dealer, next_honba = dealer, honba + 1
        else:
            next_dealer, next_honba = (dealer + 1) % n, 0
        next_riichi = 0

    else:
        # ---- 対戦相手間 or 流局 ----
        opp_total_rate = sum(s.win_rate for s in stats)
        p_opp = min(0.55, opp_total_rate * 0.55)

        if rng.random() < p_opp:
            # 対戦相手の一人がツモ和了
            idx = rng.randrange(3)
            winner_seat = opp_seats[idx]
            win_score = stats[idx].avg_win_score + honba_bonus + riichi_bonus
            per_payer = win_score // 3
            for i in range(n):
                score_changes[i] = -per_payer
            score_changes[winner_seat] = per_payer * 3

            if winner_seat == dealer:
                next_dealer, next_honba = dealer, honba + 1
            else:
                next_dealer, next_honba = (dealer + 1) % n, 0
            next_riichi = 0
        else:
            # 流局: 本場加算、供託スティックは持ち越し
            winner_seat = None
            next_dealer, next_honba = dealer, honba + 1
            next_riichi = riichi_sticks

    return RoundOutcome(
        winner_seat=winner_seat,
        score_changes=score_changes,
        next_dealer=next_dealer,
        next_honba=next_honba,
        next_riichi_sticks=next_riichi,
    )
