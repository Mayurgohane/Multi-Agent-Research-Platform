"use client";

import { useEffect, useState, useTransition } from "react";
import { api } from "@/lib/api";
import type { Report, ResearchJobDetail } from "@/lib/types";
import { AgentTimeline } from "./AgentTimeline";
import { ReportView } from "./ReportView";
import { StatusBadge } from "./StatusBadge";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);

export function JobDetailClient({
  initialJob,
  initialReport,
}: {
  initialJob: ResearchJobDetail;
  initialReport: Report | null;
}) {
  const [job, setJob] = useState(initialJob);
  const [report, setReport] = useState(initialReport);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    if (TERMINAL.has(job.status)) return;

    const timer = window.setInterval(async () => {
      try {
        const next = await api.getResearch(job.id);
        setJob(next);
        if (next.status === "completed") {
          try {
            setReport(await api.getReport(job.id));
          } catch {
            /* report may lag briefly */
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Polling failed");
      }
    }, 2500);

    return () => window.clearInterval(timer);
  }, [job.id, job.status]);

  function cancel() {
    startTransition(async () => {
      try {
        const updated = await api.cancelResearch(job.id);
        setJob((prev) => ({ ...prev, ...updated }));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Cancel failed");
      }
    });
  }

  return (
    <>
      <div className="page-head">
        <div>
          <p className="muted" style={{ margin: 0 }}>
            {job.status === "running" ? <span className="pulse" /> : null}
            Research job
          </p>
          <h1>{job.topic}</h1>
        </div>
        <div style={{ display: "flex", gap: "0.65rem", alignItems: "center" }}>
          <StatusBadge status={job.status} />
          {!TERMINAL.has(job.status) ? (
            <button
              type="button"
              className="btn btn-danger"
              onClick={cancel}
              disabled={pending}
            >
              Cancel
            </button>
          ) : null}
        </div>
      </div>

      {error ? <p className="error-text">{error}</p> : null}
      {job.error ? <p className="error-text">{job.error}</p> : null}

      <div className="detail-layout">
        <aside className="panel panel-pad">
          <h2 style={{ marginTop: 0, fontFamily: "var(--font-display)" }}>Status</h2>
          <ul className="meta-list">
            <li>
              <span className="muted">Job ID</span>
              <span style={{ fontSize: "0.8rem" }}>{job.id.slice(0, 8)}…</span>
            </li>
            <li>
              <span className="muted">Max papers</span>
              <span>{String(job.config.max_papers ?? "—")}</span>
            </li>
            <li>
              <span className="muted">Critic loops</span>
              <span>{String(job.config.max_critic_loops ?? "—")}</span>
            </li>
            <li>
              <span className="muted">Papers found</span>
              <span>{job.papers?.length ?? 0}</span>
            </li>
          </ul>

          <h2 style={{ fontFamily: "var(--font-display)" }}>Agent activity</h2>
          <AgentTimeline events={job.events || []} />
        </aside>

        <section className="panel panel-pad">
          <h2 style={{ marginTop: 0, fontFamily: "var(--font-display)" }}>Report</h2>
          <ReportView report={report} papers={job.papers || []} />
        </section>
      </div>
    </>
  );
}
