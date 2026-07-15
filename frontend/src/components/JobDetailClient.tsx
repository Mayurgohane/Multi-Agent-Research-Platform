"use client";

import { useEffect, useState, useTransition } from "react";
import { api } from "@/lib/api";
import type { Report, ResearchJobDetail } from "@/lib/types";
import { AgentTimeline } from "./AgentTimeline";
import { ReportView } from "./ReportView";
import { StatusBadge } from "./StatusBadge";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);
const RETRIABLE = new Set(["failed", "cancelled"]);

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
  const [copied, setCopied] = useState(false);
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
        setError(null);
        const updated = await api.cancelResearch(job.id);
        setJob((prev) => ({ ...prev, ...updated }));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Cancel failed");
      }
    });
  }

  function retry() {
    startTransition(async () => {
      try {
        setError(null);
        setReport(null);
        const updated = await api.retryResearch(job.id);
        const detail = await api.getResearch(job.id);
        setJob({ ...detail, ...updated });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Retry failed");
      }
    });
  }

  async function copyReport() {
    if (!report?.content_md) return;
    try {
      await navigator.clipboard.writeText(report.content_md);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Could not copy report to clipboard");
    }
  }

  function downloadReport() {
    if (!report?.content_md) return;
    const blob = new Blob([report.content_md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `marp-report-${job.id.slice(0, 8)}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <div className="page-head">
        <div>
          <p className="muted" style={{ margin: 0 }}>
            {job.status === "running" || job.status === "queued" ? (
              <span className="pulse" />
            ) : null}
            Research job
          </p>
          <h1>{job.topic}</h1>
        </div>
        <div style={{ display: "flex", gap: "0.65rem", alignItems: "center", flexWrap: "wrap" }}>
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
          {RETRIABLE.has(job.status) ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={retry}
              disabled={pending}
            >
              {pending ? "Retrying…" : "Retry job"}
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
            <li>
              <span className="muted">Events</span>
              <span>{job.events?.length ?? 0}</span>
            </li>
          </ul>

          <h2 style={{ fontFamily: "var(--font-display)" }}>Agent activity</h2>
          <AgentTimeline events={job.events || []} />
        </aside>

        <section className="panel panel-pad">
          <div className="report-toolbar">
            <h2 style={{ margin: 0, fontFamily: "var(--font-display)" }}>Report</h2>
            {report ? (
              <div className="report-actions">
                <button type="button" className="btn btn-secondary" onClick={copyReport}>
                  {copied ? "Copied" : "Copy"}
                </button>
                <button type="button" className="btn btn-secondary" onClick={downloadReport}>
                  Download .md
                </button>
              </div>
            ) : null}
          </div>
          <ReportView report={report} papers={job.papers || []} />
        </section>
      </div>
    </>
  );
}
