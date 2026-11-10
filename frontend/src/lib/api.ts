import { RuleDefinition, RuleProfile } from "@/types/rule"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const rulesApi = {
  list: () => request<RuleProfile[]>("/api/rules"),

  get: (id: string) => request<RuleProfile>(`/api/rules/${id}`),

  create: (name: string, description: string | null, definition: RuleDefinition) =>
    request<RuleProfile>("/api/rules", {
      method: "POST",
      body: JSON.stringify({ name, description, definition }),
    }),

  update: (id: string, data: { name?: string; description?: string; definition?: RuleDefinition }) =>
    request<RuleProfile>(`/api/rules/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  validate: (id: string) =>
    request<{ valid: boolean; errors: string[] }>(`/api/rules/${id}/validate`, {
      method: "POST",
    }),

  delete: (id: string) =>
    request<void>(`/api/rules/${id}`, { method: "DELETE" }),
}
