// AI-assisted: Milestone 3 score fetch client.

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function fetchJobScore(jobId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/jobs/${jobId}/score`)

  if (response.status === 400) {
    throw new Error('Score is not ready yet — job still processing.')
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null
    throw new Error(payload?.detail ?? 'Could not fetch score.')
  }

  return response.text()
}
