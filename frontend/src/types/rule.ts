export interface RedTileConfig {
  count_per_suit: number
  han: number
}

export interface ChipPayer {
  ron: string
  tsumo: string
}

export interface BlueTileConfig {
  count_per_suit: number
  han: number
  chip_enabled: boolean
  chips_per_blue_tile: number
  chip_trigger: string
  chip_payer: ChipPayer
}

export interface ChipSettlement {
  mode: string
  chip_value: number | null
}

export interface UmaConfig {
  first: number
  second: number
  third: number
  fourth: number
}

export interface ScoringConfig {
  oka: number | null
  uma: UmaConfig
  tie_break: string
  last_round_win_stop: boolean
}

export interface RuleDefinition {
  player_count: number
  red_tile: RedTileConfig
  blue_tile: BlueTileConfig
  chip_settlement: ChipSettlement
  scoring: ScoringConfig
}

export interface RuleProfileVersion {
  id: string
  version: number
  definition: RuleDefinition
  is_active: boolean
  created_at: string
}

export interface RuleProfile {
  id: string
  name: string
  description: string | null
  created_at: string
  updated_at: string
  latest_version: RuleProfileVersion | null
}

export const DEFAULT_RULE_DEFINITION: RuleDefinition = {
  player_count: 4,
  red_tile: { count_per_suit: 1, han: 1 },
  blue_tile: {
    count_per_suit: 1,
    han: 1,
    chip_enabled: true,
    chips_per_blue_tile: 2,
    chip_trigger: "AGARI_WITH_BLUE",
    chip_payer: { ron: "DEAL_IN_PLAYER", tsumo: "ALL_OPPONENTS" },
  },
  chip_settlement: { mode: "SEPARATE", chip_value: null },
  scoring: {
    oka: null,
    uma: { first: 0, second: 0, third: 0, fourth: 0 },
    tie_break: "DEALER_ORDER",
    last_round_win_stop: false,
  },
}
