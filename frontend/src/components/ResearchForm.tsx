"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition, type FormEvent } from "react";
import { api } from "@/lib/api";

export function ResearchForm() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const form = new FormData(event.currentTarget);
    const topic = String(form.get("topic") || "").trim();
    const maxPapers = Number(form.get("max_papers") || 15);
    const maxCriticLoops = Number(form.get("max_critic_loops") || 1);
    const yearFromRaw = String(form.get("year_from") || "").trim();
    const yearToRaw = String(form.get("year_to") || "").trim();
    const inclusionNotes = String(form.get("inclusion_notes") || "").trim();

    if (topic.length < 3) {
      setError("Topic must be at least 3 characters.");
      return;
    }

    startTransition(async () => {
      try {
        const job = await api.createResearch({
          topic,
          max_papers: maxPapers,
          max_critic_loops: maxCriticLoops,
          year_from: yearFromRaw ? Number(yearFromRaw) : undefined,
          year_to: yearToRaw ? Number(yearToRaw) : undefined,
          inclusion_notes: inclusionNotes || undefined,
        });
        router.push(`/research/${job.id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to start research");
      }
    });
  }

  return (
    <form className="panel panel-pad form-grid" onSubmit={onSubmit}>
      <label>
        Research topic
        <textarea
          name="topic"
          required
          minLength={3}
          placeholder="e.g. Evaluation benchmarks for retrieval-augmented generation"
          defaultValue=""
        />
      </label>

      <div className="form-row">
        <label>
          Max papers
          <input name="max_papers" type="number" min={1} max={100} defaultValue={15} />
        </label>
        <label>
          Critic loops
          <input
            name="max_critic_loops"
            type="number"
            min={0}
            max={5}
            defaultValue={1}
          />
        </label>
      </div>

      <div className="form-row">
        <label>
          Year from
          <input name="year_from" type="number" min={1900} max={2100} placeholder="2020" />
        </label>
        <label>
          Year to
          <input name="year_to" type="number" min={1900} max={2100} placeholder="2026" />
        </label>
      </div>

      <label>
        Inclusion notes
        <textarea
          name="inclusion_notes"
          placeholder="Optional constraints — venues, methods, exclusions…"
        />
      </label>

      {error ? <p className="error-text">{error}</p> : null}

      <button className="btn btn-primary" type="submit" disabled={pending}>
        {pending ? "Starting…" : "Launch multi-agent review"}
      </button>
    </form>
  );
}
