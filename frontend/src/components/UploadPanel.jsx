import React, { useState, useRef } from "react";
import { uploadMultiplePDFs } from "../services/api";

export default function UploadPanel({ onUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [queue, setQueue] = useState([]);
  const [error, setError] = useState("");
  const inputRef = useRef();

  const handleFiles = async (fileList) => {
    const files = Array.from(fileList).filter((f) =>
      f.name.toLowerCase().endsWith(".pdf")
    );
    const invalid = Array.from(fileList).filter(
      (f) => !f.name.toLowerCase().endsWith(".pdf")
    );

    if (invalid.length > 0) {
      setError(`Skipped ${invalid.length} non-PDF file(s).`);
    } else {
      setError("");
    }

    if (files.length === 0) return;

    setQueue(files.map((f) => f.name));
    setUploading(true);
    setProgress(0);

    try {
      const result = await uploadMultiplePDFs(files, setProgress);
      onUploaded(result.documents);
      if (result.errors?.length > 0) {
        setError(`${result.errors.length} file(s) failed to upload.`);
      }
    } catch (e) {
      setError(e.response?.data?.detail || "Upload failed.");
    } finally {
      setUploading(false);
      setQueue([]);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="card">
      <div className="card-body">
        <div className="d-flex align-items-center gap-2 mb-3">
          <div
            className="d-flex align-items-center justify-content-center"
            style={{
              width: 28,
              height: 28,
              borderRadius: "6px",
              background: "#fef2f2",
              color: "var(--color-danger)",
            }}
          >
            <i className="bi bi-file-earmark-pdf-fill" style={{ fontSize: "0.8rem" }} />
          </div>
          <h6 className="mb-0 fw-semibold" style={{ fontSize: "0.9rem" }}>
            Upload Reports
          </h6>
        </div>

        <div
          className="text-center d-flex flex-column align-items-center justify-content-center"
          style={{
            cursor: "pointer",
            minHeight: 130,
            borderRadius: "var(--radius-md)",
            border: `2px dashed ${dragging ? "var(--color-primary)" : "var(--color-border)"}`,
            background: dragging ? "var(--color-primary-light)" : "#fafafa",
            transition: "all 150ms ease",
            padding: "1rem",
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => !uploading && inputRef.current.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf"
            multiple
            className="d-none"
            onChange={(e) => handleFiles(e.target.files)}
          />

          {uploading ? (
            <>
              <div className="spinner-border spinner-border-sm text-primary mb-2" />
              <p className="text-muted app-text-muted mb-2 fw-semibold" style={{ fontSize: "0.8125rem" }}>
                Uploading & preparing {queue.length} file{queue.length > 1 ? "s" : ""}…
              </p>
              <div className="w-100 mb-2" style={{ maxHeight: 72, overflowY: "auto" }}>
                {queue.map((name, i) => (
                  <p key={i} className="text-muted mb-0 app-text-compact">
                    <i className="bi bi-file-earmark-pdf text-danger me-1" />
                    {name}
                  </p>
                ))}
              </div>
              <div className="w-100">
                <div className="progress" style={{ height: 4 }}>
                  <div
                    className="progress-bar bg-primary"
                    style={{ width: `${progress}%` }}
                  />
                </div>
                <small className="text-muted" style={{ fontSize: "0.75rem" }}>{progress}%</small>
              </div>
            </>
          ) : (
            <>
              <i className="bi bi-cloud-arrow-up fs-4 text-muted mb-2" style={{ opacity: 0.5 }} />
              <p className="mb-1 fw-semibold app-text-muted" style={{ fontSize: "0.875rem" }}>
                Drop PDFs here
              </p>
              <p className="text-muted mb-0" style={{ fontSize: "0.75rem" }}>
                or click to browse · multiple files supported
              </p>
            </>
          )}
        </div>

        {error && (
          <div
            className="mt-2 py-1.5 px-2 app-text-muted"
            style={{
              background: "#fef3c7",
              color: "#92400e",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.8125rem",
            }}
          >
            <i className="bi bi-exclamation-triangle me-1" />
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
