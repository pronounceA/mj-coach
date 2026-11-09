# データベース設計

## ER図（概略）

```
users
 ├── rule_profiles ── rule_profile_versions
 ├── analysis_sessions ── game_states
 │    ├── analysis_results
 │    └── simulation_jobs
 ├── matches ── rounds
 └── coach_sessions ── coach_messages

opponent_models ── opponent_model_versions
```

---

## テーブル定義

### system_settings

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | INT | NOT NULL | PK（固定1行のみ使用） |
| `llm_provider` | VARCHAR(20) | NOT NULL | `claude` / `ollama` |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

- レコードは常に1行のみ（初期データとして INSERT しておく）

---

### users

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `email` | VARCHAR(255) | NOT NULL | UNIQUE |
| `password_hash` | VARCHAR(255) | NOT NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

---

### rule_profiles

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `name` | VARCHAR(100) | NOT NULL | ルール名 |
| `description` | TEXT | NULL | |
| `created_by` | UUID | NOT NULL | FK → users.id |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

---

### rule_profile_versions

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `rule_profile_id` | UUID | NOT NULL | FK → rule_profiles.id |
| `version` | INT | NOT NULL | 1始まりの連番 |
| `definition` | JSONB | NOT NULL | ルール定義（settings.md 参照） |
| `is_active` | BOOLEAN | NOT NULL | 有効バージョンフラグ |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

- UNIQUE(`rule_profile_id`, `version`)
- 既存バージョンは更新せず、常に新バージョンを INSERT する

---

### opponent_models

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `name` | VARCHAR(50) | NOT NULL | `random` / `basic` / `aggressive` / `defensive` / `custom` |
| `description` | TEXT | NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

### opponent_model_versions

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `opponent_model_id` | UUID | NOT NULL | FK → opponent_models.id |
| `version` | INT | NOT NULL | 1始まりの連番 |
| `parameters` | JSONB | NOT NULL | モデルパラメータ |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

- UNIQUE(`opponent_model_id`, `version`)

---

### analysis_sessions

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `user_id` | UUID | NOT NULL | FK → users.id |
| `rule_profile_version_id` | UUID | NOT NULL | FK → rule_profile_versions.id |
| `opponent_model_version_id` | UUID | NOT NULL | FK → opponent_model_versions.id |
| `analysis_mode` | VARCHAR(20) | NOT NULL | `hand_ev` / `match_ev` |
| `simulation_count` | INT | NOT NULL | |
| `random_seed` | INT | NULL | NULL = ランダム |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

### game_states

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `analysis_session_id` | UUID | NOT NULL | FK → analysis_sessions.id |
| `hand` | JSONB | NOT NULL | 手牌（PhysicalTile[]） |
| `drawn_tile` | JSONB | NULL | ツモ牌 |
| `melds` | JSONB | NOT NULL | 副露（Meld[]） |
| `discards` | JSONB | NOT NULL | 河（全プレイヤー） |
| `dora_indicators` | JSONB | NOT NULL | ドラ表示牌 |
| `scores` | JSONB | NOT NULL | 点棒（int[4]） |
| `chips` | JSONB | NOT NULL | チップ数（int[4]） |
| `round_wind` | VARCHAR(10) | NOT NULL | `east` / `south` |
| `hand_number` | INT | NOT NULL | 局数 |
| `honba` | INT | NOT NULL | 本場 |
| `riichi_sticks` | INT | NOT NULL | 供託 |
| `dealer` | INT | NOT NULL | 親の座席（0〜3） |
| `player_seat` | INT | NOT NULL | 自分の座席（0〜3） |
| `remaining_hands` | INT | NULL | 残り局数の見積もり |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

### analysis_results

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `analysis_session_id` | UUID | NOT NULL | FK → analysis_sessions.id |
| `game_state_id` | UUID | NOT NULL | FK → game_states.id |
| `engine_version` | VARCHAR(20) | NOT NULL | 計算エンジンのバージョン |
| `candidates` | JSONB | NOT NULL | 打牌候補ごとの EV・確率・リスク |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

### simulation_jobs

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `analysis_session_id` | UUID | NOT NULL | FK → analysis_sessions.id |
| `status` | VARCHAR(20) | NOT NULL | `pending` / `running` / `completed` / `failed` |
| `progress` | INT | NOT NULL | 進捗（0〜100） |
| `result` | JSONB | NULL | 完了時に格納 |
| `error_message` | TEXT | NULL | 失敗時のエラー内容 |
| `started_at` | TIMESTAMPTZ | NULL | |
| `completed_at` | TIMESTAMPTZ | NULL | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

### matches

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `user_id` | UUID | NOT NULL | FK → users.id |
| `rule_profile_version_id` | UUID | NOT NULL | FK → rule_profile_versions.id |
| `final_scores` | JSONB | NULL | 最終点棒（int[4]） |
| `final_chips` | JSONB | NULL | 最終チップ数（int[4]） |
| `final_ranks` | JSONB | NULL | 最終順位（int[4]） |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `completed_at` | TIMESTAMPTZ | NULL | |

---

### rounds

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `match_id` | UUID | NOT NULL | FK → matches.id |
| `round_wind` | VARCHAR(10) | NOT NULL | `east` / `south` |
| `hand_number` | INT | NOT NULL | 局数 |
| `honba` | INT | NOT NULL | 本場 |
| `outcome` | VARCHAR(20) | NOT NULL | `tsumo` / `ron` / `draw` / `chombo` |
| `score_changes` | JSONB | NOT NULL | 点棒変動（int[4]） |
| `chip_changes` | JSONB | NOT NULL | チップ変動（int[4]） |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

### coach_sessions

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `user_id` | UUID | NOT NULL | FK → users.id |
| `analysis_session_id` | UUID | NULL | FK → analysis_sessions.id（局面コンテキスト引き継ぎ） |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

---

### coach_messages

| カラム名 | 型 | NULL | 説明 |
|---|---|---|---|
| `id` | UUID | NOT NULL | PK |
| `coach_session_id` | UUID | NOT NULL | FK → coach_sessions.id |
| `role` | VARCHAR(10) | NOT NULL | `user` / `assistant` |
| `content` | TEXT | NOT NULL | メッセージ本文 |
| `recalculation_result` | JSONB | NULL | 再計算が発生した場合の結果 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

---

## フェーズ別テーブル実装順

| フェーズ | テーブル |
|---|---|
| Phase 1 | `users`, `rule_profiles`, `rule_profile_versions`, `opponent_models`, `opponent_model_versions`, `analysis_sessions`, `game_states`, `analysis_results` |
| Phase 2 | `rule_profile_versions`（definition スキーマ拡張） |
| Phase 4 | `simulation_jobs`, `matches`, `rounds` |
| Phase 5 | `system_settings`, `coach_sessions`, `coach_messages` |
