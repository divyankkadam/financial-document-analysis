import React from "react";
import { useNavigate } from "react-router-dom";

export default function AppHeader({ actionLabel = "Get Started", actionTo = "/analyst" }) {
  const navigate = useNavigate();

  return (
    <nav
      className="d-flex align-items-center justify-content-between px-5 py-3"
      style={{
        position: "sticky",
        top: 0,
        zIndex: 100,
        background: "rgba(255,255,255,0.85)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      <div
        className="d-flex align-items-center gap-2"
        style={{ cursor: "pointer" }}
        onClick={() => navigate("/")}
      >
        <div className="logo-mark" style={{ width: 32, height: 32, fontSize: "0.85rem" }}>
          <i className="bi bi-graph-up-arrow" />
        </div>
        <span className="fw-bold" style={{ fontSize: "1.05rem", letterSpacing: "-0.02em" }}>
          FinGrowth
        </span>
      </div>

      <div className="d-none d-md-flex align-items-center gap-4" />

      <div className="d-flex align-items-center gap-2">
        <button className="btn btn-sm btn-primary" onClick={() => navigate(actionTo)}>
          {actionLabel}
        </button>
      </div>
    </nav>
  );
}
