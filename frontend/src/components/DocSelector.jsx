import React, { useState } from "react";
import { deleteDocument } from "../services/api";

export default function DocSelector({
  documents,
  selectedDocId,
  onSelect,
  onDeleted,
  readOnly = false,
}) {
  const [deleting, setDeleting] = useState(null);

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    if (!window.confirm("Remove this document?")) return;
    setDeleting(docId);
    try {
      await deleteDocument(docId);
      onDeleted(docId);
    } catch (err) {
      alert("Failed to delete document.");
    } finally {
      setDeleting(null);
    }
  };

  const handleReindex = async (e, docId) => {
    e.stopPropagation();
    try {
      await fetch(`/api/documents/${docId}/reindex`, { method: "POST" });
      window.location.reload();
    } catch (err) {
      alert("Failed to process document.");
    }
  };

  if (documents.length === 0) {
    return (
      <div className="card">
        <div className="card-body text-center py-4">
          <div
            className="d-inline-flex align-items-center justify-content-center mb-2"
            style={{
              width: 40,
              height: 40,
              borderRadius: "var(--radius-sm)",
              background: "#f3f4f6",
            }}
          >
            <i className="bi bi-folder2-open text-muted" style={{ fontSize: "1.1rem", opacity: 0.5 }} />
          </div>
          <p className="text-muted app-text-muted mt-1 mb-0" style={{ fontSize: "0.8125rem" }}>
            No documents uploaded yet
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div
        className="card-header d-flex align-items-center justify-content-between"
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
            <i className="bi bi-folder2-open" style={{ fontSize: "0.7rem" }} />
          </div>
          <span className="fw-semibold" style={{ fontSize: "0.9rem" }}>
            Documents
          </span>
          <span
            className="badge"
            style={{
              background: "var(--color-primary-light)",
              color: "var(--color-primary)",
              fontSize: "0.7rem",
            }}
          >
            {documents.length}
          </span>
        </div>
        <span className="text-muted" style={{ fontSize: "0.75rem" }}>
          {readOnly ? "Ready to use" : "Click to select"}
        </span>
      </div>

      <div className="card-body p-2" style={{ maxHeight: 320, overflowY: "auto" }}>
        {documents.map((doc) => {
          const isSelected = doc.doc_id === selectedDocId;
          return (
            <div
              key={doc.doc_id}
              className="d-flex align-items-start justify-content-between gap-2"
              style={{
                cursor: readOnly ? "default" : "pointer",
                padding: "0.5rem 0.625rem",
                borderRadius: "var(--radius-sm)",
                marginBottom: 4,
                background: isSelected ? "var(--color-primary-light)" : "transparent",
                border: isSelected
                  ? "1px solid var(--color-primary)"
                  : "1px solid transparent",
                transition: "all 120ms ease",
              }}
              onClick={() => !readOnly && onSelect(doc)}
              onMouseEnter={(e) => {
                if (!isSelected) e.currentTarget.style.background = "#f9fafb";
              }}
              onMouseLeave={(e) => {
                if (!isSelected) e.currentTarget.style.background = "transparent";
              }}
            >
              <div className="d-flex align-items-start gap-2 flex-grow-1 overflow-hidden">
                <i
                  className={`bi bi-file-earmark-pdf-fill mt-1 flex-shrink-0 ${
                    isSelected ? "text-primary" : "text-danger"
                  }`}
                  style={{ fontSize: "0.85rem" }}
                />
                <div className="overflow-hidden">
                  <p
                    className={`mb-0 fw-semibold text-truncate document-title ${
                      isSelected ? "text-primary" : ""
                    }`}
                    title={doc.file_name}
                    style={{ fontSize: "0.8125rem" }}
                  >
                    {doc.file_name}
                  </p>
                  <p className="text-muted mb-0 document-meta">
                    {doc.total_pages} pages
                    {doc.metadata?.title &&
                      ` · ${doc.metadata.title.slice(0, 25)}`}
                  </p>
                  <code className="text-muted document-id">{doc.doc_id?.slice(0, 8)}…</code>
                </div>
              </div>

              <div className="d-flex flex-column align-items-end gap-1 flex-shrink-0">
                {readOnly && (
                  <span
                    className="badge"
                    style={{
                      background: "#ecfdf5",
                      color: "#065f46",
                      fontSize: "0.675rem",
                      fontWeight: 600,
                    }}
                  >
                    <i className="bi bi-check2 me-1" style={{ fontSize: "0.6rem" }} />
                    Ready
                  </span>
                )}

                {!readOnly && isSelected && (
                  <span
                    className="badge"
                    style={{
                      background: "var(--color-primary)",
                      color: "#ffffff",
                      fontSize: "0.675rem",
                    }}
                  >
                    Active
                  </span>
                )}

                {!doc.indexed && (
                  <button
                    className="btn btn-sm py-0 px-1"
                    style={{ color: "#d97706", background: "#fef3c7", fontSize: "0.7rem" }}
                    onClick={(e) => handleReindex(e, doc.doc_id)}
                    title="Re-process this document"
                  >
                    <i className="bi bi-arrow-clockwise me-1" />
                    Re-process
                  </button>
                )}

                <button
                  className="btn btn-sm p-0"
                  style={{ lineHeight: 1, color: "var(--color-danger)" }}
                  onClick={(e) => handleDelete(e, doc.doc_id)}
                  disabled={deleting === doc.doc_id}
                  title="Remove document"
                >
                  {deleting === doc.doc_id ? (
                    <span className="spinner-border spinner-border-sm" />
                  ) : (
                    <i className="bi bi-trash3" style={{ fontSize: "0.8rem" }} />
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
