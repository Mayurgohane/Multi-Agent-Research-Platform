export default function NotFound() {
  return (
    <div className="shell" style={{ padding: "4rem 0" }}>
      <h1 style={{ fontFamily: "var(--font-display)" }}>Job not found</h1>
      <p className="muted">That research job does not exist or was removed.</p>
      <a className="btn btn-primary" href="/research">
        Back to workspace
      </a>
    </div>
  );
}
