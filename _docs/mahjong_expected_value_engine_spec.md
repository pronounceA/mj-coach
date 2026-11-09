# 競技麻雀向けWebアプリ：期待値計算エンジン詳細仕様書

## 1. 目的と設計方針

本システムでは、単に「何を切ればシャンテン数が下がるか」だけでなく、**現在の局面から半荘終了までを見据え、最終的な順位・点棒・チップ収支を考慮して最善の選択を評価すること**を目指す。

設計上、次の3つを分離する。

1.  **麻雀ルールエンジン**：牌、役、ドラ、符、翻、点数など、ルールに従った事実を計算する。
2.  **局面評価・シミュレーションエンジン**：和了率、放銃率、打点、局収支、最終順位などの確率的な評価を行う。
3.  **AIコーチ**：計算結果を根拠に、候補手の比較や戦術的な理由を説明する。

青牌の価値を固定の「2,000点」として扱わず、ドラによる打点変化とチップ獲得期待値を分け、さらに順位状況に応じた価値を評価する。

## 2. 既存エンジンの調査・比較

既存ライブラリを活用し、牌効率・役判定・点数計算をゼロから実装しない方針とする。以下は候補の比較であり、採用時には公式リポジトリの最新状態、依存関係、ライセンス、商用利用・配布条件を再確認する。

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  候補                                                                        主な機能                                             言語・ライセンス（要再確認）   評価
  --------------------------------------------------------------------------- ---------------------------------------------------- ------------------------------ --------------------------------
  [MahjongRepository/mahjong](https://github.com/MahjongRepository/mahjong)   シャンテン、和了判定、役・符・翻・点数               Python / MIT                   基盤候補

  [nekobean/mahjong-cpp](https://github.com/nekobean/mahjong-cpp)             シャンテン、有効牌、不要牌、点数、確率・期待値関連   C++17 / GPL-3.0                期待値計算の研究候補

  [Mortal](https://github.com/Equim-chan/Mortal)                              深層強化学習による麻雀AI                             Rust等 / AGPL-3.0              打牌判断・対戦モデルの研究候補

  [Riichi Advanced](https://github.com/EpicOrange/riichi_advanced)            ルールセット・独自ルール拡張を備える対局エンジン     Elixir等 / AGPL-3.0            独自ルール表現の研究候補
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

### 2.1 MahjongRepository/mahjong

**第一候補として採用を検討する。**

Pythonライブラリであり、FastAPIバックエンドに組み込みやすい。公開情報では、シャンテン数、和了判定、役・翻・符・点数計算などを扱う。

公式資料： - [GitHub](https://github.com/MahjongRepository/mahjong) -
[ドキュメント](https://mahjongrepository.github.io/mahjong/)

不足する可能性がある機能： - 青牌独自のドラ・チップ処理 -
独自ルールにおける牌の枚数・種類 - チップ精算 - 半荘全体の順位期待値 -
対戦相手の行動モデル - 押し引きの総合評価

採用前に、現行バージョンでのAPI、対応ルール、牌表現、テスト範囲を確認する。

### 2.2 nekobean/mahjong-cpp

期待値計算の参考候補。C++17で実装されており、シャンテン数、有効牌、不要牌、点数計算に加えて確率・期待値関連の機能が公開されている。

公式資料：[GitHub](https://github.com/nekobean/mahjong-cpp)

GPL-3.0の場合、組み込み方・配布形態・改変の有無によってライセンス上の義務が生じる可能性がある。ライセンス確認が完了するまでは、本体への組み込みを保留し、アルゴリズムの研究・比較対象とする。

### 2.3 Mortal

深層強化学習を利用した麻雀AI。単なる点数計算ライブラリではなく、打牌判断モデルを持つ。

公式資料： - [GitHub](https://github.com/Equim-chan/Mortal) -
[ドキュメント](https://mortal.ekyu.moe/)

用途候補： - 標準ルールにおける打牌判断との比較 -
対戦相手の打牌傾向の研究 - 牌譜レビュー機能の参考

独自ルールにそのまま最適な判断を出せるとは限らない。AGPL-3.0の適用範囲も確認する。

### 2.4 Riichi Advanced

複数の麻雀ルールセットや独自ルール表現を研究する候補。

公式資料： - [GitHub](https://github.com/EpicOrange/riichi_advanced) -
[公式サイト](https://riichiadvanced.com/)

Python製分析エンジンに直接組み込むには技術的な距離がある。AGPL-3.0を含むライセンス条件も確認する。

### 2.5 採用方針

MahjongRepository/mahjongを基本ライブラリとして採用し、独自の期待値計算エンジンを上位に構築する案を推奨する。

既存ライブラリへの依存はAdapter層で隔離し、将来的に別ライブラリや独自実装へ差し替えられる構造にする。

## 3. システム全体構成

``` mermaid
flowchart TB
    UI["Next.js / React / TypeScript"]
    API["FastAPI"]
    APP["Application Service"]
    DOMAIN["mahjong_engine<br/>ドメイン・計算パッケージ"]
    ADAPTER["Existing Engine Adapter"]
    LIB["MahjongRepository/mahjong"]
    EV["EV / Simulation Engine"]
    OPP["Opponent Model"]
    LLM["AI Coach / LLM"]
    DB[("PostgreSQL")]
    CACHE[("Redis 任意")]

    UI --> API
    API --> APP
    APP --> DOMAIN
    DOMAIN --> ADAPTER
    ADAPTER --> LIB
    DOMAIN --> EV
    EV --> OPP
    APP --> LLM
    APP --> DB
    EV --> CACHE
```

### 3.1 コンポーネントの責務

  コンポーネント            責務
  ------------------------- --------------------------------------------------
  Next.js                   手牌・局面入力、候補比較、分析結果表示
  FastAPI                   API提供、認証、入力検証、分析処理の起動
  Application Service       各計算モジュールの呼び出しと結果統合
  mahjong_engine            麻雀ドメインモデル、ルール、計算ロジック
  Existing Engine Adapter   既存ライブラリとの変換・呼び出し
  EV / Simulation Engine    確率計算、局・半荘シミュレーション
  Opponent Model            対戦相手の行動確率モデル
  AI Coach                  数値結果を用いた説明・質疑応答
  PostgreSQL                ルール、牌譜、分析履歴などの永続化
  Redis                     計算キャッシュ・非同期ジョブ管理（必要に応じて）

### 3.2 重要な設計原則

-   麻雀の計算ロジックをAPIルートに書かない。
-   LLMにシャンテン数、点数、期待値を計算させない。
-   ルール定義はデータとして管理し、任意のPythonコードを実行できる仕組みにしない。
-   すべての分析結果に使用したルールバージョンと計算モデルのバージョンを記録する。
-   局単位の期待値と半荘全体の期待値を明確に区別する。

## 4. スコープ

### 4.1 初期開発の対象

  機能                   内容                                       優先度
  ---------------------- ------------------------------------------ --------
  ルール管理             通常牌、赤牌、青牌、ドラ、チップ等の定義   必須
  手牌解析               手牌・副露・河などの入力と検証             必須
  シャンテン計算         通常手、七対子、国士無双                   必須
  受け入れ計算           有効牌の種類・残り枚数                     必須
  打点計算               役・ドラ・符・翻・点数                     必須
  打牌比較               各候補のシャンテン・受け入れ・打点比較     必須
  チップ計算             青牌のチップ獲得期待値                     必須
  局収支評価             和了・放銃・流局を含む局単位EV             必須
  順位評価               点棒状況・順位点による評価                 次段階
  半荘シミュレーション   最終順位・チップ収支の推定                 次段階
  AIコーチ               計算結果を根拠に戦術を説明                 次段階

### 4.2 初期開発の対象外

-   実際のオンライン対局機能
-   自動牌譜取得・外部サービス連携
-   あらゆる麻雀ルールを自由に記述できる汎用ルール言語
-   強化学習モデルの独自学習
-   対戦相手の個人別行動予測（牌譜データが十分に蓄積するまで）
-   完全なゲーム木探索による最適解の保証

## 5. ドメインモデル

### 5.1 牌の表現

牌の種類と物理的な牌を分ける。

``` python
from dataclasses import dataclass
from enum import Enum

class Suit(str, Enum):
    MAN = "m"
    PIN = "p"
    SOU = "s"
    HONOR = "z"

class TileVariant(str, Enum):
    NORMAL = "normal"
    RED = "red"
    BLUE = "blue"

@dataclass(frozen=True)
class TileType:
    suit: Suit
    rank: int

@dataclass(frozen=True)
class PhysicalTile:
    tile_type: TileType
    variant: TileVariant
    physical_id: str
```

例えば、通常の5筒・赤5筒・青5筒は同じ`TileType`を持つが、`PhysicalTile`としては別の牌である。

-   シャンテン計算：牌種で集計する。
-   受け入れ計算：牌種ごとの残り枚数を使う。
-   打点計算：赤牌・青牌の種類を参照する。
-   チップ計算：青牌の物理枚数や獲得条件を参照する。

### 5.2 牌の残り枚数

``` python
remaining_count = (
    rule_profile.tile_inventory[tile_type]
    - known_tiles.count(tile_type)
)
```

実際には、通常牌・赤牌・青牌の物理枚数をそれぞれ管理し、牌種単位の受け入れ枚数と、特殊牌を引く確率を別々に計算する。

### 5.3 ルールプロファイル

ルールはJSONで定義する。

``` json
{
  "rule_name": "custom_competitive_rule",
  "player_count": 4,
  "tile_inventory": {
    "5m": {"normal": 2, "red": 1, "blue": 1},
    "5p": {"normal": 2, "red": 1, "blue": 1},
    "5s": {"normal": 2, "red": 1, "blue": 1}
  },
  "blue_tile": {
    "count_per_suit": 1,
    "han": 1,
    "chip_enabled": true,
    "chips_per_blue_tile": 2,
    "chip_trigger": "AGARI_WITH_BLUE",
    "chip_payer": {
      "ron": "DEAL_IN_PLAYER",
      "tsumo": "ALL_OPPONENTS"
    }
  },
  "chip_settlement": {
    "mode": "SEPARATE",
    "chip_value": null
  },
  "scoring": {
    "oka": null,
    "uma": null,
    "tie_break": "DEALER_ORDER",
    "last_round_win_stop": false
  }
}
```

`count_per_suit` は 0 または 1 に設定可能。`chip_value`・`oka`・`uma` はルール設定から変更可能な数値。`last_round_win_stop: false` はオーラスの上がりやめ無しを示す（Mリーグ準拠）。

ルール定義には次の検証を行う。

-   牌の総枚数がルール上妥当であること。
-   牌種ごとの物理枚数が矛盾しないこと。
-   ドラ表示牌からドラ牌への対応が正しいこと。
-   有効な役・翻・符・点数体系が定義されていること。
-   チップ獲得条件と精算方式が矛盾しないこと。

## 6. 入力モデル

### 6.1 GameState

  項目                型                 内容
  ------------------- ------------------ --------------------------
  hand                PhysicalTile\[\]   自分の手牌
  drawn_tile          PhysicalTile?      現在のツモ牌
  melds               Meld\[\]           自分の副露
  discards            Discard\[\]\[\]    全プレイヤーの河
  dora_indicators     PhysicalTile\[\]   ドラ表示牌
  scores              int\[4\]           各プレイヤーの点棒
  chips               int\[4\]           各プレイヤーのチップ数
  round_wind          enum               場風
  hand_number         int                局数
  honba               int                本場
  riichi_sticks       int                供託
  dealer              int                親の座席
  player_seat         int                自分の座席
  remaining_hands     int?               残り局数の見積もり
  rule_version_id     UUID               使用するルールバージョン
  opponent_model_id   UUID               対戦相手モデル

### 6.2 入力検証

次のような不正な局面は計算前に拒否する。

-   手牌と副露の合計枚数が不正
-   同一物理牌の重複
-   5枚以上存在する牌種
-   既知の牌がルール上の総枚数を超過
-   座席・親・場風の不整合
-   現在の局面と矛盾する供託・本場
-   存在しないルールバージョン

エラーは、どの項目が不正なのかを特定できる形式で返す。

## 7. シャンテン数・受け入れ・打牌候補

### 7.1 シャンテン数

既存ライブラリの計算機能を利用する。対象は通常手、七対子、国士無双とする。

``` python
for discard in discard_candidates:
    next_hand = hand.remove(discard)

    result = shanten_calculator.calculate(
        hand=next_hand,
        melds=melds,
        rule=rule_profile,
    )
```

特殊ルールで牌の種類や構成が変わる場合は、既存ライブラリがその入力を正しく扱えるか確認する。

### 7.2 受け入れ枚数

``` json
{
  "discard": "3s",
  "shanten": 1,
  "ukeire": [
    {"tile_type": "2s", "remaining_count": 3},
    {"tile_type": "5s", "remaining_count": 2}
  ],
  "total_ukeire": 5
}
```

受け入れ枚数だけでなく、特殊牌の種類も区別する。同じ5sでも、通常牌・赤牌・青牌の残り枚数によって打点・チップへの影響が異なる。

### 7.3 打牌候補の評価

各打牌候補について、以下を算出する。

-   打牌後のシャンテン数
-   受け入れ枚数
-   有効牌の種類
-   次のツモによるシャンテン改善確率
-   聴牌到達確率
-   和了到達確率
-   和了時の打点分布
-   チップ獲得期待値
-   放銃リスク（局面情報がある場合）

最初は牌効率中心の評価を実装し、後から押し引き・順位期待値を追加する。

## 8. 役・ドラ・符・翻・点数計算

### 8.1 計算の流れ

``` mermaid
flowchart TD
    A["和了形の生成"] --> B["面子・雀頭の分解"]
    B --> C["成立役の判定"]
    C --> D["ドラ・赤牌・青牌の判定"]
    D --> E["翻数・符の計算"]
    E --> F["点数計算"]
    F --> G["支払い方法の計算"]
    G --> H["チップ精算情報の生成"]
```

### 8.2 既存ライブラリとの連携

MahjongRepository/mahjongに役・符・翻・点数の計算を委譲し、独自ルール部分はAdapter側で処理する。

``` python
class ScoreCalculator:
    def calculate(self, hand, win_tile, rule):
        normalized_hand = self.adapter.normalize(hand)

        result = self.adapter.calculate_standard_score(
            normalized_hand,
            rule,
        )

        custom_bonus = self.custom_yaku_calculator.calculate(
            hand,
            win_tile,
            rule,
        )

        return self.score_adjuster.apply(
            result,
            custom_bonus,
            rule,
        )
```

単純に翻数を後から足すだけでは不十分である。青牌がドラとして成立する条件、和了形への含有条件、ドラ表示牌との関係、満貫・跳満などの打点上限を含めて計算する。

既存ライブラリが返す計算結果と、独自拡張後の計算結果をテストで比較できるようにする。

## 9. 青牌・チップの評価

### 9.1 ドラ効果とチップ効果を分離する

  -------------------------------------------------------------------------------------
  要素                    内容                             評価方法
  ----------------------- -------------------------------- ----------------------------
  ドラ効果                和了時の翻数増加                 点数計算

  チップ効果              条件を満たした場合のチップ獲得   チップ獲得確率・枚数・精算

  牌効率への影響          青牌の残り枚数・受け入れ         受け入れ計算
  -------------------------------------------------------------------------------------

ドラ効果は和了打点を変化させ、チップ効果はチップ収支を変化させる。一つの「青牌の点数価値」にまとめると、局面や順位による価値の違いを表現できない。

### 9.2 チップ獲得モデル

``` python
@dataclass
class ChipRule:
    enabled: bool
    trigger: str
    chips_per_blue_tile: int
    settlement_mode: str
```

確定した獲得ルール：

- **トリガー**: 青牌を含む手での和了時（`AGARI_WITH_BLUE`）。副露した青牌も対象。ツモった時点では得ない。
- **獲得枚数**: 青牌1枚につき2チップ（`chips_per_blue_tile: 2`）。
- **支払い方**:
  - ロン和了: 放銃者が全チップを支払う。
  - ツモ和了: 他3人がそれぞれ全チップを支払う。

### 9.3 チップ精算モデル

**確定**: チップは順位計算とは別に精算する（`mode: SEPARATE`）。

- チップ精算額は点棒・順位点に影響しない。
- チップ1枚あたりの精算額（`chip_value`）はルール設定から変更可能。
- `Outcome` の `placement_points` と `chip_settlement` は必ず分けて保持し、二重計上を禁止する。

### 9.4 チップ期待値

チップ獲得枚数を確率分布で求める。

\[ E\[C `\mid `{=tex}a\] = `\sum`{=tex}\_k k `\cdot `{=tex}P(C=k
`\mid `{=tex}a) \]

-   (a)：候補打牌
-   (C)：最終的なチップ獲得枚数

和了率が高くても青牌を手牌に残せない選択なら、チップ期待値が低くなる場合がある。

### 9.5 「+2,000点」の扱い

仮にチップ1枚の精算価値が1,000点相当なら、2枚獲得は2,000点相当になる。ただし、これはチップ精算額であって、必ずしも点棒や順位点に直接加算するものではない。

``` python
@dataclass
class Outcome:
    final_scores: list[int]
    final_chips: list[int]
    placement_points: list[int]
    chip_settlement: list[int]
    final_ranks: list[int]
```

チップが順位に影響しないルールなら、順位点は最終点棒だけで計算する。チップが順位に影響するルールなら、チップを点棒に換算するタイミングを定義する。

同じチップ価値を点棒とチップ精算額の両方に加算する二重計上は禁止する。

## 10. 押し引き・放銃リスク・局収支

### 10.1 押し引き判断に必要な情報

-   自分の手牌
-   自分のシャンテン数
-   自分の和了確率
-   自分の和了打点分布
-   相手のリーチ状況
-   相手の副露状況
-   相手の河
-   相手の推定打点
-   相手の放銃待ち候補
-   点棒状況
-   局・本場・供託
-   親か子か
-   残り局数

### 10.2 放銃確率

放銃確率は相手の手牌を直接知ることができないため推定値となる。

初期段階では以下を利用する。

-   河に対する現物判定
-   スジ
-   壁・ノーチャンス
-   牌の見えている枚数
-   リーチ宣言後の巡目
-   相手の副露情報

その後、牌譜データが蓄積した段階で統計モデルや機械学習モデルに拡張する。

### 10.3 局単位の期待値

\[ EV\_{`\text{hand}`{=tex}}(a) = `\sum`{=tex}\_o P(o
`\mid `{=tex}a,s,r,m) `\cdot `{=tex}`\Delta `{=tex}S(o) \]

-   (a)：候補打牌
-   (s)：現在の局面
-   (r)：ルール
-   (m)：相手モデル
-   (o)：局の結果
-   (`\Delta `{=tex}S(o))：自分の点棒変動

これは局単位のEVであり、半荘全体の順位期待値とは異なる。

### 10.4 押し引きの比較

``` python
push_ev = evaluator.evaluate(
    action="PUSH",
    state=game_state,
)

fold_ev = evaluator.evaluate(
    action="FOLD",
    state=game_state,
)

best_action = max(
    [push_ev, fold_ev],
    key=lambda x: x.expected_utility,
)
```

押す・降りるの二択だけでなく、実際には複数の打牌候補を比較する。

## 11. 順位点・半荘全体の評価

### 11.1 順位点

順位点（オカ・ウマ）はルールプロファイルで設定可能にする。Mリーグ準拠のルールを初期値とし、変更できる構造にする。

``` json
{
  "scoring": {
    "oka": null,
    "uma": null
  }
}
```

`oka`・`uma` はルール設定から変更可能な数値。

### 11.2 順位評価

最終点棒から順位を算出する。**同点時は起家に近い席の順位が上**（`tie_break: "DEALER_ORDER"`）。

``` python
def calculate_ranks(final_scores, dealer_seat, tie_break_rule="DEALER_ORDER"):
    ...
```

**半荘終了条件**: Mリーグ準拠。**上がりやめ無し**（`last_round_win_stop: false`）。オーラストップ目が和了しても続行する。

### 11.3 半荘全体の目的関数

\[ U(o) = P\_{`\text{placement}`{=tex}}(o) +
C\_{`\text{settlement}`{=tex}}(o) \]

-   (P\_{`\text{placement}`{=tex}})：最終順位に応じた順位点
-   (C\_{`\text{settlement}`{=tex}})：チップの精算額

チップが順位計算に含まれるルールなら、順位を決める前にチップを点棒に反映する。その場合、順位点に加えてチップ精算額を二重計上しない。

### 11.4 局面による価値の変化

  ----------------------------------------------------------------------------------------
  状況                                評価上の傾向
  ----------------------------------- ----------------------------------------------------
  東場・点棒が横並び                  チップ収支の期待値を重視する場面がある

  南場・トップ目                      順位維持の価値が大きくなる

  オーラス・僅差の2着目               トップ逆転確率を重視する

  オーラス・ラス目                    順位上昇のためにリスクを取る価値が高まる場合がある

  オーラス・トップ目                  放銃による順位低下を避ける価値が大きい
  ----------------------------------------------------------------------------------------

青牌の価値に固定の重みを付けるのではなく、最終的な順位点・チップ精算額の期待値をシミュレーションすることで、結果として局面ごとの価値が変化する設計にする。

## 12. Monte Carloシミュレーション

### 12.1 目的

候補打牌ごとに、将来のツモ・相手の行動・局の結果を多数回シミュレーションし、期待値を推定する。

### 12.2 シミュレーションの流れ

``` mermaid
flowchart TD
    A["現在のGameState"] --> B["候補打牌を列挙"]
    B --> C["候補打牌を1つ選択"]
    C --> D["未知牌をサンプリング"]
    D --> E["相手の行動を生成"]
    E --> F["ツモ・打牌・副露を進行"]
    F --> G{"局終了？"}
    G -->|No| E
    G -->|Yes| H["点棒・チップ収支を計算"]
    H --> I{"半荘終了？"}
    I -->|No| D
    I -->|Yes| J["最終順位点を計算"]
    J --> K["期待値・分散・信頼区間を集計"]
```

### 12.3 シミュレーション結果の例

``` json
{
  "candidate": "3s",
  "simulation_count": 100000,
  "expected_placement_points": 12000,
  "expected_chip_settlement": 1800,
  "expected_utility": 13800,
  "win_probability": 0.28,
  "deal_in_probability": 0.07,
  "expected_final_rank": 1.85,
  "confidence_interval": {
    "lower": 13000,
    "upper": 14600
  }
}
```

数値は出力形式を示すための架空の例である。

### 12.4 対戦相手モデル

  モデル       内容
  ------------ --------------------------------
  Random       合法手からランダムに選択
  Basic        一般的な牌効率・押し引きルール
  Aggressive   攻撃的な押し引き
  Defensive    守備重視
  Custom       独自のパラメータ設定

将来的には実際の牌譜データを用いてモデルのパラメータを推定する。

### 12.5 不確実性の表示

シミュレーション結果は確定値ではない。次の情報を表示する。

-   シミュレーション回数
-   推定期待値
-   標準誤差
-   信頼区間
-   使用した相手モデル
-   ルールバージョン
-   モデルの仮定

異なる候補打牌の期待値差が小さい場合は、優劣を断定しない。

## 13. 期待値計算の統合ロジック

### 13.1 候補打牌の期待効用

\[ EV(a `\mid `{=tex}s,r,m) = `\sum`{=tex}\_o P(o
`\mid `{=tex}a,s,r,m)U(o) \]

-   (a)：候補打牌
-   (s)：現在の局面
-   (r)：ルールプロファイル
-   (m)：相手モデル
-   (o)：半荘終了までの結果
-   (U(o))：最終効用

### 13.2 擬似コード

``` python
def evaluate_discards(
    game_state,
    rule_profile,
    opponent_model,
    simulation_count,
):
    candidates = discard_generator.generate(game_state)
    results = []

    for candidate in candidates:
        next_state = game_state.discard(candidate)
        simulation_results = []

        for _ in range(simulation_count):
            outcome = match_simulator.run(
                state=next_state,
                rule=rule_profile,
                opponent_model=opponent_model,
            )

            utility = utility_calculator.calculate(
                outcome=outcome,
                rule=rule_profile,
            )
            simulation_results.append(utility)

        results.append(
            aggregate_results(
                candidate=candidate,
                values=simulation_results,
            )
        )

    return sorted(
        results,
        key=lambda x: x.expected_utility,
        reverse=True,
    )
```

実装時は同一の未知牌サンプルを候補間で共有するなど、比較時の分散を抑える工夫も検討する。

### 13.3 局単位と半荘単位の使い分け

  評価方式     用途
  ------------ ----------------------------------------
  局単位EV     牌効率・和了率・打点・放銃率の比較
  半荘単位EV   順位点・チップ・残り局数を含む総合判断

半荘全体のシミュレーションが重い場合は、局単位EVを先に表示し、必要な場合だけ半荘シミュレーションを実行する。

## 14. API設計

### 14.1 ルール関連

  Method   Endpoint                     内容
  -------- ---------------------------- ------------
  GET      `/api/rules`                 ルール一覧
  POST     `/api/rules`                 ルール作成
  GET      `/api/rules/{id}`            ルール取得
  PUT      `/api/rules/{id}`            ルール更新
  POST     `/api/rules/{id}/validate`   ルール検証

### 14.2 分析関連

  Method   Endpoint                    内容
  -------- --------------------------- ----------------
  POST     `/api/analysis/shanten`     シャンテン計算
  POST     `/api/analysis/ukeire`      受け入れ計算
  POST     `/api/analysis/scoring`     点数計算
  POST     `/api/analysis/discards`    打牌候補比較
  POST     `/api/analysis/push-fold`   押し引き評価
  POST     `/api/analysis/match-ev`    半荘期待値計算

### 14.3 AIコーチ関連

  Method   Endpoint                              内容
  -------- ------------------------------------- ----------------
  POST     `/api/coach/sessions`                 セッション作成
  POST     `/api/coach/sessions/{id}/messages`   質問・回答

### 14.4 打牌比較APIの例

Request:

``` json
{
  "game_state": {
    "hand": [
      "1m", "2m", "3m", "4m", "5m", "6m",
      "2p", "3p", "4p", "5s", "6s", "7s",
      "5z", "5z"
    ],
    "drawn_tile": "blue_5s",
    "scores": [35000, 30000, 20000, 15000],
    "round_wind": "south",
    "hand_number": 3
  },
  "rule_version_id": "00000000-0000-0000-0000-000000000001",
  "opponent_model_id": "basic",
  "analysis_mode": "match_ev",
  "simulation_count": 100000
}
```

Response:

``` json
{
  "analysis_id": "uuid",
  "engine_version": "1.0.0",
  "rule_version": 1,
  "analysis_mode": "match_ev",
  "candidates": [
    {
      "discard": "5s",
      "shanten": 1,
      "ukeire": 8,
      "expected_utility": 12000,
      "win_probability": 0.3,
      "deal_in_probability": 0.06,
      "expected_chip_settlement": 1000
    }
  ],
  "assumptions": [
    "opponent_model=basic",
    "simulation_count=100000"
  ]
}
```

これは形式例である。実際のAPIでは、牌の識別子や物理牌ID、座席情報などを厳密に定義する。

## 15. データモデル・バージョン管理

### 15.1 テーブル構成

  テーブル                    内容
  --------------------------- --------------------------
  `rule_profiles`             ルールの基本情報
  `rule_profile_versions`     ルール定義のバージョン
  `matches`                   半荘情報
  `rounds`                    局情報
  `game_states`               局面情報
  `analysis_sessions`         分析セッション
  `analysis_results`          計算結果
  `simulation_jobs`           シミュレーション実行情報
  `opponent_models`           対戦相手モデル
  `opponent_model_versions`   相手モデルのバージョン

### 15.2 ルールバージョン

ルールを変更した場合は既存バージョンを上書きせず、新しいバージョンを作成する。

``` text
rule_profiles
  └── rule_profile_versions
        ├── version 1
        ├── version 2
        └── version 3
```

分析結果には、使用した`rule_profile_version_id`を保存する。これにより過去の分析結果を同じルール条件で再現できる。

### 15.3 計算モデルのバージョン

ルールだけでなく、次のバージョンも記録する。

-   期待値計算エンジン
-   対戦相手モデル
-   既存ライブラリのバージョン
-   シミュレーション設定
-   乱数シード

## 16. 主要クラス・モジュール構成

``` text
mahjong_engine/
├── domain/
│   ├── tile.py
│   ├── hand.py
│   ├── meld.py
│   ├── game_state.py
│   ├── rule_profile.py
│   └── outcome.py
├── rules/
│   ├── rule_loader.py
│   ├── rule_validator.py
│   ├── dora_calculator.py
│   ├── chip_calculator.py
│   └── placement_calculator.py
├── adapters/
│   ├── base.py
│   └── mahjong_repository_adapter.py
├── efficiency/
│   ├── shanten_calculator.py
│   ├── ukeire_calculator.py
│   └── discard_generator.py
├── scoring/
│   ├── hand_divider.py
│   ├── yaku_calculator.py
│   ├── fu_calculator.py
│   └── score_calculator.py
├── defense/
│   ├── danger_calculator.py
│   └── push_fold_evaluator.py
├── simulation/
│   ├── wall_sampler.py
│   ├── opponent_model.py
│   ├── hand_simulator.py
│   ├── match_simulator.py
│   └── monte_carlo.py
├── evaluation/
│   ├── hand_ev.py
│   ├── match_ev.py
│   ├── utility_calculator.py
│   └── result_aggregator.py
└── tests/
    ├── test_tile.py
    ├── test_shanten.py
    ├── test_ukeire.py
    ├── test_scoring.py
    ├── test_chip.py
    ├── test_placement.py
    └── test_simulation.py
```

各モジュールは単体テスト可能な構造にする。

## 17. AIコーチとの連携

### 17.1 AIの役割

AIは計算エンジンの代わりに計算するのではなく、計算結果を解釈・説明する役割を持つ。

``` mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant E as Mahjong Engine
    participant L as LLM

    U->>API: この場面は何を切るべき？
    API->>E: 局面・ルールを渡す
    E-->>API: 候補・EV・リスク・根拠
    API->>L: 計算結果と質問を渡す
    L-->>API: 戦術的な説明
    API-->>U: 候補比較と説明
```

### 17.2 回答に含める情報

-   推奨打牌
-   次点候補
-   シャンテン・受け入れ
-   和了確率
-   打点期待値
-   放銃リスク
-   チップ期待値
-   順位点期待値
-   判断の根拠
-   使用したモデルと仮定

### 17.3 ユーザーが反論した場合

例えば「ここで發を切ると3s・6sの受け入れが消えるのでは？」と指摘された場合、AIは単に同意するのではなく、次の処理を行う。

1.  対象の打牌候補を再計算する。
2.  3s・6sの受け入れ枚数を取得する。
3.  他候補と比較する。
4.  先ほどの評価に誤りがあれば訂正する。
5.  判断が変わらない場合は、その理由を説明する。

## 18. テスト戦略

麻雀の計算エンジンでは、正しい結果を返すことが最も重要である。

### 18.1 単体テスト

  対象        検証内容
  ----------- ----------------------------
  Tile        牌種・物理牌・特殊牌の区別
  Shanten     既知の手牌のシャンテン数
  Ukeire      有効牌の種類・残り枚数
  Scoring     役・符・翻・点数
  Dora        通常ドラ・赤ドラ・青牌
  Chip        チップ獲得条件・枚数
  Placement   順位点・同点処理
  Utility     二重計上がないこと

### 18.2 既存ライブラリとの比較テスト

標準ルールにおいては、MahjongRepository/mahjongの計算結果と独自Adapterの結果が一致することを確認する。

独自ルールを適用した場合は、期待値を明示したテストケースを作成する。

### 18.3 特殊ルールテスト

最低限、次のケースを検証する。

-   青牌を含まない和了
-   青牌を1枚含む和了
-   青牌を複数枚含む和了
-   青牌がドラ表示牌に関係するケース
-   赤牌と青牌を同時に含む和了
-   青牌をツモったが和了しなかったケース
-   青牌を副露に含めたケース
-   青牌を捨てたケース
-   青牌が残り0枚になったケース

### 18.4 シミュレーションテスト

-   同じ乱数シードで同じ結果になること。
-   試行回数を増やした場合に推定値が安定すること。
-   既知牌を重複して抽選しないこと。
-   牌山の総枚数が正しいこと。
-   点棒・チップの収支計算が正しいこと。
-   全プレイヤーの結果を合計した収支がルール上整合すること。

## 19. 性能要件

初期段階では以下を暫定目標とする。

  処理                     目標
  ------------------------ ------------
  シャンテン計算           100ms以内
  受け入れ計算             200ms以内
  点数計算                 100ms以内
  打牌候補比較（局単位）   2秒以内
  半荘シミュレーション     非同期実行
  分析履歴取得             500ms以内

これらは設計上の目標値であり、実際の性能保証ではない。

### 19.1 高速化方針

-   牌種カウントのキャッシュ
-   同一局面の計算結果キャッシュ
-   ルールバージョン単位のキャッシュ
-   Monte Carloの並列化
-   シミュレーションの非同期実行
-   候補間での乱数サンプル共有
-   計算途中の進捗管理

試行回数を増やすほど精度は改善しやすいが、計算時間も増加する。少ない試行回数で暫定結果を出し、追加計算で精度を上げる方式も検討する。

## 20. 段階的な実装計画・工数見積もり

1人で実装する場合の概算。既存ライブラリの検証・改修量や独自ルールの複雑さによって変動する。

  フェーズ   内容                                 概算工数
  ---------- -------------------------------- ------------
  1          既存ライブラリ調査・技術検証         3〜5人日
  2          ドメインモデル・ルール管理           5〜8人日
  3          シャンテン・受け入れ・打牌候補       5〜8人日
  4          役・点数・特殊牌対応                5〜10人日
  5          チップ・局単位EV                     5〜8人日
  6          押し引き・放銃リスク                8〜15人日
  7          半荘シミュレーション               10〜20人日
  8          順位期待値・総合評価                5〜10人日
  9          AIコーチ連携                         3〜7人日
  10         テスト・性能改善                    5〜10人日

**概算合計：54〜101人日。**
フロントエンド・認証・運用基盤などの通常のWebアプリ開発工数は含まない。

### 推奨する開発順序

**Phase 1：既存ライブラリを使った基盤** -
MahjongRepository/mahjongの導入 - 手牌入力 - シャンテン数 - 受け入れ -
役・点数計算

**Phase 2：独自ルール対応** - 赤牌・青牌 - ドラ計算 - チップ計算 -
ルールプロファイル管理

**Phase 3：局単位の期待値** - 和了確率 - 打点期待値 - チップ期待値 -
放銃リスク - 押し引き

**Phase 4：半荘全体の期待値** - 順位点 - 残り局数 -
半荘シミュレーション - 最終順位期待値

**Phase 5：AIコーチ** - 計算結果の自然言語説明 - ユーザーとの壁打ち -
指摘された候補の再計算 - 戦術的な根拠の提示

## 21. 仕様確定一覧

  No.   確認事項                             確定内容
  ----- ------------------------------------ -----------------------------------------------------
  1     青牌は何枚存在するか                 各スート1枚（設定で0枚に変更可能）
  2     青牌は通常のドラとして何翻扱いか     1翻
  3     青牌を含む和了で一律2チップか        青牌1枚につき2チップ（一律ではなく枚数比例）
  4     青牌1枚につき2チップか               確定：青牌1枚につき2チップ
  5     青牌をツモった時点でチップを得るか   和了時のみ（ツモった時点では得ない）
  6     青牌を副露した場合もチップ対象か     対象
  7     チップは誰が誰に支払うか             ロン：放銃者が全額 / ツモ：他3人がそれぞれ全額
  8     チップ1枚の精算額                    設定から変更可能
  9     チップ精算は順位計算に含むか         含まない（別精算）
  10    順位点の体系                         オカ・ウマどちらも設定から変更可能
  11    同点時の順位決定方法                 起家に近い席の順位が上
  12    オカ・ウマの体系                     設定から変更可能
  13    半荘終了条件・延長条件               Mリーグ準拠・上がりやめ無し
  14    相手モデルの初期設定                 要確認
  15    分析対象は四人麻雀のみか             要確認

## 22. 最終的な推奨設計

今回のアプリでは、最初から独自の麻雀エンジンをすべて作る必要はない。

推奨構成：

1.  **MahjongRepository/mahjong**：シャンテン・和了判定・役・符・翻・点数計算
2.  **独自ドメインエンジン**：青牌・赤牌・チップ・独自ルール・牌の物理的な管理
3.  **独自期待値エンジン**：和了確率・放銃確率・局収支・順位点・半荘シミュレーション
4.  **AIコーチ**：計算結果の解釈・戦術説明・再計算による壁打ち

最も重要なのは、既存ライブラリで計算できる部分と、独自ルール・独自戦術として実装する部分の境界を明確にすることである。

特に、順位点・チップ・半荘全体の期待値は、一般的なシャンテン計算ライブラリだけでは実現できない。ここを独自実装の中心に据えることで、競技麻雀向けの分析ツールに発展させられる。

## 参考資料

-   [MahjongRepository/mahjong](https://github.com/MahjongRepository/mahjong)
    --- [APIドキュメント](https://mahjongrepository.github.io/mahjong/)
-   [nekobean/mahjong-cpp](https://github.com/nekobean/mahjong-cpp)
-   [Mortal](https://github.com/Equim-chan/Mortal) ---
    [公式ドキュメント](https://mortal.ekyu.moe/)
-   [Riichi Advanced](https://github.com/EpicOrange/riichi_advanced)

**仕様書の結論：**
まずMahjongRepository/mahjongを実際に動かし、独自ルールを含まない標準ルールで計算結果を検証する。そのうえで青牌・チップ・順位点を段階的に追加する進め方を推奨する。
