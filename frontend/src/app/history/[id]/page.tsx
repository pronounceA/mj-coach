"use client"

import { Suspense, useEffect, useState } from "react"
import { useParams } from "next/navigation"
import Link from "next/link"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { AnalysisHistoryEntry, DiscardCandidate } from "@/types/analysis"
import { cn } from "@/lib/utils"

const ROUND_WIND_LABEL: Record<string, string> = { E: "東", S: "南" }
const SEAT_LABELS = ["東", "南", "西", "北"]

function formatPct(n: number): string {
  return (n * 100).toFixed(1) + "%"
}

function formatEv(n: number): string {
  return Math.round(n).toLocaleString("ja-JP")
}

function formatTimestamp(iso: string): string {
  const d = new Date(iso)
  const y = d.getFullYear()
  const mo = String(d.getMonth() + 1).padStart(2, "0")
  const day = String(d.getDate()).padStart(2, "0")
  const h = String(d.getHours()).padStart(2, "0")
  const mi = String(d.getMinutes()).padStart(2, "0")
  const s = String(d.getSeconds()).padStart(2, "0")
  return `${y}/${mo}/${day} ${h}:${mi}:${s}`
}

function HistoryDetailPageInner() {
  const params = useParams()
  const id = params?.id

  const [entry, setEntry] = useState<AnalysisHistoryEntry | null>(null)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (id == null) return
    try {
      const raw = localStorage.getItem("analysis_history")
      if (raw) {
        const history: AnalysisHistoryEntry[] = JSON.parse(raw)
        const index = parseInt(String(id), 10)
        if (!isNaN(index) && index >= 0 && index < history.length) {
          setEntry(history[index])
        }
      }
    } catch {
      // ignore
    }
    setLoaded(true)
  }, [id])

  if (!loaded) return null

  if (!entry) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b border-gray-200 shadow-sm">
          <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-6">
            <h1 className="text-lg font-bold text-gray-900">局面分析</h1>
          </div>
        </header>
        <main className="max-w-4xl mx-auto w-full px-4 py-6">
          <div className="flex flex-col items-center justify-center gap-4 py-20 text-center">
            <p className="text-gray-500">履歴データが見つかりません。</p>
            <Link href="/history">
              <Button variant="secondary">履歴一覧へ</Button>
            </Link>
          </div>
        </main>
      </div>
    )
  }

  const { game_state: gs, candidates: rawCandidates, timestamp } = entry
  const candidates: DiscardCandidate[] = [...rawCandidates].sort(
    (a, b) => b.round_ev - a.round_ev
  )

  const roundLabel = `${ROUND_WIND_LABEL[gs.round_wind] ?? gs.round_wind}${gs.hand_number}局`
  const honbaLabel = gs.honba > 0 ? ` ${gs.honba}本場` : ""
  const dealerLabel = SEAT_LABELS[gs.dealer] ?? String(gs.dealer)
  const seatLabel = SEAT_LABELS[gs.player_seat] ?? String(gs.player_seat)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-6">
          <h1 className="text-lg font-bold text-gray-900">局面分析</h1>
          <nav className="flex gap-4">
            <Link
              href="/analysis"
              className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
            >
              局面入力
            </Link>
            <Link
              href="/history"
              className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
            >
              履歴
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto w-full px-4 py-6 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">分析結果 (履歴)</h2>
            <p className="text-sm text-gray-500 mt-0.5">{formatTimestamp(timestamp)}</p>
          </div>
          <Link href="/history">
            <Button variant="secondary">一覧へ戻る</Button>
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
              <dd className="font-semibold">{gs.riichi_sticks}本</dd>
            </div>
            <div>
              <dt className="text-gray-500">親</dt>
              <dd className="font-semibold">{dealerLabel}家</dd>
            </div>
            <div>
              <dt className="text-gray-500">自席</dt>
              <dd className="font-semibold">{seatLabel}家</dd>
            </div>
            {gs.scores.map((s, i) => (
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
                    <td className="px-3 py-2 text-center">
                      {Math.round(c.expected_cost).toLocaleString("ja-JP")}
                    </td>
                    <td className="px-3 py-2 text-center">{formatPct(c.win_probability)}</td>
                    <td className="px-3 py-2 text-center">{formatPct(c.deal_in_probability)}</td>
                    <td
                      className={cn(
                        "px-3 py-2 text-center font-semibold",
                        c.round_ev > 0
                          ? "text-green-700"
                          : c.round_ev < 0
                          ? "text-red-700"
                          : "text-gray-700"
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
      </main>
    </div>
  )
}

export default function HistoryDetailPage() {
  return (
    <Suspense>
      <HistoryDetailPageInner />
    </Suspense>
  )
}
