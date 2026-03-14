export function Skeleton({ h = 16, w = "100%", r = 6 }: { h?:number; w?:number|string; r?:number }) {
  return (
    <div style={{
      height:h, width:w, borderRadius:r,
      background:"linear-gradient(90deg, var(--border) 25%, var(--border2) 50%, var(--border) 75%)",
      backgroundSize:"200% 100%",
      animation:"shimmer 1.5s infinite",
    }} />
  )
}