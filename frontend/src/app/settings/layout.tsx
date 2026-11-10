import Link from "next/link"
import { ReactNode } from "react"

export default function SettingsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-6">
          <Link href="/" className="text-sm text-gray-500 hover:text-gray-700">
            ← ホーム
          </Link>
          <h1 className="text-base font-semibold text-gray-900">設定</h1>
          <nav className="flex gap-4 ml-4">
            <Link href="/settings" className="text-sm text-gray-600 hover:text-blue-600">
              システム設定
            </Link>
            <Link href="/settings/rules" className="text-sm text-gray-600 hover:text-blue-600">
              ルール管理
            </Link>
          </nav>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
    </div>
  )
}
