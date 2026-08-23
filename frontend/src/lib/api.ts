export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"

export async function fetchCompanies() {
  const res = await fetch(`${API_BASE}/companies`)
  return res.json()
}

export async function fetchCompany(id: string) {
  const res = await fetch(`${API_BASE}/companies/${id}`)
  return res.json()
}

export async function fetchGenome(companyId: string) {
  const res = await fetch(`${API_BASE}/companies/${companyId}/genome`)
  return res.json()
}

export async function fetchMutations(companyId: string) {
  const res = await fetch(`${API_BASE}/companies/${companyId}/mutations`)
  return res.json()
}

export async function fetchAgentRuns(companyId: string) {
  const res = await fetch(`${API_BASE}/companies/${companyId}/agent/runs`)
  return res.json()
}

export async function fetchAgentEvents(runId: string) {
  const res = await fetch(`${API_BASE}/agent/runs/${runId}/events`)
  return res.json()
}

export async function fetchScrapers(companyId: string) {
  const res = await fetch(`${API_BASE}/companies/${companyId}/scrapers`)
  return res.json()
}

export async function triggerSequence(companyId: string) {
  const res = await fetch(`${API_BASE}/companies/${companyId}/sequence`, { method: "POST" })
  if (!res.ok) throw new Error(`Failed to start sequence (${res.status})`)
  return res.json()
}

export async function fetchSequenceStatus(companyId: string, jobId: string) {
  const res = await fetch(`${API_BASE}/companies/${companyId}/sequence/${jobId}`)
  if (!res.ok) throw new Error(`Failed to fetch sequence status (${res.status})`)
  return res.json()
}

export async function createCompany(name: string) {
  const res = await fetch(`${API_BASE}/companies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  })
  if (!res.ok) throw new Error(`Failed to create company (${res.status})`)
  return res.json()
}
