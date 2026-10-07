import React, { useState, useEffect } from "react";
import { getEvalStats, getRecentRuns } from "../services/api";

export default function Sidebar({ selectedDoc, sessionId }) {
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedDoc?.doc_id) {
      setStats(null);
      setRecent([]);
      return;
    }
    setLoading(true);
    Promise.all([
      getEvalStats(selectedDoc.doc_id),
      getRecentRuns(5, selectedDoc.doc_id),
    ])
      .then(([s, r]) => {
        setStats(s);
        setRecent(r.records || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedDoc]);

  return (
    <div className="d-flex flex-column gap-3">
      {stats && stats.total_queries > 0 && (
        <div className="card">
          <div
            className="card-header"
            style={{ borderBottom: "1px solid var(--color-border-light)" }}
          >
            <div className="d-flex align-items-center gap-2">
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
                <i className="bi bi-speedometer2" style={{ fontSize: "0.7rem" }} />
              </div>
              <span className="fw-semibold" style={{ fontSize: "0.9rem" }}>
                Analysis Stats
              </span>
            </div>
          </div>
          <div className="card-body py-2 px-3">
            {[
              ["Questions", stats.total_queries],
              ["Avg accuracy", `${Math.round((stats.avg_confidence || 0) * 100)}%`],
              ["Avg response", `${stats.avg_latency_ms || 0}ms`],
              ["Refinements", stats.avg_retries ?? 0],
            ].map(([label, val]) => (
              <div
                key={label}
                className="d-flex justify-content-between py-1.5"
                style={{ borderBottom: "1px solid var(--color-border-light)" }}
              >
                <span className="text-muted app-text-muted">{label}</span>
                <span className="fw-semibold app-text-muted">{val}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {recent.length > 0 && (
        <div className="card">
          <div
            className="card-header"
            style={{ borderBottom: "1px solid var(--color-border-light)" }}
          >
            <div className="d-flex align-items-center gap-2">
              <div
                className="d-flex align-items-center justify-content-center"
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "6px",
                  background: "#f3f4f6",
                  color: "var(--color-text-secondary)",
                }}
              >
                <i className="bi bi-clock-history" style={{ fontSize: "0.7rem" }} />
              </div>
              <span className="fw-semibold" style={{ fontSize: "0.9rem" }}>
                Recent Questions
              </span>
            </div>
          </div>
          <div className="card-body py-2 px-3" style={{ maxHeight: 220, overflowY: "auto" }}>
            {recent.slice().reverse().map((r, i) => (
              <div
                key={i}
                className="py-2"
                style={{ borderBottom: "1px solid var(--color-border-light)" }}
              >
                <p className="mb-1 app-text-muted text-truncate" title={r.query} style={{ fontSize: "0.8125rem" }}>
                  {r.query}
                </p>
                <div className="d-flex gap-2">
                  <span
                    className="badge"
                    style={{ background: "#f3f4f6", color: "var(--color-text-secondary)", fontSize: "0.675rem" }}
                  >
                    {Math.round((r.confidence || 0) * 100)}% accurate
                  </span>
                  <span
                    className="badge"
                    style={{ background: "#f3f4f6", color: "var(--color-text-secondary)", fontSize: "0.675rem" }}
                  >
                    {r.latency_ms ? `${(r.latency_ms / 1000).toFixed(1)}s` : "—"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="text-center py-2">
          <span className="spinner-border spinner-border-sm text-secondary" />
        </div>
      )}
    </div>
  );
}
