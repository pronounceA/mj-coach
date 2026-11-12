"use client"

import { PhysicalTileInput } from "@/types/analysis"
import { cn } from "@/lib/utils"

interface TilePickerProps {
  value: PhysicalTileInput[]
  onChange: (tiles: PhysicalTileInput[]) => void
  maxCount?: number
  occupiedTiles?: PhysicalTileInput[]
  label?: string
}

export const SUIT_STYLES: Record<string, { bg: string; border: string; text: string }> = {
  m: { bg: "bg-red-100", border: "border-red-400", text: "text-red-900" },
  p: { bg: "bg-blue-100", border: "border-blue-400", text: "text-blue-900" },
  s: { bg: "bg-green-100", border: "border-green-400", text: "text-green-900" },
  z: { bg: "bg-gray-100", border: "border-gray-400", text: "text-gray-700" },
}

export const HONOR_LABELS = ["東", "南", "西", "北", "白", "發", "中"]

function tileKey(t: PhysicalTileInput): string {
  return `${t.suit}${t.rank}`
}

const SUIT_ORDER: Record<string, number> = { m: 0, p: 1, s: 2, z: 3 }

function sortTiles(tiles: PhysicalTileInput[]): PhysicalTileInput[] {
  return [...tiles].sort((a, b) => {
    const sd = SUIT_ORDER[a.suit] - SUIT_ORDER[b.suit]
    return sd !== 0 ? sd : a.rank - b.rank
  })
}

function countByType(tiles: PhysicalTileInput[]): Map<string, number> {
  const map = new Map<string, number>()
  for (const t of tiles) {
    const k = tileKey(t)
    map.set(k, (map.get(k) ?? 0) + 1)
  }
  return map
}

export function TilePicker({
  value,
  onChange,
  maxCount = 14,
  occupiedTiles = [],
  label,
}: TilePickerProps) {
  const valueCounts = countByType(value)
  const occupiedCounts = countByType(occupiedTiles)

  function totalCount(suit: string, rank: number): number {
    const k = `${suit}${rank}`
    return (valueCounts.get(k) ?? 0) + (occupiedCounts.get(k) ?? 0)
  }

  function handleAdd(suit: "m" | "p" | "s" | "z", rank: number) {
    if (value.length >= maxCount) return
    if (totalCount(suit, rank) >= 4) return
    const tile: PhysicalTileInput = {
      suit,
      rank,
      variant: "normal",
      physical_id: `${suit}${rank}_${Date.now()}_${Math.random()}`,
    }
    onChange([...value, tile])
  }

  function handleRemove(physical_id: string) {
    // Remove the last tile of that type, identified by physical_id
    const idx = value.findIndex((t) => t.physical_id === physical_id)
    if (idx === -1) return
    const next = [...value]
    next.splice(idx, 1)
    onChange(next)
  }

  function handleClear() {
    onChange([])
  }

  const suits: Array<{ suit: "m" | "p" | "s" | "z"; ranks: number[]; suitLabel: string }> = [
    { suit: "m", ranks: [1, 2, 3, 4, 5, 6, 7, 8, 9], suitLabel: "萬" },
    { suit: "p", ranks: [1, 2, 3, 4, 5, 6, 7, 8, 9], suitLabel: "筒" },
    { suit: "s", ranks: [1, 2, 3, 4, 5, 6, 7, 8, 9], suitLabel: "索" },
    { suit: "z", ranks: [1, 2, 3, 4, 5, 6, 7], suitLabel: "字" },
  ]

  return (
    <div className="flex flex-col gap-2">
      {label && <span className="text-sm font-medium text-gray-700">{label}</span>}

      <div className="flex flex-col gap-1">
        {suits.map(({ suit, ranks, suitLabel }) => {
          const style = SUIT_STYLES[suit]
          return (
            <div key={suit} className="flex items-center gap-1">
              <span className="w-5 text-xs text-gray-500 font-medium shrink-0">{suitLabel}</span>
              <div className="flex gap-1 flex-wrap">
                {ranks.map((rank) => {
                  const used = totalCount(suit, rank)
                  const disabled = used >= 4 || value.length >= maxCount
                  const tileLabel =
                    suit === "z" ? HONOR_LABELS[rank - 1] : String(rank)
                  const suitSuffix = suit !== "z" ? suit : ""

                  return (
                    <button
                      key={rank}
                      type="button"
                      disabled={disabled}
                      onClick={() => handleAdd(suit, rank)}
                      className={cn(
                        "relative w-9 h-11 rounded border-2 text-xs font-bold flex flex-col items-center justify-center leading-tight transition-opacity",
                        style.bg,
                        style.border,
                        style.text,
                        disabled
                          ? "opacity-30 cursor-not-allowed"
                          : "hover:brightness-95 cursor-pointer"
                      )}
                    >
                      <span className="text-sm leading-none">{tileLabel}</span>
                      {suitSuffix && (
                        <span className="text-[9px] opacity-70">{suitSuffix}</span>
                      )}
                      {used > 0 && (
                        <span className="absolute -top-1 -right-1 bg-gray-700 text-white text-[9px] rounded-full w-3.5 h-3.5 flex items-center justify-center leading-none">
                          {used}
                        </span>
                      )}
                    </button>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected tiles display */}
      <div className="flex items-start gap-2 min-h-[2rem]">
        <span className="text-xs text-gray-500 mt-1 shrink-0">選択中 ({value.length}/{maxCount}):</span>
        <div className="flex flex-wrap gap-1">
          {value.map((tile) => {
            const style = SUIT_STYLES[tile.suit]
            const tileLabel =
              tile.suit === "z"
                ? HONOR_LABELS[tile.rank - 1]
                : `${tile.rank}${tile.suit}`
            return (
              <span
                key={tile.physical_id}
                className={cn(
                  "inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs font-medium border",
                  style.bg,
                  style.border,
                  style.text
                )}
              >
                {tileLabel}
                <button
                  type="button"
                  onClick={() => handleRemove(tile.physical_id)}
                  className="ml-0.5 hover:opacity-60 cursor-pointer"
                  aria-label={`${tileLabel}を削除`}
                >
                  ×
                </button>
              </span>
            )
          })}
        </div>
        {value.length > 0 && (
          <div className="flex gap-2 shrink-0 mt-1">
            <button
              type="button"
              onClick={() => onChange(sortTiles(value))}
              className="text-xs text-gray-400 hover:text-gray-600 underline cursor-pointer"
            >
              ソート
            </button>
            <button
              type="button"
              onClick={handleClear}
              className="text-xs text-gray-400 hover:text-gray-600 underline cursor-pointer"
            >
              クリア
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
