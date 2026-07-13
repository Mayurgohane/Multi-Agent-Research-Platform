import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header shell">
      <Link href="/" className="brand" aria-label="MARP home">
        <span className="brand-mark">MARP</span>
        <span className="brand-sub">Academic Research</span>
      </Link>
      <nav className="nav-links" aria-label="Primary">
        <Link href="/research">Workspace</Link>
        <Link href="/research" className="btn btn-primary">
          Start review
        </Link>
      </nav>
    </header>
  );
}
