const BASE = "https://achrafjarrou-themis.hf.space"

async function wakeUp() {
  try { await fetch(BASE + "/health") } catch {}
  await new Promise(r => setTimeout(r, 3000))
}

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, opts)
  if (!r.ok) throw new Error(r.status + " " + (await r.text().catch(() => "")))
  return r.json()
}

export const api = {
  analyze: async (form: FormData) => {
    await wakeUp()
    return req<{session_id:string}>("/analyze", { method:"POST", body:form })
  },
  report:  (sid: string) => req<any>("/sessions/" + sid + "/report"),
  session: (sid: string) => req<any>("/sessions/" + sid),
  health:  () => req<any>("/health"),
}
