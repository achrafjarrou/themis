import type { CSSProperties, ReactNode } from "react"

export function Card({ children, style, className }: {
  children: ReactNode
  style?: CSSProperties
  className?: string
}) {
  return (
    <div className={className} style={{
      background:"var(--bg2)",
      border:"1px solid var(--border2)",
      borderRadius:14,
      ...style
    }}>
      {children}
    </div>
  )
}