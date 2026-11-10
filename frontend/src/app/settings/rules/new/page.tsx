"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { RuleForm } from "@/components/rules/RuleForm"
import { rulesApi } from "@/lib/api"
import { RuleDefinition } from "@/types/rule"

export default function NewRulePage() {
  const router = useRouter()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async (
    name: string,
    description: string | null,
    definition: RuleDefinition
  ) => {
    setSaving(true)
    setError(null)
    try {
      await rulesApi.create(name, description, definition)
      router.push("/settings/rules")
    } catch (e) {
      setError((e as Error).message)
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link href="/settings/rules" className="text-sm text-gray-500 hover:text-gray-700">
          ← ルール管理
        </Link>
        <h2 className="text-xl font-semibold text-gray-900">ルール新規作成</h2>
      </div>
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-700">
          {error}
        </div>
      )}
      <RuleForm onSave={handleSave} saving={saving} />
    </div>
  )
}
