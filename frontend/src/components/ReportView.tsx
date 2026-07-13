import ReactMarkdown from "react-markdown";
import type { JobPaper, Report } from "@/lib/types";

export function ReportView({
  report,
  papers,
}: {
  report: Report | null;
  papers: JobPaper[];
}) {
  if (!report) {
    return (
      <div className="empty">
        Report will appear here when the writer agent finishes.
      </div>
    );
  }

  return (
    <div className="report">
      <ReactMarkdown>{report.content_md}</ReactMarkdown>

      {papers.length > 0 ? (
        <section style={{ marginTop: "2rem" }}>
          <h2>Papers in this review</h2>
          <div className="papers">
            {papers.map((item) => (
              <article key={item.paper.id} className="paper">
                <h3>
                  {item.paper.url ? (
                    <a href={item.paper.url} target="_blank" rel="noreferrer">
                      {item.paper.title}
                    </a>
                  ) : (
                    item.paper.title
                  )}
                </h3>
                <p>
                  {(item.paper.authors || []).slice(0, 3).join(", ")}
                  {item.paper.year ? ` · ${item.paper.year}` : ""}
                  {item.relevance_score != null
                    ? ` · relevance ${(item.relevance_score * 100).toFixed(0)}%`
                    : ""}
                </p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
