# 設定可能項目一覧

ルールプロファイル・シミュレーション設定として変更できる項目の一覧。
実装時はこの一覧を `rule_profiles` テーブルおよびルールプロファイル JSON スキーマの基準とする。

---

## 1. 牌設定

### 赤牌

| 項目 | キー | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| 赤牌の枚数（スートあたり） | `red_tile.count_per_suit` | `int` (0〜4) | `1` | 0 にすると赤牌なしルールになる |
| 赤牌の翻数 | `red_tile.han` | `int` | `1` | ドラとしての翻数 |

### 青牌

| 項目 | キー | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| 青牌の枚数（スートあたり） | `blue_tile.count_per_suit` | `int` (0 or 1) | `1` | 0 にすると青牌なしルールになる |
| 青牌の翻数 | `blue_tile.han` | `int` | `1` | ドラとしての翻数 |

### 牌枚数のバリデーション制約

1スートの5牌は合計4枚固定（`normal + red + blue = 4`）。  
`red.count_per_suit + blue.count_per_suit > 4` となる設定はルールバリデーション（`rule_validator`）でエラーとして弾く。

```
normal枚数 = 4 − red.count_per_suit − blue.count_per_suit  ≥ 0
```

| red | blue | normal | 判定 |
|---|---|---|---|
| 1 | 1 | 2 | OK（デフォルト） |
| 3 | 1 | 0 | OK |
| 4 | 1 | -1 | **NG → バリデーションエラー** |

---

## 2. チップ設定

| 項目 | キー | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| チップ機能の有効/無効 | `blue_tile.chip_enabled` | `bool` | `true` | false にするとチップ計算をスキップ |
| 青牌1枚あたりのチップ数 | `blue_tile.chips_per_blue_tile` | `int` | `2` | 和了時に手牌の青牌1枚につき獲得するチップ数 |
| チップ獲得トリガー | `blue_tile.chip_trigger` | `str` | `"AGARI_WITH_BLUE"` | 現時点では `AGARI_WITH_BLUE` 固定（副露した青牌も対象） |
| ロン時の支払者 | `blue_tile.chip_payer.ron` | `str` | `"DEAL_IN_PLAYER"` | ロン和了時に全チップを支払うプレイヤー |
| ツモ時の支払者 | `blue_tile.chip_payer.tsumo` | `str` | `"ALL_OPPONENTS"` | ツモ和了時に他3人がそれぞれ全チップを支払う |
| チップ1枚の精算額 | `chip_settlement.chip_value` | `int` | ※要設定 | 点棒換算額（例: 1000 なら1枚=1,000点相当） |

---

## 3. 順位点設定

| 項目 | キー | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| オカ | `scoring.oka` | `int` | ※要設定 | 返し点超過分の加算（例: 30000返しなら供託25000点等） |
| ウマ | `scoring.uma` | `object` | ※要設定 | 順位ごとの加減点（例: `{"first": 20000, "second": 10000, "third": -10000, "fourth": -20000}`） |

---

## 4. ルール設定

| 項目 | キー | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| 同点時の順位決定方法 | `scoring.tie_break` | `str` | `"DEALER_ORDER"` | `"DEALER_ORDER"` = 起家に近い席の順位が上 |
| 上がりやめ | `scoring.last_round_win_stop` | `bool` | `false` | `false` = Mリーグ準拠（上がりやめ無し） |
| プレイヤー数 | `player_count` | `int` | `4` | 現時点では四人麻雀のみ（要確認） |

---

## 5. シミュレーション設定

分析リクエスト時に指定するパラメータ。ルールプロファイルではなく API リクエストに含める。

| 項目 | キー | 型 | デフォルト | 説明 |
|---|---|---|---|---|
| シミュレーション回数 | `simulation_count` | `int` | `10000` | 多いほど精度が上がるが計算時間が増加 |
| 対戦相手モデル | `opponent_model_id` | `str` | `"basic"` | `random` / `basic` / `aggressive` / `defensive` / `custom` |
| 乱数シード | `random_seed` | `int \| null` | `null` | 指定すると再現可能なシミュレーションになる |

---

---

## 6. LLM設定

プロバイダー選択のみDBで管理し、APIキー等の認証情報は `.env` で管理する。

### DB管理（設定画面から変更可能）

| 項目 | テーブル・カラム | 値 | 説明 |
|---|---|---|---|
| LLMプロバイダー | `system_settings.llm_provider` | `claude` / `ollama` | 設定画面から切り替え可能 |

### .env管理（環境変数・変更には再デプロイが必要）

| 項目 | 環境変数 | 説明 |
|---|---|---|
| Claude APIキー | `ANTHROPIC_API_KEY` | `llm_provider=claude` の場合に使用 |
| Claudeモデル | `CLAUDE_MODEL` | 使用するClaudeモデルID（例: `claude-sonnet-4-6`） |
| OllamaエンドポイントURL | `OLLAMA_BASE_URL` | `llm_provider=ollama` の場合に使用 |
| Ollamaモデル | `OLLAMA_MODEL` | 使用するOllamaモデル名（例: `llama3.2`） |

---

## 設定値のスコープ整理

```
ルールプロファイル（DB 管理・バージョン管理対象）
├── 牌設定
├── チップ設定
├── 順位点設定（オカ・ウマ）
└── ルール設定（同点処理・終了条件）

システム設定（DB 管理・設定画面から変更可能）
└── LLMプロバイダー選択（claude / ollama）

環境変数（.env 管理・再デプロイで反映）
├── APIキー・認証情報
└── 接続先URL・モデル名

分析リクエスト（API リクエスト時に指定）
└── シミュレーション設定（回数・相手モデル・乱数シード）
```

分析結果には使用したルールプロファイルのバージョン ID とシミュレーション設定を必ず記録する。
