import { ReactNode } from "react"

interface CardProps {
  title?: string
  children: ReactNode
  className?: string
}

export function Card({ title, children, className = "" }: CardProps) {
  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {title && (
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  )
}
