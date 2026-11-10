import Link from "next/link"
import { ReactNode } from "react"

export default function AnalysisLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-6">
          <h1 className="text-lg font-bold text-gray-900">局面分析</h1>
          <nav className="flex gap-4">
            <Link
              href="/analysis"
              className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
            >
              局面入力
            </Link>
            <Link
              href="/history"
              className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
            >
              履歴
            </Link>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">{children}</main>
    </div>
  )
}
