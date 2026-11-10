"use client"

export const dynamic = "force-dynamic"

import { useEffect, useState } from "react"
import { useRouter, useParams } from "next/navigation"
import Link from "next/link"
import { RuleForm } from "@/components/rules/RuleForm"
import { rulesApi } from "@/lib/api"
import { RuleProfile, RuleDefinition } from "@/types/rule"

export default function EditRulePage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const [rule, setRule] = useState<RuleProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [fetchError, setFetchError] = useState<string | null>(null)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => {
    rulesApi
      .get(id)
      .then(setRule)
      .catch((e) => setFetchError((e as Error).message))
      .finally(() => setLoading(false))
  }, [id])

  const handleSave = async (
    name: string,
    description: string | null,
    definition: RuleDefinition
  ) => {
    setSaving(true)
    setSaveError(null)
    try {
      await rulesApi.update(id, {
        name,
        description: description ?? undefined,
        definition,
      })
      router.push("/settings/rules")
    } catch (e) {
      setSaveError((e as Error).message)
      setSaving(false)
    }
  }

  if (loading) return <p className="text-sm text-gray-500">読み込み中...</p>
  if (fetchError) return <p className="text-sm text-red-600">{fetchError}</p>
  if (!rule) return null

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/settings/rules" className="text-sm text-gray-500 hover:text-gray-700">
          ← ルール管理
        </Link>
        <h2 className="text-xl font-semibold text-gray-900">ルール編集: {rule.name}</h2>
      </div>

      {rule.latest_version && (
        <div className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-700">
          現在 v{rule.latest_version.version} — 保存すると新しいバージョンとして作成されます
        </div>
      )}

      {saveError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {saveError}
        </div>
      )}

      <RuleForm
        initialName={rule.name}
        initialDescription={rule.description ?? ""}
        initialDefinition={rule.latest_version?.definition}
        ruleId={id}
        onSave={handleSave}
        saving={saving}
      />
    </div>
  )
}
