const BASE = "https://achrafjarrou-themis.hf.space"

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, opts)
  if (!r.ok) throw new Error(r.status + " " + (await r.text().catch(() => "")))
  return r.json()
}

export const api = {
  analyze: (form: FormData) =>
    req<{ session_id: string; status: string; estimated_minutes: number }>(
      "/analyze", { method: "POST", body: form }
    ),
  session: (sid: string) => req<import("../types").SessionData>(`/sessions/${sid}`),
  report:  (sid: string) => req<import("../types").ComplianceReport>(`/sessions/${sid}/report`),
  health:  ()            => req<{ status: string }>("/health"),
}
