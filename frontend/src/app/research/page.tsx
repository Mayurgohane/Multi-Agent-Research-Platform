import { JobList } from "@/components/JobList";
import { ResearchForm } from "@/components/ResearchForm";
import { api } from "@/lib/api";
import type { ResearchJob } from "@/lib/types";

export const dynamic = "force-dynamic";

async function loadJobs(): Promise<ResearchJob[]> {
  try {
    const data = await api.listResearch(1, 20);
    return data.items;
  } catch {
    return [];
  }
}

export default async function ResearchPage() {
  const jobs = await loadJobs();

  return (
    <div className="shell" style={{ paddingBottom: "3rem" }}>
      <div className="page-head">
        <div>
          <p className="muted" style={{ margin: 0 }}>
            Workspace
          </p>
          <h1>Start a literature review</h1>
        </div>
      </div>

      <div className="detail-layout">
        <section>
          <ResearchForm />
        </section>
        <section className="panel panel-pad">
          <h2 style={{ marginTop: 0, fontFamily: "var(--font-display)" }}>Recent jobs</h2>
          <JobList jobs={jobs} />
        </section>
      </div>
    </div>
  );
}
