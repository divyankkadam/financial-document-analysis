import React, { useState } from "react";

function ScoreBar({ label, value }) {
  const pct = Math.round((value || 0) * 100);
  const color =
    pct >= 80 ? "var(--color-success)" : pct >= 60 ? "var(--color-warning)" : "var(--color-danger)";

  return (
    <div className="mb-2">
      <div className="d-flex justify-content-between mb-1">
        <span className="text-capitalize text-muted app-text-compact">{label}</span>
        <span className="fw-semibold app-text-compact">{pct}%</span>
      </div>
      <div className="progress" style={{ height: 4 }}>
        <div className="progress-bar" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}

export default function EvalBadge({ confidence, metrics, retryCount }) {
  const [open, setOpen] = useState(false);
  if (confidence === undefined || confidence === null) return null;

  const pct = Math.round(confidence * 100);
  const badgeColor =
    pct >= 80
      ? { bg: "#ecfdf5", text: "#065f46", border: "#a7f3d0" }
      : pct >= 60
      ? { bg: "#fef3c7", text: "#92400e", border: "#fde68a" }
      : { bg: "#fef2f2", text: "#991b1b", border: "#fecaca" };

  return (
    <div className="mt-2">
      <div className="d-flex align-items-center gap-2 flex-wrap">
        <span
          className="badge px-2 py-1"
          style={{
            background: badgeColor.bg,
            color: badgeColor.text,
            border: `1px solid ${badgeColor.border}`,
            fontSize: "0.75rem",
          }}
        >
          <i className="bi bi-graph-up me-1" />
          Confidence: {pct}%
        </span>

        {retryCount > 0 && (
          <span
            className="badge px-2 py-1"
            style={{
              background: "#fef3c7",
              color: "#92400e",
              border: "1px solid #fde68a",
              fontSize: "0.75rem",
            }}
          >
            <i className="bi bi-arrow-repeat me-1" />
            {retryCount} refinement{retryCount !== 1 ? "s" : ""}
          </span>
        )}

        {metrics && Object.keys(metrics).length > 0 && (
          <button
            className="btn btn-sm btn-outline-secondary py-0"
            onClick={() => setOpen((o) => !o)}
            style={{ fontSize: "0.75rem" }}
          >
            <i className={`bi bi-chevron-${open ? "up" : "down"} me-1`} />
            Quality details
          </button>
        )}
      </div>

      {open && metrics && (
        <div
          className="mt-2"
          style={{
            background: "#f9fafb",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--color-border-light)",
            padding: "0.75rem",
          }}
        >
          <p
            className="app-text-compact fw-semibold text-muted mb-2"
            style={{ letterSpacing: "0.04em", fontSize: "0.7rem", textTransform: "uppercase" }}
          >
            Answer Quality Metrics
          </p>
          <ScoreBar label="Relevance" value={metrics.relevance} />
          <ScoreBar label="Accuracy" value={metrics.groundedness} />
          <ScoreBar label="Completeness" value={metrics.completeness} />
          <ScoreBar label="Confidence" value={metrics.confidence} />
          {metrics.improvement && metrics.improvement !== "none" && (
            <div
              className="mt-2 app-text-muted"
              style={{
                background: "#eff6ff",
                color: "#1e40af",
                borderRadius: "var(--radius-sm)",
                padding: "0.4rem 0.6rem",
                fontSize: "0.8125rem",
              }}
            >
              <i className="bi bi-lightbulb me-1" />
              {metrics.improvement}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
