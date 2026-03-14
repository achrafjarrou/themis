export function fmt(s: number) {
  return s < 60 ? `${s}s` : `${Math.floor(s/60)}m ${s%60}s`
}
export function scoreColor(s: number) {
  return s >= 75 ? "#10b981" : s >= 50 ? "#f59e0b" : "#ef4444"
}
export function scoreLabel(s: number) {
  return s >= 75 ? "COMPLIANT" : s >= 50 ? "PARTIAL" : "NON-COMPLIANT"
}
export function riskColor(r: string) {
  const m: Record<string,string> = {
    unacceptable:"#ef4444", high:"#f97316",
    limited:"#f59e0b", minimal:"#10b981",
    gpai:"#8b5cf6", unknown:"#64748b"
  }
  return m[r] ?? "#64748b"
}
export function clsx(...c: (string|undefined|false|null)[]) {
  return c.filter(Boolean).join(" ")
}