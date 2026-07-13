import { Hero } from "@/components/Hero";

const STEPS = [
  { title: "Planner", copy: "Shapes queries and inclusion criteria from your topic." },
  { title: "Searcher", copy: "Pulls papers from arXiv and Semantic Scholar." },
  { title: "Reader", copy: "Extracts claims, methods, and limitations." },
  { title: "Critic", copy: "Finds coverage gaps and may request another pass." },
  { title: "Writer", copy: "Composes a cited literature review you can trust." },
];

export default function HomePage() {
  return (
    <>
      <Hero />

      <section id="pipeline" className="section shell">
        <div className="section-head">
          <h2>One pipeline. Clear handoffs.</h2>
          <p>
            Each agent has a single job. Together they turn a research question into a
            structured, citable review.
          </p>
        </div>
        <div className="pipeline">
          {STEPS.map((step) => (
            <article key={step.title} className="pipeline-step">
              <strong>{step.title}</strong>
              <span>{step.copy}</span>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}
