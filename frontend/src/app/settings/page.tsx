"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

type LLMProvider = "ollama" | "claude"

interface SystemSettings {
  llm_provider: LLMProvider
}

export default function SettingsPage() {
  const [provider, setProvider] = useState<LLMProvider>("ollama")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${BASE_URL}/api/settings`)
      .then((r) => r.json())
      .then((d: SystemSettings) => setProvider(d.llm_provider))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleSave = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const res = await fetch(`${BASE_URL}/api/settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ llm_provider: provider }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setMessage("保存しました")
    } catch (e) {
      setMessage(`エラー: ${(e as Error).message}`)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="text-gray-500 text-sm">読み込み中...</p>

  return (
    <div>
      <h2 className="text-xl font-semibold text-gray-900 mb-6">システム設定</h2>
      <Card title="LLMプロバイダー">
        <div className="space-y-3">
          {(["ollama", "claude"] as const).map((p) => (
            <label key={p} className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="provider"
                value={p}
                checked={provider === p}
                onChange={() => setProvider(p)}
                className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                {p === "ollama" ? "Ollama（ローカル）" : "Claude API（Anthropic）"}
              </span>
            </label>
          ))}
          <p className="text-xs text-gray-400 mt-2">
            APIキーの設定は .env ファイルで管理します
          </p>
        </div>
        <div className="mt-4 flex items-center gap-4">
          <Button onClick={handleSave} loading={saving}>
            保存
          </Button>
          {message && (
            <p
              className={`text-sm ${
                message.startsWith("エラー") ? "text-red-600" : "text-green-600"
              }`}
            >
              {message}
            </p>
          )}
        </div>
      </Card>
    </div>
  )
}
