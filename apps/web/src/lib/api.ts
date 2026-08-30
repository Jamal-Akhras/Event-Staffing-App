import { appVersion, sessionId } from "./session";

const envBase = import.meta.env.VITE_API_BASE ?? "";
export const API_BASE = envBase || (import.meta.env.DEV ? "http://127.0.0.1:8001" : "");

type UnauthorizedHandler = () => void | Promise<void>;
type ApiErrorOptions = {
  status?: number;
  path: string;
  method: string;
  serverDetail?: string;
  cause?: unknown;
};

const NETWORK_ERROR_MESSAGE = "We couldn't reach the server. Check your connection and try again.";

let unauthorizedHandler: UnauthorizedHandler | null = null;

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler;
}

export class ApiError extends Error {
  status?: number;
  path: string;
  method: string;
  serverDetail?: string;
  cause?: unknown;

  constructor(message: string, options: ApiErrorOptions) {
    super(message);
    this.name = "ApiError";
    this.status = options.status;
    this.path = options.path;
    this.method = options.method;
    this.serverDetail = options.serverDetail;
    this.cause = options.cause;
  }
}

function getAuthToken(): string {
  const token = localStorage.getItem("auth_token");
  if (!token) {
    throw new Error("Not authenticated");
  }
  return token;
}

export function getAuthHeaders(): Record<string, string> {
  return {
    Authorization: `Bearer ${getAuthToken()}`,
    "Content-Type": "application/json",
    ...clientHeaders(),
  };
}

export function clientHeaders(): Record<string, string> {
  const headers: Record<string, string> = { "X-Client": "web", "X-Session-Id": sessionId() };
  if (appVersion) headers["X-App-Version"] = appVersion;
  return headers;
}

export async function fetchJson<T>(path: string): Promise<T> {
  return requestJson<T>(path, { headers: getAuthHeaders() });
}

export async function postJson<T = void>(path: string, body?: object): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: getAuthHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export async function fetchPublicJson<T>(path: string): Promise<T> {
  return requestJson<T>(path, { headers: { "Content-Type": "application/json" } });
}

export async function postPublicJson<T = void>(path: string, body?: object): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export async function putJson<T>(path: string, body: object): Promise<T> {
  return requestJson<T>(path, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(body),
  });
}

export async function deleteJson(path: string, body?: object): Promise<void> {
  await requestJson<void>(path, {
    method: "DELETE",
    headers: getAuthHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export async function uploadFile<T>(path: string, file: File): Promise<T> {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<T>(path, {
    method: "POST",
    headers: { Authorization: `Bearer ${getAuthToken()}` },
    body: formData,
  });
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const method = init.method ?? "GET";
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch (err) {
    const apiError = new ApiError(NETWORK_ERROR_MESSAGE, { path, method, cause: err });
    logApiError(apiError);
    throw apiError;
  }
  return parseResponse<T>(response, path, method);
}

async function parseResponse<T>(response: Response, path: string, method: string): Promise<T> {
  if (!response.ok) {
    if (response.status === 401) {
      await unauthorizedHandler?.();
    }
    const serverDetail = await readServerDetail(response);
    const apiError = new ApiError(getFriendlyErrorMessage(response.status, path, serverDetail), {
      status: response.status,
      path,
      method,
      serverDetail,
    });
    logApiError(apiError);
    throw apiError;
  }
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  try {
    return JSON.parse(text) as T;
  } catch (err) {
    const apiError = new ApiError("The server returned an unexpected response. Please try again.", {
      status: response.status,
      path,
      method,
      cause: err,
    });
    logApiError(apiError);
    throw apiError;
  }
}

async function readServerDetail(response: Response): Promise<string | undefined> {
  const rawText = await response.text().catch(() => "");
  if (!rawText) {
    return undefined;
  }
  let detail: unknown = rawText;
  try {
    const payload = JSON.parse(rawText) as { detail?: unknown; message?: unknown; error?: unknown } | null;
    detail = payload?.detail ?? payload?.message ?? payload?.error ?? rawText;
  } catch {
    detail = rawText;
  }
  const text = typeof detail === "string" ? detail : JSON.stringify(detail);
  return text.length > 500 ? `${text.slice(0, 500)}...` : text;
}

function getFriendlyErrorMessage(status: number, path: string, serverDetail?: string): string {
  if (status === 401 && path === "/auth/login") {
    return "Email or password is incorrect.";
  }
  const isRegisterConflict =
    status === 400 &&
    path.includes("/auth/register") &&
    serverDetail?.toLowerCase().includes("already registered");
  if (isRegisterConflict) {
    return "An account with this email already exists. Sign in instead.";
  }
  switch (status) {
    case 400:
    case 422:
      return "Please check the information and try again.";
    case 401:
      return "Your session has expired. Please sign in again.";
    case 403:
      return "You don't have permission to do that.";
    case 404:
      return "We couldn't find that item. Refresh and try again.";
    case 409:
      return "This action conflicts with the latest data. Refresh and try again.";
    case 429:
      return "Too many attempts. Please wait a minute and try again.";
    default:
      if (status >= 500) {
        return "The server is unavailable right now. Please try again in a moment.";
      }
      return "Something went wrong. Please try again.";
  }
}

function logApiError(error: ApiError): void {
  console.warn("API request failed", {
    message: error.message,
    status: error.status,
    method: error.method,
    path: error.path,
    serverDetail: error.serverDetail,
    cause: error.cause instanceof Error ? error.cause.message : error.cause,
  });
}
