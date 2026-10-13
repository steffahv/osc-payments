/** Same-origin API proxy; authentication cookies stay inaccessible to JavaScript. */
export const sessionEvents = new EventTarget()

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message)
    this.name = "ApiError"
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(15000)
  const response = await fetch(`/api/v1${path}`, {
    ...options,
    signal: options.signal ? AbortSignal.any([options.signal, timeout]) : timeout,
    credentials: "include",
    cache: "no-store",
  })
  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/login") {
      sessionEvents.dispatchEvent(new Event("expired"))
    }
    const message = response.status === 401 ? "You must sign in" :
      response.status === 403 ? "You do not have permission to perform this action" :
      "Unable to complete the request"
    throw new ApiError(response.status, message)
  }
  return response.status === 204 ? undefined as T : response.json() as Promise<T>
}

export function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  return apiRequest<T>(path, { signal })
}

export function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    ...(body === undefined ? {} : {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  })
}
