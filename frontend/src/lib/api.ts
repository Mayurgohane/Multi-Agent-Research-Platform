import type {
  CreateResearchPayload,
  Report,
  ResearchJob,
  ResearchJobDetail,
  ResearchJobList,
} from "./types";

function getApiBase(): string {
  const fallback = "http://localhost:8000";
  if (typeof window === "undefined") {
    return (
      process.env.API_INTERNAL_BASE_URL?.replace(/\/$/, "") ||
      process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
      fallback
    );
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || fallback;
}

const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${getApiBase()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) detail = data.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const api = {
  createResearch(payload: CreateResearchPayload) {
    return request<ResearchJob>("/api/v1/research", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  listResearch(page = 1, pageSize = 20, status?: string) {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (status) params.set("status", status);
    return request<ResearchJobList>(`/api/v1/research?${params.toString()}`);
  },
  getResearch(id: string) {
    return request<ResearchJobDetail>(`/api/v1/research/${id}`);
  },
  getReport(id: string) {
    return request<Report>(`/api/v1/research/${id}/report`);
  },
  cancelResearch(id: string) {
    return request<ResearchJob>(`/api/v1/research/${id}`, {
      method: "DELETE",
    });
  },
  retryResearch(id: string) {
    return request<ResearchJob>(`/api/v1/research/${id}/retry`, {
      method: "POST",
    });
  },
};

export { ApiError };
export const API_BASE = getApiBase();
