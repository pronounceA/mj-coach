"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { analysisApi } from "@/lib/api"
import { GameStateInput, DiscardCandidate, AnalysisHistoryEntry, PushFoldResult } from "@/types/analysis"
import { cn } from "@/lib/utils"

interface AnalysisState {
  gameState: GameStateInput
  candidates: DiscardCandidate[]
}

const ROUND_WIND_LABEL: Record<string, string> = { E: "東", S: "南" }
const SEAT_LABELS = ["東", "南", "西", "北"]

function formatPct(n: number): string {
  return (n * 100).toFixed(1) + "%"
}

function formatEv(n: number): string {
  return Math.round(n).toLocaleString("ja-JP")
}

export default function ResultPage() {
  const [state, setState] = useState<AnalysisState | null>(null)
  const [pushFoldResult, setPushFoldResult] = useState<PushFoldResult | null>(null)
  const [pushFoldLoading, setPushFoldLoading] = useState(false)
  const [historySaved, setHistorySaved] = useState(false)

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
  const dealerLabel = SEAT_LABELS[gameState.dealer] ?? String(gameState.dealer)
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
          <div>
            <dt className="text-gray-500">供託</dt>
            <dd className="font-semibold">{gameState.riichi_sticks}本</dd>
          </div>
          <div>
            <dt className="text-gray-500">親</dt>
            <dd className="font-semibold">{dealerLabel}家</dd>
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
                    <span className="font-mono font-bold text-gray-900">{c.discard}</span>
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
