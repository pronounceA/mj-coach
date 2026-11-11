export interface PhysicalTileInput {
  suit: "m" | "p" | "s" | "z"
  rank: number
  variant: "normal" | "red" | "blue"
  physical_id: string
}

export interface MeldInput {
  meld_type: "chi" | "pon" | "kan_open" | "kan_added" | "kan_closed"
  tiles: PhysicalTileInput[]
  stolen_from: number | null
}

export interface GameStateInput {
  hand: PhysicalTileInput[]
  drawn_tile: PhysicalTileInput | null
  melds: MeldInput[]
  discards: PhysicalTileInput[][]
  dora_indicators: PhysicalTileInput[]
  scores: number[]
  chips: number[]
  round_wind: string
  hand_number: number
  honba: number
  riichi_sticks: number
  dealer: number
  player_seat: number
  junme: number | null
  remaining_hands: number | null
  rule_version_id: string
}

export interface DiscardCandidate {
  discard: string
  shanten: number
  ukeire: { tile_type: string; remaining_count: number }[]
  total_ukeire: number
  normal_dora: number
  red_dora: number
  blue_dora: number
  total_dora_han: number
  chip_count_on_win: number
  win_probability: number
  expected_han: number
  expected_cost: number
  deal_in_probability: number
  round_ev: number
}

export interface DiscardsResult {
  candidates: DiscardCandidate[]
}

export interface PushFoldResult {
  recommendation: "push" | "fold"
  push_ev: number
  fold_ev: number
  ev_diff: number
  push_win_probability: number
  push_deal_in_probability: number
  fold_deal_in_probability: number
}

export interface AnalysisHistoryEntry {
  id: string
  timestamp: string
  game_state: GameStateInput
  candidates: DiscardCandidate[]
}

export type OpponentModelType = "random" | "basic" | "aggressive" | "defensive"

export interface MatchEvRequest {
  game_state: GameStateInput
  discard: PhysicalTileInput
  opponent_models: OpponentModelType[]
  n_simulations: number
}

export interface MatchEvResult {
  placement_distribution: {
    first: number
    second: number
    third: number
    fourth: number
  }
  mean_placement: number
  mean_final_score: number
  ci_low_95: number
  ci_high_95: number
  simulation_count: number
}
