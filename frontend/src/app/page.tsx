import Link from "next/link"

const menuItems = [
  {
    href: "/analysis",
    title: "局面分析",
    description: "手牌・ツモ牌を入力して打牌候補・期待値を分析します。",
    icon: "🀄",
  },
  {
    href: "/history",
    title: "分析履歴",
    description: "過去に実行した局面分析の結果を確認します。",
    icon: "📋",
  },
  {
    href: "/settings",
    title: "設定",
    description: "ルールプロファイルの管理やシステム設定を行います。",
    icon: "⚙️",
  },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">MJ Coach</h1>
          <p className="text-sm text-gray-500 mt-0.5">麻雀戦略コーチングツール</p>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {menuItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="bg-white border border-gray-200 rounded-lg shadow-sm p-6 flex flex-col gap-3 hover:shadow-md hover:border-blue-300 transition-all"
            >
              <div className="text-3xl">{item.icon}</div>
              <div>
                <h2 className="text-base font-semibold text-gray-900">{item.title}</h2>
                <p className="text-sm text-gray-500 mt-1 leading-relaxed">{item.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  )
}
