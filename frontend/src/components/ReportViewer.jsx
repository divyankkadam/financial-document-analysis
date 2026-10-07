import React, { useState } from "react";

function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false);
  const score = source.crag_score ? Math.round(source.crag_score * 100) : null;

  const scoreStyle =
    score !== null
      ? score >= 80
        ? { bg: "#ecfdf5", text: "#065f46", border: "#a7f3d0" }
        : score >= 60
        ? { bg: "#fef3c7", text: "#92400e", border: "#fde68a" }
        : { bg: "#f3f4f6", text: "var(--color-text-secondary)", border: "var(--color-border)" }
      : null;

  return (
    <div className="mb-2">
      <div
        className="d-flex align-items-center justify-content-between py-2 px-3"
        style={{
          borderRadius: "var(--radius-sm)",
          border: "1px solid var(--color-border)",
          background: expanded ? "#f9fafb" : "var(--color-surface)",
          cursor: "pointer",
          transition: "all 120ms ease",
        }}
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="d-flex align-items-center gap-2 overflow-hidden">
          <span
            className="badge flex-shrink-0"
            style={{
              background: "#f3f4f6",
              color: "var(--color-text-secondary)",
              fontSize: "0.7rem",
            }}
          >
            #{index + 1}
          </span>
          <span
            className="fw-semibold text-truncate"
            style={{ fontSize: "0.8125rem", maxWidth: 180 }}
          >
            {source.section || "Unknown section"}
          </span>
          {source.page && (
            <span className="text-muted" style={{ fontSize: "0.75rem" }}>
              p. {source.page}
            </span>
          )}
        </div>
        <div className="d-flex align-items-center gap-2">
          {score !== null && scoreStyle && (
            <span
              className="badge px-2 py-1"
              style={{
                background: scoreStyle.bg,
                color: scoreStyle.text,
                border: `1px solid ${scoreStyle.border}`,
                fontSize: "0.7rem",
              }}
            >
              {score}%
            </span>
          )}
          <i
            className={`bi bi-chevron-${expanded ? "up" : "down"} text-muted`}
            style={{ fontSize: "0.7rem" }}
          />
        </div>
      </div>

      {expanded && (
        <div
          className="px-3 py-2"
          style={{
            borderLeft: "2px solid var(--color-border)",
            marginLeft: 8,
            marginTop: 2,
          }}
        >
          <p
            className="text-muted mb-0"
            style={{
              fontSize: "0.8125rem",
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              fontFamily: "monospace",
            }}
          >
            {source.snippet}
          </p>
        </div>
      )}
    </div>
  );
}

export default function ReportViewer({ sources, docMeta }) {
  if (!sources?.length) return null;

  return (
    <div className="card">
      <div
        className="card-header d-flex align-items-center gap-2"
        style={{ borderBottom: "1px solid var(--color-border-light)" }}
      >
        <div
          className="d-flex align-items-center justify-content-center"
          style={{
            width: 24,
            height: 24,
            borderRadius: "6px",
            background: "var(--color-primary-light)",
            color: "var(--color-primary)",
          }}
        >
          <i className="bi bi-journal-text" style={{ fontSize: "0.7rem" }} />
        </div>
        <span className="fw-semibold" style={{ fontSize: "0.9rem" }}>
          Source Chunks
        </span>
        <span
          className="badge"
          style={{
            background: "var(--color-primary-light)",
            color: "var(--color-primary)",
            fontSize: "0.7rem",
          }}
        >
          {sources.length}
        </span>
      </div>
      <div className="card-body p-3" style={{ maxHeight: 420, overflowY: "auto" }}>
        {docMeta && (
          <div
            className="app-text-muted mb-3"
            style={{
              background: "#f9fafb",
              borderRadius: "var(--radius-sm)",
              border: "1px solid var(--color-border-light)",
              padding: "0.5rem 0.75rem",
              fontSize: "0.8125rem",
            }}
          >
            <i className="bi bi-file-earmark-text me-1" />
            <strong>{docMeta.title || docMeta.file_name}</strong>
            {docMeta.author && (
              <span className="text-muted ms-2">· {docMeta.author}</span>
            )}
            {docMeta.pages && (
              <span className="text-muted ms-2">· {docMeta.pages} pages</span>
            )}
          </div>
        )}
        {sources.map((src, i) => (
          <SourceCard key={i} source={src} index={i} />
        ))}
      </div>
    </div>
  );
}
