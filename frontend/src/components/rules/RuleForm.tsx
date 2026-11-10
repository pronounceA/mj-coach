"use client"

import { useState } from "react"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Select } from "@/components/ui/Select"
import { Card } from "@/components/ui/Card"
import { RuleDefinition, DEFAULT_RULE_DEFINITION } from "@/types/rule"
import { rulesApi } from "@/lib/api"

interface RuleFormProps {
  initialName?: string
  initialDescription?: string
  initialDefinition?: RuleDefinition
  ruleId?: string
  onSave: (name: string, description: string | null, definition: RuleDefinition) => Promise<void>
  saving?: boolean
}

export function RuleForm({
  initialName = "",
  initialDescription = "",
  initialDefinition = DEFAULT_RULE_DEFINITION,
  ruleId,
  onSave,
  saving = false,
}: RuleFormProps) {
  const [name, setName] = useState(initialName)
  const [description, setDescription] = useState(initialDescription)
  const [definition, setDefinition] = useState<RuleDefinition>(initialDefinition)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<{ valid: boolean; errors: string[] } | null>(null)

  const setDef = (patch: Partial<RuleDefinition>) =>
    setDefinition((prev) => ({ ...prev, ...patch }))

  const handleValidate = async () => {
    if (!ruleId) return
    setValidating(true)
    setValidationResult(null)
    try {
      const result = await rulesApi.validate(ruleId)
      setValidationResult(result)
    } catch (e) {
      setValidationResult({ valid: false, errors: [(e as Error).message] })
    } finally {
      setValidating(false)
    }
  }

  const handleSave = () => {
    onSave(name, description || null, definition)
  }

  return (
    <div className="space-y-6">
      {/* 基本情報 */}
      <Card title="基本情報">
        <div className="space-y-4">
          <Input
            id="name"
            label="ルール名"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="例: 標準ルール"
            required
          />
          <Input
            id="description"
            label="説明"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="任意"
          />
        </div>
      </Card>

      {/* 牌設定 */}
      <Card title="牌設定">
        <div className="space-y-4">
          <p className="text-sm font-medium text-gray-700">赤牌</p>
          <div className="grid grid-cols-2 gap-4">
            <Input
              id="red_count"
              label="枚数/スート"
              type="number"
              min={0}
              max={4}
              value={definition.red_tile.count_per_suit}
              onChange={(e) =>
                setDef({ red_tile: { ...definition.red_tile, count_per_suit: Number(e.target.value) } })
              }
            />
            <Input
              id="red_han"
              label="翻数"
              type="number"
              min={1}
              value={definition.red_tile.han}
              onChange={(e) =>
                setDef({ red_tile: { ...definition.red_tile, han: Number(e.target.value) } })
              }
            />
          </div>

          <p className="text-sm font-medium text-gray-700 pt-2">青牌</p>
          <div className="grid grid-cols-2 gap-4">
            <Input
              id="blue_count"
              label="枚数/スート"
              type="number"
              min={0}
              max={1}
              value={definition.blue_tile.count_per_suit}
              onChange={(e) =>
                setDef({ blue_tile: { ...definition.blue_tile, count_per_suit: Number(e.target.value) } })
              }
            />
            <Input
              id="blue_han"
              label="翻数"
              type="number"
              min={1}
              value={definition.blue_tile.han}
              onChange={(e) =>
                setDef({ blue_tile: { ...definition.blue_tile, han: Number(e.target.value) } })
              }
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="chip_enabled"
              type="checkbox"
              checked={definition.blue_tile.chip_enabled}
              onChange={(e) =>
                setDef({ blue_tile: { ...definition.blue_tile, chip_enabled: e.target.checked } })
              }
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="chip_enabled" className="text-sm text-gray-700">
              チップを有効にする
            </label>
          </div>
        </div>
      </Card>

      {/* チップ設定 */}
      {definition.blue_tile.chip_enabled && (
        <Card title="チップ設定">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Input
                id="chips_per_blue"
                label="チップ数/青牌"
                type="number"
                min={1}
                value={definition.blue_tile.chips_per_blue_tile}
                onChange={(e) =>
                  setDef({
                    blue_tile: { ...definition.blue_tile, chips_per_blue_tile: Number(e.target.value) },
                  })
                }
              />
              <Input
                id="chip_value"
                label="1チップの精算額"
                type="number"
                min={0}
                value={definition.chip_settlement.chip_value ?? ""}
                placeholder="未設定"
                onChange={(e) => {
                  const v = e.target.value
                  setDef({
                    chip_settlement: {
                      ...definition.chip_settlement,
                      chip_value: v === "" ? null : Number(v),
                    },
                  })
                }}
              />
            </div>
            <Select
              id="chip_trigger"
              label="チップ取得トリガー"
              value={definition.blue_tile.chip_trigger}
              onChange={(e) =>
                setDef({ blue_tile: { ...definition.blue_tile, chip_trigger: e.target.value } })
              }
              options={[
                { value: "AGARI_WITH_BLUE", label: "青牌を含む手での和了" },
                { value: "PER_BLUE_TILE", label: "青牌1枚につき" },
                { value: "DRAW_BLUE", label: "青牌のツモ時" },
              ]}
            />
            <div className="grid grid-cols-2 gap-4">
              <Select
                id="chip_payer_ron"
                label="支払い（ロン）"
                value={definition.blue_tile.chip_payer.ron}
                onChange={(e) =>
                  setDef({
                    blue_tile: {
                      ...definition.blue_tile,
                      chip_payer: { ...definition.blue_tile.chip_payer, ron: e.target.value },
                    },
                  })
                }
                options={[
                  { value: "DEAL_IN_PLAYER", label: "放銃者のみ" },
                  { value: "ALL_OPPONENTS", label: "全対戦相手" },
                ]}
              />
              <Select
                id="chip_payer_tsumo"
                label="支払い（ツモ）"
                value={definition.blue_tile.chip_payer.tsumo}
                onChange={(e) =>
                  setDef({
                    blue_tile: {
                      ...definition.blue_tile,
                      chip_payer: { ...definition.blue_tile.chip_payer, tsumo: e.target.value },
                    },
                  })
                }
                options={[
                  { value: "ALL_OPPONENTS", label: "全対戦相手" },
                  { value: "DEAL_IN_PLAYER", label: "特定プレイヤー" },
                ]}
              />
            </div>
          </div>
        </Card>
      )}

      {/* 順位点設定 */}
      <Card title="順位点設定">
        <div className="space-y-4">
          <Input
            id="oka"
            label="オカ"
            type="number"
            value={definition.scoring.oka ?? ""}
            placeholder="未設定"
            onChange={(e) => {
              const v = e.target.value
              setDef({ scoring: { ...definition.scoring, oka: v === "" ? null : Number(v) } })
            }}
          />
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2">ウマ</p>
            <div className="grid grid-cols-4 gap-2">
              {(["first", "second", "third", "fourth"] as const).map((place, i) => (
                <Input
                  key={place}
                  id={`uma_${place}`}
                  label={`${i + 1}位`}
                  type="number"
                  value={definition.scoring.uma[place]}
                  onChange={(e) =>
                    setDef({
                      scoring: {
                        ...definition.scoring,
                        uma: { ...definition.scoring.uma, [place]: Number(e.target.value) },
                      },
                    })
                  }
                />
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* ルール設定 */}
      <Card title="ルール設定">
        <div className="space-y-4">
          <Select
            id="tie_break"
            label="同点処理"
            value={definition.scoring.tie_break}
            onChange={(e) =>
              setDef({ scoring: { ...definition.scoring, tie_break: e.target.value } })
            }
            options={[{ value: "DEALER_ORDER", label: "起家に近い順" }]}
          />
          <div className="flex items-center gap-2">
            <input
              id="last_round_win_stop"
              type="checkbox"
              checked={definition.scoring.last_round_win_stop}
              onChange={(e) =>
                setDef({ scoring: { ...definition.scoring, last_round_win_stop: e.target.checked } })
              }
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="last_round_win_stop" className="text-sm text-gray-700">
              上がりやめあり（最終局）
            </label>
          </div>
        </div>
      </Card>

      {/* バリデーション結果 */}
      {validationResult && (
        <div
          className={`rounded-md p-4 ${
            validationResult.valid
              ? "bg-green-50 border border-green-200"
              : "bg-red-50 border border-red-200"
          }`}
        >
          {validationResult.valid ? (
            <p className="text-sm text-green-700 font-medium">
              バリデーション成功: ルール定義は有効です
            </p>
          ) : (
            <div>
              <p className="text-sm text-red-700 font-medium mb-2">バリデーションエラー:</p>
              <ul className="list-disc list-inside space-y-1">
                {validationResult.errors.map((err, i) => (
                  <li key={i} className="text-sm text-red-600">
                    {err}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* アクション */}
      <div className="flex gap-3">
        {ruleId && (
          <Button
            variant="secondary"
            onClick={handleValidate}
            loading={validating}
            disabled={saving}
          >
            バリデーション実行
          </Button>
        )}
        <Button onClick={handleSave} loading={saving} disabled={validating || !name.trim()}>
          保存
        </Button>
      </div>
    </div>
  )
}
