// AI-assisted: Milestone 5 completion API client.

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export interface CompletionPayload {
  musicXml: string
  targetPart?: string
  style?: string
}

export interface CompletionResult {
  success: boolean
  music_xml?: string | null
  warnings: string[]
  error?: string | null
}

export async function fetchCompletionStatus(): Promise<boolean> {
  const response = await fetch(`${API_BASE}/api/completion/status`)
  if (!response.ok) {
    return false
  }

  const payload = (await response.json()) as { enabled?: boolean }
  return Boolean(payload.enabled)
}

export async function suggestHarmony(payload: CompletionPayload): Promise<CompletionResult> {
  const response = await fetch(`${API_BASE}/api/completion/suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      music_xml: payload.musicXml,
      target_part: payload.targetPart ?? 'Bass',
      style: payload.style ?? 'simple_roots',
    }),
  })

  if (response.status === 403) {
    throw new Error('AI completion is disabled on the server. Set ENABLE_AI_COMPLETION=true.')
  }

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(errorPayload?.detail ?? 'Completion request failed.')
  }

  return response.json() as Promise<CompletionResult>
}
