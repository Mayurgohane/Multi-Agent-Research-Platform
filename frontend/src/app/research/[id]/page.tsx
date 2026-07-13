import { notFound } from "next/navigation";
import { JobDetailClient } from "@/components/JobDetailClient";
import { api, ApiError } from "@/lib/api";
import type { Report } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ResearchDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let job;
  try {
    job = await api.getResearch(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }

  let report: Report | null = null;
  if (job.status === "completed") {
    try {
      report = await api.getReport(id);
    } catch {
      report = null;
    }
  }

  return (
    <div className="shell">
      <JobDetailClient initialJob={job} initialReport={report} />
    </div>
  );
}
