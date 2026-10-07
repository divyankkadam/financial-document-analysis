import React, { useState } from "react";

export default function DocSearchedBadge({ docsSearched, routingReason }) {
  const [open, setOpen] = useState(false);
  if (!docsSearched?.length) return null;

  return (
    <div className="mt-2">
      <div className="d-flex align-items-center gap-2 flex-wrap">
        <span
          className="badge px-2 py-1"
          style={{
            background: "#eff6ff",
            color: "#1e40af",
            border: "1px solid #bfdbfe",
            fontSize: "0.75rem",
          }}
        >
          <i className="bi bi-search me-1" />
          Searched {docsSearched.length} document{docsSearched.length > 1 ? "s" : ""}
        </span>

        {docsSearched.map((doc, i) => (
          <span
            key={i}
            className="badge px-2 py-1"
            style={{
              background: "#f9fafb",
              color: "var(--color-text-secondary)",
              border: "1px solid var(--color-border)",
              fontSize: "0.75rem",
            }}
          >
            <i className="bi bi-file-earmark-pdf text-danger me-1" style={{ fontSize: "0.7rem" }} />
            {doc.file_name?.slice(0, 25)}
            {doc.file_name?.length > 25 ? "…" : ""}
          </span>
        ))}

        {routingReason && (
          <button
            className="btn btn-sm p-0"
            style={{ color: "var(--color-text-muted)", fontSize: "0.75rem" }}
            onClick={() => setOpen((o) => !o)}
          >
            {open ? "hide" : "why these?"}
          </button>
        )}
      </div>

      {open && routingReason && (
        <div
          className="mt-1 app-text-muted"
          style={{
            background: "#eff6ff",
            borderRadius: "var(--radius-sm)",
            padding: "0.35rem 0.5rem",
            fontSize: "0.8125rem",
            color: "#1e40af",
          }}
        >
          <i className="bi bi-info-circle me-1" />
          {routingReason}
        </div>
      )}
    </div>
  );
}
