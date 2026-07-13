import Link from "next/link";

export function Hero() {
  return (
    <section className="hero shell" aria-labelledby="hero-title">
      <div className="hero-copy">
        <div className="brand">
          <span className="brand-mark">MARP</span>
        </div>
        <h1 id="hero-title">Literature reviews, orchestrated by agents.</h1>
        <p>
          Search arXiv and Semantic Scholar, critique coverage, and generate cited
          academic reviews — without babysitting every step.
        </p>
        <div className="hero-actions">
          <Link href="/research" className="btn btn-primary">
            Open workspace
          </Link>
          <Link href="#pipeline" className="btn btn-secondary">
            See the pipeline
          </Link>
        </div>
      </div>

      <div className="hero-visual" aria-hidden="true">
        <div className="orbit" />
        <div className="orbit orbit-2" />
        <span className="node node-a" />
        <span className="node node-b" />
        <span className="node node-c" />
        <div className="hero-caption">
          <strong>Five agents. One report.</strong>
          <span>Planner → Searcher → Reader → Critic → Writer</span>
        </div>
      </div>
    </section>
  );
}
