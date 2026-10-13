/** Shared transport. Future sessions will use HttpOnly cookies. */
export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message)
    this.name = "ApiError"
  }
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { credentials: "same-origin", signal })
  if (!response.ok) {
    const message = response.status === 401 ? "You must sign in" :
      response.status === 403 ? "You do not have permission to perform this action" :
      "Unable to complete the request"
    throw new ApiError(response.status, message)
  }
  return response.json() as Promise<T>
}
