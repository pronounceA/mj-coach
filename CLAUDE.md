# mj-coach プロジェクト

競技麻雀向けWebアプリ。現在の局面から半荘終了までを見据え、最終的な順位・点棒・チップ収支を考慮して最善の選択を評価するコーチングツール。

詳細仕様: `_docs/mahjong_expected_value_engine_spec.md`

## 技術スタック

| レイヤー | 技術 |
|---|---|
| フロントエンド | Next.js / React / TypeScript |
| バックエンドAPI | FastAPI (Python 3.11) |
| 麻雀ライブラリ | MahjongRepository/mahjong |
| データベース | PostgreSQL 16 |
| キャッシュ | Redis 7 |
| LLM（本番） | Claude API（`LLM_PROVIDER=claude`） |
| LLM（開発） | Ollama（`LLM_PROVIDER=ollama`）|

## ディレクトリ構成

```
mj-coach/
├── _docs/                        # 仕様書・ドキュメント
├── backend/                      # FastAPI アプリケーション
│   ├── mahjong_engine/           # 麻雀計算ドメイン
│   │   ├── domain/               # ドメインモデル（Tile, Hand, GameState等）
│   │   ├── rules/                # ルール管理・検証
│   │   ├── adapters/             # 既存ライブラリのAdapter
│   │   ├── efficiency/           # シャンテン・受け入れ計算
│   │   ├── scoring/              # 役・点数計算
│   │   ├── defense/              # 押し引き・放銃リスク
│   │   ├── simulation/           # Monte Carloシミュレーション
│   │   └── evaluation/           # 期待値計算
│   ├── api/                      # FastAPI ルーター
│   ├── tests/                    # テスト
│   ├── main.py                   # FastAPIエントリーポイント
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                     # Next.js アプリケーション
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── CLAUDE.md
```

## 開発環境の起動

```bash
cp .env.example .env
docker compose up --build
```

| サービス | URL |
|---|---|
| フロントエンド | http://localhost:3000 |
| バックエンドAPI | http://localhost:8000 |
| APIドキュメント | http://localhost:8000/docs |

## コーディング規約

### 共通
- コメントは原則書かない。WHYが非自明な場合のみ1行で記載

### バックエンド (Python)
- 型ヒントを必ず付ける
- Pydantic v2 でリクエスト・レスポンスのスキーマを定義する
- ドメインロジックは `mahjong_engine/` に閉じ込め、`api/` には書かない
- LLMにシャンテン数・点数・期待値を計算させない

### フロントエンド (TypeScript)
- `any` 型の使用禁止
- コンポーネントは関数コンポーネントで統一

## 設計原則（仕様書より）

- 麻雀の計算ロジックをAPIルートに書かない
- LLMは計算結果の**解釈・説明**のみ行う（計算はエンジンが担う）
- 既存ライブラリへの依存はAdapter層で隔離する
- すべての分析結果に使用したルールバージョンと計算モデルバージョンを記録する
- 局単位の期待値と半荘全体の期待値を明確に区別する
- チップ効果とドラ効果を分離して評価する

## APIエンドポイント概要

```
GET/POST /api/rules              ルール管理
POST     /api/analysis/shanten   シャンテン計算
POST     /api/analysis/ukeire    受け入れ計算
POST     /api/analysis/scoring   点数計算
POST     /api/analysis/discards  打牌候補比較
POST     /api/analysis/push-fold 押し引き評価
POST     /api/analysis/match-ev  半荘期待値計算
POST     /api/coach/sessions     AIコーチセッション
```

## 実装フェーズ

1. **Phase 1** — 既存ライブラリ導入・シャンテン・受け入れ・点数計算
2. **Phase 2** — 赤牌・青牌・ドラ・チップ・ルールプロファイル管理
3. **Phase 3** — 和了確率・打点期待値・チップ期待値・押し引き
4. **Phase 4** — 順位点・半荘シミュレーション・最終順位期待値
5. **Phase 5** — AIコーチ（計算結果の自然言語説明・壁打ち）
