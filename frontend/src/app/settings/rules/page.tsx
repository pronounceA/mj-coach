"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/Button"
import { rulesApi } from "@/lib/api"
import { RuleProfile } from "@/types/rule"

export default function RulesPage() {
  const [rules, setRules] = useState<RuleProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      setRules(await rulesApi.list())
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`「${name}」を削除しますか？この操作は元に戻せません。`)) return
    setDeleting(id)
    try {
      await rulesApi.delete(id)
      setRules((prev) => prev.filter((r) => r.id !== id))
    } catch (e) {
      alert((e as Error).message)
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">ルール管理</h2>
        <Link href="/settings/rules/new">
          <Button>新規作成</Button>
        </Link>
      </div>

      {loading && <p className="text-sm text-gray-500">読み込み中...</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {!loading && !error && rules.length === 0 && (
        <div className="text-center py-16 text-gray-400 border border-dashed border-gray-300 rounded-lg">
          <p className="text-sm">ルールプロファイルがありません</p>
          <p className="text-xs mt-1">「新規作成」ボタンから作成してください</p>
        </div>
      )}

      {rules.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ルール名
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  バージョン
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最終更新日
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-gray-900">{rule.name}</p>
                    {rule.description && (
                      <p className="text-xs text-gray-500 mt-0.5">{rule.description}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    v{rule.latest_version?.version ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {new Date(rule.updated_at).toLocaleDateString("ja-JP")}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link href={`/settings/rules/${rule.id}`}>
                        <Button variant="secondary" className="text-xs px-3 py-1.5">
                          編集
                        </Button>
                      </Link>
                      <Button
                        variant="danger"
                        className="text-xs px-3 py-1.5"
                        loading={deleting === rule.id}
                        onClick={() => handleDelete(rule.id, rule.name)}
                      >
                        削除
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
