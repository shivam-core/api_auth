let accessToken: string | null = null;

export function setAccessToken(value: string | null) {
  accessToken = value;
}

export function getAccessToken() {
    return accessToken;
}

export async function api<T>(
  path: string,
  init: RequestInit = {},
  tokenOverride?: string | null,
): Promise<T> {
  if (!path.startsWith("/api/") || path.includes("://")) {
    throw new Error("Only local API routes are permitted");
  }

  const headers = new Headers(init.headers);
  const token = tokenOverride === undefined ? accessToken : tokenOverride;

  if (init.body) headers.set("Content-Type", "application/json");
  headers.delete("Authorization");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(path, {
    ...init,
    headers,
    credentials: "omit",
    cache: "no-store",
  });

  if (response.status === 204) return undefined as T;

  let data: any = null;
  try {
      data = await response.json();
  } catch(e) {}

  if (!response.ok) {
    if (response.status === 401 && tokenOverride === undefined) {
      accessToken = null;
      window.dispatchEvent(new Event("auth-expired"));
    }
    const error = Object.assign(new Error(data?.error?.message ?? "Request failed"), {
      status: response.status,
      data,
    });
    throw error;
  }

  return data as T;
}
