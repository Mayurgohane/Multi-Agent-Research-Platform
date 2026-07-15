export type JobStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type AgentEvent = {
  id: string;
  agent: string;
  event_type: string;
  message: string | null;
  payload: Record<string, unknown>;
  created_at: string;
};

export type PaperSummary = {
  id: string;
  title: string;
  abstract: string | null;
  authors: string[];
  venue: string | null;
  year: number | null;
  url: string | null;
  source: string;
  arxiv_id: string | null;
  doi: string | null;
  citation_count: number | null;
  extractions: Record<string, unknown>;
};

export type JobPaper = {
  relevance_score: number | null;
  role: string;
  paper: PaperSummary;
};

export type ResearchJob = {
  id: string;
  topic: string;
  status: JobStatus;
  config: Record<string, unknown>;
  error: string | null;
  idempotency_key: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ResearchJobDetail = ResearchJob & {
  events: AgentEvent[];
  papers: JobPaper[];
};

export type ResearchJobList = {
  items: ResearchJob[];
  total: number;
  page: number;
  page_size: number;
};

export type Report = {
  id: string;
  job_id: string;
  content_md: string;
  content_json: Record<string, unknown>;
  citation_map: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type CreateResearchPayload = {
  topic: string;
  max_papers?: number;
  max_critic_loops?: number;
  year_from?: number;
  year_to?: number;
  inclusion_notes?: string;
};
