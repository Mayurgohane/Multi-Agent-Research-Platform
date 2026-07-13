import Link from "next/link";
import type { ResearchJob } from "@/lib/types";
import { StatusBadge } from "./StatusBadge";

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function JobList({ jobs }: { jobs: ResearchJob[] }) {
  if (!jobs.length) {
    return (
      <div className="empty">
        No research jobs yet. Launch your first review with the form above.
      </div>
    );
  }

  return (
    <div className="jobs-grid">
      {jobs.map((job) => (
        <Link key={job.id} href={`/research/${job.id}`} className="job-link">
          <div className="job-link-top">
            <h3 className="job-topic">{job.topic}</h3>
            <StatusBadge status={job.status} />
          </div>
          <p className="muted" style={{ margin: 0, fontSize: "0.86rem" }}>
            Created {formatDate(job.created_at)}
          </p>
        </Link>
      ))}
    </div>
  );
}
