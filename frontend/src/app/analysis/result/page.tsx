"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { analysisApi } from "@/lib/api"
import {
  GameStateInput,
  DiscardCandidate,
  AnalysisHistoryEntry,
  PushFoldResult,
  MatchEvResult,
  OpponentModelType,
} from "@/types/analysis"
import { cn } from "@/lib/utils"

interface AnalysisState {
  gameState: GameStateInput
  candidates: DiscardCandidate[]
}

const ROUND_WIND_LABEL: Record<string, string> = { E: "東", S: "南" }
const SEAT_LABELS = ["東", "南", "西", "北"]
const HONOR_LABELS = ["東", "南", "西", "北", "白", "發", "中"]

function formatTile(discard: string): string {
  if (discard.endsWith("z")) {
    const rank = parseInt(discard, 10)
    if (rank >= 1 && rank <= 7) return HONOR_LABELS[rank - 1]
  }
  return discard
}

function formatPct(n: number): string {
  return (n * 100).toFixed(1) + "%"
}

function formatEv(n: number): string {
  return Math.round(n).toLocaleString("ja-JP")
}

const OPPONENT_LABELS: Record<OpponentModelType, string> = {
  random: "ランダム",
  basic: "標準",
  aggressive: "攻撃的",
  defensive: "守備的",
}

function PlacementBar({ label, pct, color }: { label: string; pct: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-6 text-gray-600 font-medium shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
        <div
          className={cn("h-full rounded-full flex items-center justify-end pr-1.5", color)}
          style={{ width: `${Math.max(pct * 100, 1)}%` }}
        >
          <span className="text-white text-[10px] font-bold leading-none">
            {(pct * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  )
}

export default function ResultPage() {
  const [state, setState] = useState<AnalysisState | null>(null)
  const [pushFoldResult, setPushFoldResult] = useState<PushFoldResult | null>(null)
  const [pushFoldLoading, setPushFoldLoading] = useState(false)
  const [historySaved, setHistorySaved] = useState(false)
  const [matchEvResult, setMatchEvResult] = useState<MatchEvResult | null>(null)
  const [matchEvLoading, setMatchEvLoading] = useState(false)
  const [matchEvDiscard, setMatchEvDiscard] = useState<string | null>(null)
  const [opponentModel, setOpponentModel] = useState<OpponentModelType>("basic")

  useEffect(() => {
    const raw = sessionStorage.getItem("analysis_state")
    if (!raw) return
    try {
      const parsed: AnalysisState = JSON.parse(raw)
      // Sort by round_ev desc
      const sorted = [...parsed.candidates].sort((a, b) => b.round_ev - a.round_ev)
      setState({ ...parsed, candidates: sorted })
    } catch {
      // ignore parse error
    }
  }, [])

  useEffect(() => {
    if (!state || state.candidates.length === 0) return
    handleMatchEv(state.candidates[0], opponentModel)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state])

  useEffect(() => {
    if (!state || historySaved) return
    const entry: AnalysisHistoryEntry = {
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      game_state: state.gameState,
      candidates: state.candidates,
    }
    try {
      const history = JSON.parse(localStorage.getItem("analysis_history") || "[]")
      history.unshift(entry)
      localStorage.setItem("analysis_history", JSON.stringify(history.slice(0, 50)))
      setHistorySaved(true)
    } catch {
      // ignore storage errors
    }
  }, [state, historySaved])

  async function handleMatchEv(candidate: DiscardCandidate, model: OpponentModelType) {
    if (!state) return
    const suit = candidate.discard.slice(-1) as "m" | "p" | "s" | "z"
    const rank = parseInt(candidate.discard.replace(/[^0-9]/g, ""), 10)
    const tile =
      state.gameState.hand.find((t) => t.suit === suit && t.rank === rank) ??
      (state.gameState.drawn_tile?.suit === suit && state.gameState.drawn_tile?.rank === rank
        ? state.gameState.drawn_tile
        : null)
    if (!tile) return

    setMatchEvLoading(true)
    setMatchEvDiscard(candidate.discard)
    setMatchEvResult(null)
    try {
      const result = await analysisApi.matchEv({
        game_state: state.gameState,
        discard: tile,
        opponent_models: [model, model, model],
        n_simulations: 2000,
      })
      setMatchEvResult(result)
    } catch {
      // ignore errors
    } finally {
      setMatchEvLoading(false)
    }
  }

  async function handlePushFold() {
    if (!state || state.candidates.length < 2) return
    const top = state.candidates[0]
    const second = state.candidates[1]

    // Find the actual tile objects from the hand that match the discard string
    // discard is like "1m", "5z", etc. — match by tile key
    function findTile(discardStr: string) {
      const suit = discardStr.slice(-1) as "m" | "p" | "s" | "z"
      const rank = parseInt(discardStr.slice(0, -1), 10)
      return (
        state.gameState.hand.find((t) => t.suit === suit && t.rank === rank) ??
        (state.gameState.drawn_tile?.suit === suit && state.gameState.drawn_tile?.rank === rank
          ? state.gameState.drawn_tile
          : null)
      )
    }

    const pushTile = findTile(top.discard)
    const foldTile = findTile(second.discard)
    if (!pushTile || !foldTile) return

    setPushFoldLoading(true)
    try {
      const result = await analysisApi.pushFold(state.gameState, pushTile, foldTile)
      setPushFoldResult(result)
    } catch {
      // ignore push-fold errors silently
    } finally {
      setPushFoldLoading(false)
    }
  }

  if (!state) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
        <p className="text-gray-500">分析データがありません。</p>
        <Link href="/analysis">
          <Button variant="primary">局面入力へ</Button>
        </Link>
      </div>
    )
  }

  const { gameState, candidates } = state
  const top = candidates[0]
  const showPushFold = top && top.deal_in_probability > 0.05

  const roundLabel = `${ROUND_WIND_LABEL[gameState.round_wind] ?? gameState.round_wind}${gameState.hand_number}局`
  const honbaLabel = gameState.honba > 0 ? ` ${gameState.honba}本場` : ""
  const seatLabel = SEAT_LABELS[gameState.player_seat] ?? String(gameState.player_seat)

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">分析結果</h2>
        <Link href="/analysis">
          <Button variant="secondary">再入力</Button>
        </Link>
      </div>

      {/* Game state summary */}
      <Card title="局面サマリー">
        <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
          <div>
            <dt className="text-gray-500">局</dt>
            <dd className="font-semibold">{roundLabel}{honbaLabel}</dd>
          </div>
          {gameState.junme != null && (
            <div>
              <dt className="text-gray-500">巡目</dt>
              <dd className="font-semibold">{gameState.junme}巡目</dd>
            </div>
          )}
          <div>
            <dt className="text-gray-500">供託</dt>
            <dd className="font-semibold">{gameState.riichi_sticks}本</dd>
          </div>
          <div>
            <dt className="text-gray-500">自席</dt>
            <dd className="font-semibold">{seatLabel}家</dd>
          </div>
          {gameState.scores.map((s, i) => (
            <div key={i}>
              <dt className="text-gray-500">{SEAT_LABELS[i]}家点棒</dt>
              <dd className="font-semibold">{s.toLocaleString("ja-JP")}</dd>
            </div>
          ))}
        </dl>
      </Card>

      {/* Discard candidates table */}
      <Card title="打牌候補">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-gray-50 text-gray-600 text-left">
                <th className="px-3 py-2 font-medium border-b border-gray-200">打牌</th>
                <th className="px-3 py-2 font-medium border-b border-gray-200">シャンテン</th>
                <th className="px-3 py-2 font-medium border-b border-gray-200">受け入れ枚数</th>
                <th className="px-3 py-2 font-medium border-b border-gray-200">期待翻数</th>
                <th className="px-3 py-2 font-medium border-b border-gray-200">期待点数</th>
                <th className="px-3 py-2 font-medium border-b border-gray-200">和了確率</th>
                <th className="px-3 py-2 font-medium border-b border-gray-200">放銃確率</th>
                <th className="px-3 py-2 font-medium border-b border-gray-200">期待値</th>
              </tr>
            </thead>
            <tbody>
              {candidates.map((c, i) => (
                <tr
                  key={`${c.discard}-${i}`}
                  className={cn(
                    "border-b border-gray-100 hover:bg-gray-50 transition-colors",
                    i === 0 && "bg-blue-50 font-semibold"
                  )}
                >
                  <td className="px-3 py-2">
                    <span className="font-mono font-bold text-gray-900">{formatTile(c.discard)}</span>
                    {i === 0 && (
                      <span className="ml-2 text-xs text-blue-600 font-normal">推奨</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">{c.shanten}</td>
                  <td className="px-3 py-2 text-center">{c.total_ukeire}</td>
                  <td className="px-3 py-2 text-center">{c.expected_han.toFixed(1)}</td>
                  <td className="px-3 py-2 text-center">{Math.round(c.expected_cost).toLocaleString("ja-JP")}</td>
                  <td className="px-3 py-2 text-center">{formatPct(c.win_probability)}</td>
                  <td className="px-3 py-2 text-center">{formatPct(c.deal_in_probability)}</td>
                  <td
                    className={cn(
                      "px-3 py-2 text-center font-semibold",
                      c.round_ev > 0 ? "text-green-700" : c.round_ev < 0 ? "text-red-700" : "text-gray-700"
                    )}
                  >
                    {formatEv(c.round_ev)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Match EV simulation section */}
      <Card title="半荘シミュレーション">
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm text-gray-600 shrink-0">対戦相手レベル:</span>
            {(["random", "basic", "aggressive", "defensive"] as OpponentModelType[]).map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setOpponentModel(m)}
                className={cn(
                  "px-3 py-1 text-xs rounded-full border transition-colors cursor-pointer",
                  opponentModel === m
                    ? "bg-blue-600 border-blue-600 text-white"
                    : "bg-white border-gray-300 text-gray-600 hover:border-blue-400"
                )}
              >
                {OPPONENT_LABELS[m]}
              </button>
            ))}
            <div className="flex gap-2 ml-auto">
              {candidates.slice(0, 5).map((c, i) => (
                <button
                  key={`${c.discard}-${i}`}
                  type="button"
                  onClick={() => handleMatchEv(c, opponentModel)}
                  className={cn(
                    "px-2 py-1 text-xs rounded border transition-colors cursor-pointer font-mono",
                    matchEvDiscard === c.discard
                      ? "bg-blue-100 border-blue-400 text-blue-800"
                      : "bg-white border-gray-300 text-gray-600 hover:border-blue-400"
                  )}
                >
                  {formatTile(c.discard)}
                </button>
              ))}
            </div>
          </div>

          {matchEvLoading && (
            <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
              <span className="animate-spin text-blue-500">⟳</span>
              シミュレーション中… ({matchEvDiscard ? formatTile(matchEvDiscard) : ""} を分析)
            </div>
          )}

          {!matchEvLoading && matchEvResult && (
            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap gap-6 text-sm">
                <div>
                  <span className="text-gray-500">対象打牌: </span>
                  <span className="font-mono font-bold text-gray-900">{matchEvDiscard ? formatTile(matchEvDiscard) : ""}</span>
                </div>
                <div>
                  <span className="text-gray-500">平均順位: </span>
                  <span className="font-semibold">{matchEvResult.mean_placement.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-500">期待精算点: </span>
                  <span className={cn("font-semibold", matchEvResult.mean_final_score >= 0 ? "text-green-700" : "text-red-700")}>
                    {Math.round(matchEvResult.mean_final_score).toLocaleString("ja-JP")}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500">95%CI: </span>
                  <span className="font-semibold text-gray-700">
                    [{Math.round(matchEvResult.ci_low_95).toLocaleString("ja-JP")},&nbsp;
                    {Math.round(matchEvResult.ci_high_95).toLocaleString("ja-JP")}]
                  </span>
                </div>
                <div className="text-gray-400 text-xs self-end">
                  ({matchEvResult.simulation_count}回試行)
                </div>
              </div>

              <div className="flex flex-col gap-2">
                <PlacementBar label="1位" pct={matchEvResult.placement_distribution.first}  color="bg-blue-500" />
                <PlacementBar label="2位" pct={matchEvResult.placement_distribution.second} color="bg-green-500" />
                <PlacementBar label="3位" pct={matchEvResult.placement_distribution.third}  color="bg-yellow-500" />
                <PlacementBar label="4位" pct={matchEvResult.placement_distribution.fourth} color="bg-red-400" />
              </div>
            </div>
          )}

          {!matchEvLoading && !matchEvResult && (
            <p className="text-sm text-gray-400 py-2">データを読み込んでいます…</p>
          )}
        </div>
      </Card>

      {/* Push-fold section */}
      {showPushFold && (
        <Card title="押し引き分析">
          {!pushFoldResult ? (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-gray-600">
                トップ候補の放銃確率が {formatPct(top.deal_in_probability)} です。
                押し引き分析を実行しますか？
              </p>
              <div>
                <Button
                  type="button"
                  variant="secondary"
                  loading={pushFoldLoading}
                  onClick={handlePushFold}
                >
                  押し引き分析を実行
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <span
                  className={cn(
                    "text-lg font-bold px-3 py-1 rounded",
                    pushFoldResult.recommendation === "push"
                      ? "bg-green-100 text-green-800"
                      : "bg-red-100 text-red-800"
                  )}
                >
                  {pushFoldResult.recommendation === "push" ? "押し推奨" : "オリ推奨"}
                </span>
                <span className="text-sm text-gray-500">
                  EV差: {formatEv(pushFoldResult.ev_diff)}
                </span>
              </div>
              <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
                <div>
                  <dt className="text-gray-500">押し時期待値</dt>
                  <dd className={cn("font-semibold", pushFoldResult.push_ev > 0 ? "text-green-700" : "text-red-700")}>
                    {formatEv(pushFoldResult.push_ev)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">オリ時期待値</dt>
                  <dd className={cn("font-semibold", pushFoldResult.fold_ev > 0 ? "text-green-700" : "text-red-700")}>
                    {formatEv(pushFoldResult.fold_ev)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500">押し時和了確率</dt>
                  <dd className="font-semibold">{formatPct(pushFoldResult.push_win_probability)}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">押し時放銃確率</dt>
                  <dd className="font-semibold text-red-600">{formatPct(pushFoldResult.push_deal_in_probability)}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">オリ時放銃確率</dt>
                  <dd className="font-semibold">{formatPct(pushFoldResult.fold_deal_in_probability)}</dd>
                </div>
              </dl>
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
