import Constants from "expo-constants";

export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ?? "http://192.168.10.131:8001";

const SESSION_ID = ((globalThis as { crypto?: { randomUUID?: () => string } }).crypto?.randomUUID?.() ?? String(Date.now())).slice(0, 64);

let _token: string | null = null;
let _workerId: string | null = null;

type UnauthorizedHandler = () => void | Promise<void>;
type ApiErrorOptions = {
  status?: number;
  path: string;
  method: string;
  serverDetail?: string;
  cause?: unknown;
};

const NETWORK_ERROR_MESSAGE = "We couldn't reach the server. Check your connection and try again.";

let _unauthorizedHandler: UnauthorizedHandler | null = null;

export function setApiAuth(token: string | null, workerId: string | null): void {
  _token = token;
  _workerId = workerId;
}

export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  _unauthorizedHandler = handler;
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
  if (!_token) {
    throw new Error("Not authenticated");
  }
  return _token;
}

function getHeaders(): Record<string, string> {
  return getClientHeaders();
}

export function isAuthenticated(): boolean {
  return _token !== null;
}

export function getClientHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${getAuthToken()}`,
    "Content-Type": "application/json",
    "X-Client": "mobile",
    "X-Session-Id": SESSION_ID,
  };
  const version = Constants.expoConfig?.version;
  if (version) headers["X-App-Version"] = version;
  return headers;
}

export function getWorkerId(): string {
  if (!_token || !_workerId) {
    throw new Error("Not authenticated");
  }
  return _workerId;
}

export async function fetchWorker<T>(path: string): Promise<T> {
  return requestJson<T>(path, { headers: getHeaders() });
}

export async function postWorker<T = void>(path: string, body?: object): Promise<T> {
  return requestJson<T>(path, {
    method: "POST",
    headers: getHeaders(),
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

export async function putWorker<T>(path: string, body: object): Promise<T> {
  return requestJson<T>(path, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
}

export async function deleteWorker<T = void>(path: string): Promise<T> {
  return requestJson<T>(path, {
    method: "DELETE",
    headers: getHeaders(),
  });
}

export async function uploadWorkerAvatar(imageUri: string, mimeType = "image/jpeg"): Promise<{ url: string }> {
  const ext = imageUri.split(".").pop()?.toLowerCase() ?? "jpg";
  const formData = new FormData();
  formData.append("file", { uri: imageUri, type: mimeType, name: `avatar.${ext}` } as never);
  return requestJson<{ url: string }>("/uploads/avatar", {
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
      await _unauthorizedHandler?.();
    }
    const apiError = new ApiError(getFriendlyErrorMessage(response.status, path), {
      status: response.status,
      path,
      method,
      serverDetail: await readServerDetail(response),
    });
    logApiError(apiError);
    throw apiError;
  }
  if (response.status === 204) {
    return undefined as T;
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
  let detail: unknown;
  try {
    const payload = JSON.parse(rawText) as { detail?: unknown; message?: unknown; error?: unknown } | null;
    detail = payload?.detail ?? payload?.message ?? payload?.error ?? rawText;
  } catch {
    detail = rawText;
  }
  const text = typeof detail === "string" ? detail : JSON.stringify(detail);
  return text.length > 500 ? `${text.slice(0, 500)}...` : text;
}

function getFriendlyErrorMessage(status: number, path: string): string {
  if (status === 401 && path === "/auth/login") {
    return "Email or password is incorrect.";
  }
  if (status === 409 && path.includes("/auth/register")) {
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
