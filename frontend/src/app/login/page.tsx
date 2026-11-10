"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Input } from "@/components/ui/Input"
import { Button } from "@/components/ui/Button"
import { Card } from "@/components/ui/Card"

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    // Simulate a brief loading state before redirect
    await new Promise((resolve) => setTimeout(resolve, 800))
    router.push("/analysis")
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">麻雀コーチ</h1>
          <p className="text-sm text-gray-500 mt-1">局面分析ツール</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <Input
              id="email"
              label="メールアドレス"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@example.com"
              autoComplete="email"
            />
            <Input
              id="password"
              label="パスワード"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="パスワードを入力"
              autoComplete="current-password"
            />
            <Button type="submit" loading={loading} className="w-full mt-2">
              ログイン
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-gray-400 mt-4">
          ログイン機能は開発中です
        </p>
      </div>
    </div>
  )
}
