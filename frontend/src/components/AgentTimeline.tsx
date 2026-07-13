import type { AgentEvent } from "@/lib/types";

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export function AgentTimeline({ events }: { events: AgentEvent[] }) {
  if (!events.length) {
    return <div className="empty">Waiting for agent events…</div>;
  }

  const ordered = [...events].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  return (
    <ol className="timeline">
      {ordered.map((event) => (
        <li key={event.id} className="timeline-item">
          <div>
            <div className="timeline-agent">{event.agent}</div>
            <div className="muted" style={{ fontSize: "0.75rem" }}>
              {formatTime(event.created_at)}
            </div>
          </div>
          <div className="timeline-body">
            <strong>{event.event_type.replaceAll("_", " ")}</strong>
            <p>{event.message || "—"}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
