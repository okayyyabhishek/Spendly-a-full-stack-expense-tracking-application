const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api/v1'

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface ApiRequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  authenticated?: boolean
}

function getAccessToken(): string | null {
  return localStorage.getItem('pulse_ledger_token')
}

async function request(path: string, options: ApiRequestOptions = {}): Promise<Response> {
  const { body, authenticated = true, headers, ...requestOptions } = options
  const token = authenticated ? getAccessToken() : null
  const isFormData = body instanceof FormData
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestOptions,
    headers: {
      Accept: 'application/json',
      ...(body !== undefined && !isFormData ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    body: body === undefined ? undefined : isFormData ? body : JSON.stringify(body),
  })

  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null)
    const message =
      typeof payload === 'object' && payload !== null && 'error' in payload
        ? String((payload as { error?: { message?: string } }).error?.message ?? 'Request failed.')
        : 'Request failed. Please try again.'
    if (response.status === 401 && authenticated) {
      localStorage.removeItem('pulse_ledger_token')
      localStorage.removeItem('pulse_ledger_user')
    }
    throw new ApiError(message, response.status)
  }
  return response
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await request(path, options)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function apiDownload(path: string): Promise<Blob> {
  return (await request(path)).blob()
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const response = await request(path, options)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}
