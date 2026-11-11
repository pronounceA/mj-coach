"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { TilePicker } from "@/components/tiles/TilePicker"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Card } from "@/components/ui/Card"
import { rulesApi } from "@/lib/api"
import { analysisApi } from "@/lib/api"
import { PhysicalTileInput, GameStateInput } from "@/types/analysis"
import { RuleProfile } from "@/types/rule"

function generateRandomHand(): { hand: PhysicalTileInput[]; drawnTile: PhysicalTileInput } {
  const allTiles: PhysicalTileInput[] = []
  for (const suit of ["m", "p", "s"] as const) {
    for (let rank = 1; rank <= 9; rank++) {
      for (let i = 0; i < 4; i++) {
        allTiles.push({ suit, rank, variant: "normal", physical_id: `${rank}${suit}_${i}` })
      }
    }
  }
  for (let rank = 1; rank <= 7; rank++) {
    for (let i = 0; i < 4; i++) {
      allTiles.push({ suit: "z", rank, variant: "normal", physical_id: `${rank}z_${i}` })
    }
  }
  for (let i = allTiles.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[allTiles[i], allTiles[j]] = [allTiles[j], allTiles[i]]
  }
  const dealt = allTiles.slice(0, 14)
  return {
    hand: dealt.slice(0, 13).map((t, i) => ({ ...t, physical_id: `hand_${i}` })),
    drawnTile: { ...dealt[13], physical_id: "drawn_0" },
  }
}

export default function AnalysisPage() {
  const router = useRouter()

  const [hand, setHand] = useState<PhysicalTileInput[]>([])
  const [drawnTile, setDrawnTile] = useState<PhysicalTileInput[]>([])
  const [doraIndicators, setDoraIndicators] = useState<PhysicalTileInput[]>([])
  const [roundWind, setRoundWind] = useState<"E" | "S">("E")
  const [handNumber, setHandNumber] = useState(1)
  const [honba, setHonba] = useState(0)
  const [junme, setJunme] = useState(1)
  const [riichiSticks, setRiichiSticks] = useState(0)
  const [isDealer, setIsDealer] = useState(false)
  const [playerSeat, setPlayerSeat] = useState(0)
  const [scores, setScores] = useState([25000, 25000, 25000, 25000])
  const [ruleVersionId, setRuleVersionId] = useState("00000000-0000-0000-0000-000000000000")
  const [rules, setRules] = useState<RuleProfile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    rulesApi.list().then(setRules).catch(() => {/* no rules available */})
  }, [])

  const allUsedTiles = [...hand, ...drawnTile, ...doraIndicators]

  function handleScoreChange(index: number, val: string) {
    const next = [...scores]
    next[index] = parseInt(val, 10) || 0
    setScores(next)
  }

  function handleRandomHand() {
    const { hand: newHand, drawnTile: newDrawn } = generateRandomHand()
    setHand(newHand)
    setDrawnTile([newDrawn])
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (hand.length < 1) {
      setError("手牌を入力してください。")
      return
    }
    if (hand.length === 13 && drawnTile.length === 0) {
      setError("手牌が13枚の場合、ツモ牌を入力してください。")
      return
    }
    if (hand.length + (drawnTile.length > 0 ? 1 : 0) > 14) {
      setError("手牌 + ツモ牌は14枚以内にしてください。")
      return
    }

    const gameState: GameStateInput = {
      hand,
      drawn_tile: drawnTile.length > 0 ? drawnTile[0] : null,
      melds: [],
      discards: [[], [], [], []],
      dora_indicators: doraIndicators,
      scores,
      round_wind: roundWind,
      hand_number: handNumber,
      honba,
      riichi_sticks: riichiSticks,
      dealer: isDealer ? playerSeat : (playerSeat + 1) % 4,
      player_seat: playerSeat,
      junme,
      remaining_hands: null,
      rule_version_id: ruleVersionId,
    }

    setLoading(true)
    try {
      const result = await analysisApi.discards(gameState)
      sessionStorage.setItem(
        "analysis_state",
        JSON.stringify({ gameState, candidates: result.candidates })
      )
      router.push("/analysis/result")
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析に失敗しました。")
    } finally {
      setLoading(false)
    }
  }

  const ruleOptions = [
    { value: "00000000-0000-0000-0000-000000000000", label: "デフォルト" },
    ...rules
      .filter((r) => r.latest_version != null)
      .map((r) => ({ value: r.latest_version!.id, label: r.name })),
  ]

  const seatLabels = ["東家 (0)", "南家 (1)", "西家 (2)", "北家 (3)"]

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">局面入力</h2>
        <Button type="button" variant="secondary" onClick={handleRandomHand}>
          ランダム生成
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-300 text-red-700 text-sm px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <Card title="手牌 (13枚)">
        <TilePicker
          value={hand}
          onChange={setHand}
          maxCount={13}
          occupiedTiles={[...drawnTile, ...doraIndicators]}
          label="手牌"
        />
      </Card>

      <Card title="ツモ牌 (必須・1枚)">
        <TilePicker
          value={drawnTile}
          onChange={(tiles) => setDrawnTile(tiles.slice(-1))}
          maxCount={1}
          occupiedTiles={[...hand, ...doraIndicators]}
          label="ツモ牌"
        />
      </Card>

      <Card title="ドラ表示牌 (最大5枚)">
        <TilePicker
          value={doraIndicators}
          onChange={setDoraIndicators}
          maxCount={5}
          occupiedTiles={[...hand, ...drawnTile]}
          label="ドラ表示牌"
        />
      </Card>

      <Card title="局面情報">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          <Select
            id="round-wind"
            label="場"
            value={roundWind}
            onChange={(e) => setRoundWind(e.target.value as "E" | "S")}
            options={[
              { value: "E", label: "東場" },
              { value: "S", label: "南場" },
            ]}
          />
          <Select
            id="hand-number"
            label="局"
            value={String(handNumber)}
            onChange={(e) => setHandNumber(Number(e.target.value))}
            options={[1, 2, 3, 4].map((n) => ({ value: String(n), label: `${n}局` }))}
          />
          <Input
            id="junme"
            label="順目"
            type="number"
            min={1}
            max={18}
            value={junme}
            onChange={(e) => setJunme(Number(e.target.value))}
          />
          <Input
            id="honba"
            label="本場"
            type="number"
            min={0}
            value={honba}
            onChange={(e) => setHonba(Number(e.target.value))}
          />
          <Input
            id="riichi-sticks"
            label="供託"
            type="number"
            min={0}
            value={riichiSticks}
            onChange={(e) => setRiichiSticks(Number(e.target.value))}
          />
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-gray-700">親</span>
            <label className="flex items-center gap-2 h-9 cursor-pointer">
              <input
                type="checkbox"
                checked={isDealer}
                onChange={(e) => setIsDealer(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300 text-blue-600"
              />
              <span className="text-sm text-gray-700">自分が親</span>
            </label>
          </div>
          <Select
            id="player-seat"
            label="自席"
            value={String(playerSeat)}
            onChange={(e) => setPlayerSeat(Number(e.target.value))}
            options={[0, 1, 2, 3].map((n) => ({ value: String(n), label: seatLabels[n] }))}
          />
        </div>
      </Card>

      <Card title="点棒">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {scores.map((score, i) => (
            <Input
              key={i}
              id={`score-${i}`}
              label={`${["東", "南", "西", "北"][i]}家`}
              type="number"
              value={score}
              onChange={(e) => handleScoreChange(i, e.target.value)}
            />
          ))}
        </div>
      </Card>

      <Card title="ルールプロファイル">
        <Select
          id="rule-version"
          label="ルール"
          value={ruleVersionId}
          onChange={(e) => setRuleVersionId(e.target.value)}
          options={ruleOptions}
        />
      </Card>

      <div className="flex justify-end">
        <Button type="submit" loading={loading} className="px-8">
          分析実行
        </Button>
      </div>
    </form>
  )
}
