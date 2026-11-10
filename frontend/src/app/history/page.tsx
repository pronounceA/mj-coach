"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card } from "@/components/ui/Card"
import { AnalysisHistoryEntry } from "@/types/analysis"

const ROUND_WIND_LABEL: Record<string, string> = { E: "東", S: "南" }
const SEAT_LABELS = ["東", "南", "西", "北"]

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
  return `${y}/${mo}/${day} ${h}:${mi}`
}

export default function HistoryPage() {
  const [history, setHistory] = useState<AnalysisHistoryEntry[]>([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem("analysis_history")
      if (raw) setHistory(JSON.parse(raw))
    } catch {
      // ignore
    }
    setLoaded(true)
  }, [])

  if (!loaded) return null

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
              className="text-sm font-medium text-blue-600 border-b-2 border-blue-600 transition-colors"
            >
              履歴
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto w-full px-4 py-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">分析履歴</h2>

        {history.length === 0 ? (
          <Card>
            <div className="text-center py-10 text-gray-400">
              <p>分析履歴がありません。</p>
              <Link href="/analysis" className="text-sm text-blue-600 hover:underline mt-2 inline-block">
                局面入力へ
              </Link>
            </div>
          </Card>
        ) : (
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50 text-gray-600 text-left">
                    <th className="px-3 py-2 font-medium border-b border-gray-200">分析日時</th>
                    <th className="px-3 py-2 font-medium border-b border-gray-200">局</th>
                    <th className="px-3 py-2 font-medium border-b border-gray-200">自席</th>
                    <th className="px-3 py-2 font-medium border-b border-gray-200">推奨打牌</th>
                    <th className="px-3 py-2 font-medium border-b border-gray-200">期待値</th>
                    <th className="px-3 py-2 font-medium border-b border-gray-200"></th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((entry, i) => {
                    const gs = entry.game_state
                    const topCandidate = [...entry.candidates].sort(
                      (a, b) => b.round_ev - a.round_ev
                    )[0]
                    const roundLabel = `${ROUND_WIND_LABEL[gs.round_wind] ?? gs.round_wind}${gs.hand_number}局`
                    const seatLabel = SEAT_LABELS[gs.player_seat] ?? String(gs.player_seat)

                    return (
                      <tr
                        key={entry.id}
                        className="border-b border-gray-100 hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-3 py-2 text-gray-700 whitespace-nowrap">
                          {formatTimestamp(entry.timestamp)}
                        </td>
                        <td className="px-3 py-2">{roundLabel}</td>
                        <td className="px-3 py-2">{seatLabel}家</td>
                        <td className="px-3 py-2 font-mono font-bold">
                          {topCandidate ? topCandidate.discard : "—"}
                        </td>
                        <td
                          className={
                            topCandidate
                              ? topCandidate.round_ev > 0
                                ? "px-3 py-2 font-semibold text-green-700"
                                : "px-3 py-2 font-semibold text-red-700"
                              : "px-3 py-2 text-gray-400"
                          }
                        >
                          {topCandidate ? formatEv(topCandidate.round_ev) : "—"}
                        </td>
                        <td className="px-3 py-2">
                          <Link
                            href={`/history/${i}`}
                            className="text-blue-600 hover:underline text-xs"
                          >
                            詳細
                          </Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}
      </main>
    </div>
  )
}
