export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function errorMessage(body: unknown): string {
  if (typeof body === "object" && body !== null) {
    const value = body as Record<string, unknown>;
    for (const key of ["detail", "message", "error"]) {
      if (typeof value[key] === "string") return value[key];
    }
  }
  return "Request failed";
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const body: unknown = await response.json();
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${errorMessage(body)}`);
  }
  return body as T;
}
