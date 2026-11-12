"use client"

import { createContext, ReactNode, useContext, useMemo, useState } from "react"
import { PhysicalTileInput } from "@/types/analysis"
import { SUIT_STYLES, HONOR_LABELS } from "@/components/tiles/TilePicker"
import { cn } from "@/lib/utils"

export interface FooterHand {
  hand: PhysicalTileInput[]
  drawnTile: PhysicalTileInput | null
  doraIndicators: PhysicalTileInput[]
}

interface FooterHandContextValue {
  footerHand: FooterHand
  setFooterHand: (next: FooterHand) => void
}

const EMPTY_FOOTER_HAND: FooterHand = { hand: [], drawnTile: null, doraIndicators: [] }

const FooterHandContext = createContext<FooterHandContextValue | null>(null)

export function useFooterHand(): FooterHandContextValue {
  const ctx = useContext(FooterHandContext)
  if (!ctx) throw new Error("useFooterHand must be used within HandFooterProvider")
  return ctx
}

function FooterTile({ tile, highlight }: { tile: PhysicalTileInput; highlight?: boolean }) {
  const style = SUIT_STYLES[tile.suit]
  const tileLabel = tile.suit === "z" ? HONOR_LABELS[tile.rank - 1] : String(tile.rank)
  return (
    <span
      className={cn(
        "w-7 h-9 rounded border-2 flex flex-col items-center justify-center leading-tight font-bold shrink-0",
        style.bg,
        style.border,
        style.text,
        highlight && "ring-2 ring-amber-400"
      )}
    >
      <span className="text-xs leading-none">{tileLabel}</span>
      {tile.suit !== "z" && <span className="text-[8px] opacity-70">{tile.suit}</span>}
    </span>
  )
}

function HandFooter({ footerHand }: { footerHand: FooterHand }) {
  const { hand, drawnTile, doraIndicators } = footerHand
  if (hand.length === 0) return null

  return (
    <footer className="fixed inset-x-0 bottom-0 z-20 bg-white/95 backdrop-blur border-t border-gray-200 shadow-[0_-2px_8px_rgba(0,0,0,0.06)]">
      <div className="max-w-4xl mx-auto px-4 py-2 flex flex-wrap items-end gap-x-6 gap-y-2">
        <div className="flex flex-col gap-1 min-w-0">
          <span className="text-[10px] text-gray-500">手牌 ({hand.length}枚)</span>
          <div className="flex items-end gap-0.5 flex-wrap">
            {hand.map((t) => (
              <FooterTile key={t.physical_id} tile={t} />
            ))}
            {drawnTile && (
              <>
                <span className="w-2" aria-hidden />
                <FooterTile tile={drawnTile} highlight />
              </>
            )}
          </div>
        </div>
        {doraIndicators.length > 0 && (
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-gray-500">ドラ表示牌</span>
            <div className="flex gap-0.5">
              {doraIndicators.map((t) => (
                <FooterTile key={t.physical_id} tile={t} />
              ))}
            </div>
          </div>
        )}
      </div>
    </footer>
  )
}

export function HandFooterProvider({ children }: { children: ReactNode }) {
  const [footerHand, setFooterHand] = useState<FooterHand>(EMPTY_FOOTER_HAND)
  const value = useMemo(() => ({ footerHand, setFooterHand }), [footerHand])

  return (
    <FooterHandContext.Provider value={value}>
      {children}
      <HandFooter footerHand={footerHand} />
    </FooterHandContext.Provider>
  )
}
