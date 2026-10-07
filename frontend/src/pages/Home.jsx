import React from "react";
import { useNavigate } from "react-router-dom";

import AppHeader from "../components/AppHeader";

function GrowthGraph() {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: 420,
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--color-border)",
        background: "#ffffff",
        boxShadow: "0 20px 60px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04)",
        overflow: "hidden",
      }}
    >
      <img
        src={`${process.env.PUBLIC_URL}/growth-graph.svg`}
        alt="Business growth chart: quarterly revenue rising from $28M to $82M with year-over-year growth up 34%"
        style={{ display: "block", width: "100%", height: "auto" }}
      />
    </div>
  );
}

function MockDocCard() {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: 360,
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--color-border)",
        background: "#ffffff",
        boxShadow: "0 20px 60px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04)",
        overflow: "hidden",
      }}
    >
      <div className="p-4">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div
            className="d-flex align-items-center justify-content-center"
            style={{ width: 40, height: 40, borderRadius: "var(--radius-sm)", background: "#fef2f2", color: "#ef4444" }}
          >
            <i className="bi bi-file-earmark-pdf-fill" />
          </div>
          <div>
            <p className="mb-0 fw-semibold" style={{ fontSize: "0.8rem" }}>10-K Annual Report</p>
            <p className="mb-0" style={{ fontSize: "0.65rem", color: "var(--color-text-muted)" }}>142 pages · Uploaded 2 min ago</p>
          </div>
          <span className="ms-auto badge" style={{ background: "#ecfdf5", color: "#065f46", fontSize: "0.6rem" }}>Ready</span>
        </div>
        <div className="d-flex gap-2 flex-wrap">
          {["Revenue", "Risk Factors", "MD&A", "Cash Flow"].map((t) => (
            <span
              key={t}
              style={{
                fontSize: "0.6rem",
                padding: "3px 8px",
                borderRadius: 4,
                background: "var(--color-primary-light)",
                color: "var(--color-primary)",
                fontWeight: 600,
              }}
            >
              {t}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function MockChatCard() {
  return (
    <div
      style={{
        width: "100%",
        maxWidth: 380,
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--color-border)",
        background: "#ffffff",
        boxShadow: "0 20px 60px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.04)",
        overflow: "hidden",
      }}
    >
      <div className="p-3">
        <div className="d-flex flex-column gap-2">
          <div className="d-flex justify-content-end">
            <div
              className="px-3 py-2"
              style={{
                borderRadius: "12px 12px 4px 12px",
                background: "var(--color-primary)",
                color: "#fff",
                fontSize: "0.75rem",
                maxWidth: "80%",
              }}
            >
              What's the YoY revenue growth and EBITDA margin trend?
            </div>
          </div>
          <div className="d-flex justify-content-start">
            <div
              className="px-3 py-2"
              style={{
                borderRadius: "12px 12px 12px 4px",
                background: "#f3f4f6",
                fontSize: "0.75rem",
                lineHeight: 1.5,
                maxWidth: "85%",
              }}
            >
              Revenue grew 23% YoY to $4.2B. EBITDA margin expanded from 18.3% to 21.7%, driven by operating leverage in the SaaS segment...
              <div className="d-flex align-items-center gap-1 mt-1">
                <span style={{ fontSize: "0.55rem", color: "var(--color-text-muted)" }}>97% confidence</span>
                <span style={{ fontSize: "0.55rem", color: "var(--color-text-muted)" }}>· p.42-44</span>
              </div>
            </div>
          </div>
          <div className="d-flex justify-content-end">
            <div
              className="px-3 py-2"
              style={{
                borderRadius: "12px 12px 4px 12px",
                background: "var(--color-primary)",
                color: "#fff",
                fontSize: "0.75rem",
                maxWidth: "80%",
              }}
            >
              What are the top risk factors affecting margin?
            </div>
          </div>
          <div className="d-flex justify-content-start">
            <div
              className="px-3 py-2"
              style={{
                borderRadius: "12px 12px 12px 4px",
                background: "#f3f4f6",
                fontSize: "0.75rem",
                lineHeight: 1.5,
                maxWidth: "85%",
              }}
            >
              Key risks: supply chain costs (+8%), regulatory compliance (+$120M), and FX headwinds (-3% impact)...
              <div className="d-flex align-items-center gap-1 mt-1">
                <span style={{ fontSize: "0.55rem", color: "var(--color-text-muted)" }}>95% confidence</span>
                <span style={{ fontSize: "0.55rem", color: "var(--color-text-muted)" }}>· p.67</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: "100vh", background: "var(--color-bg)" }}>
      <AppHeader />
      <section
        className="position-relative overflow-hidden"
        style={{
          paddingTop: "5rem",
          paddingBottom: "5rem",
          background: "linear-gradient(180deg, #ffffff 0%, var(--color-bg) 100%)",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "-20%",
            right: "-10%",
            width: 600,
            height: 600,
            background: "radial-gradient(circle, rgba(37,99,235,0.07) 0%, transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <div
          className="d-flex align-items-center gap-5 px-5 mx-auto position-relative"
          style={{ zIndex: 2, maxWidth: 1100 }}
        >
          <div className="flex-grow-1" style={{ minWidth: 0 }}>
            <div className="mb-3 animate-fade-in">
              <span
                className="d-inline-flex align-items-center gap-2 px-3 py-1.5"
                style={{
                  fontSize: "0.75rem",
                  background: "var(--color-primary-light)",
                  color: "var(--color-primary)",
                  border: "1px solid #bfdbfe",
                  borderRadius: 100,
                  fontWeight: 600,
                }}
              >
                <i className="bi bi-graph-up-arrow" />
                Financial Intelligence
              </span>
            </div>

            <h1
              className="fw-bold mb-3 animate-fade-in-delay-1"
              style={{
                fontSize: "clamp(3rem, 6vw, 4.5rem)",
                lineHeight: 1.05,
                letterSpacing: "-0.04em",
              }}
            >
              Your financial
              <br />
              reports, <span style={{ color: "var(--color-primary)" }}>decoded.</span>
            </h1>

            <p
              className="text-muted mb-4 animate-fade-in-delay-2"
              style={{ maxWidth: 440, fontSize: "1.25rem", lineHeight: 1.7 }}
            >
              Upload any report. Ask anything. Get cited answers
              in seconds — not hours.
            </p>

            <div className="d-flex align-items-center gap-3 animate-fade-in-delay-3">
              <button
                className="btn btn-primary btn-lg px-5 py-3 fw-semibold"
                style={{ borderRadius: "var(--radius-md)", fontSize: "1rem" }}
                onClick={() => navigate("/analyst")}
              >
                Start Free
              </button>
              <button
                className="btn btn-outline-secondary btn-lg px-4 py-3"
                style={{ borderRadius: "var(--radius-md)", fontSize: "1rem" }}
                onClick={() => document.getElementById("process")?.scrollIntoView({ behavior: "smooth" })}
              >
                See How
              </button>
            </div>
          </div>

          <div className="d-none d-lg-block flex-shrink-0 animate-fade-in-delay-4">
            <GrowthGraph />
          </div>
        </div>
      </section>
      <section
        id="process"
        className="py-5"
        style={{ background: "#000000", borderTop: "1px solid var(--color-border)", borderBottom: "1px solid var(--color-border)" }}
      >
        <div className="px-5 mx-auto" style={{ maxWidth: 1100 }}>
          <div className="text-center mb-5">
            <h2
              className="fw-bold"
              style={{ color : "#fbfbfb", letterSpacing: "-0.03em", fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)" }}
            >
              Three steps. Zero complexity.
            </h2>
          </div>
          <div className="d-flex align-items-center gap-5 mb-5">
            <div className="flex-grow-1" style={{ minWidth: 0 }}>
              <span
                style={{
                  fontSize: "0.80rem",
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  color: "var(--color-text-muted)",
                }}
              >
                STEP 01
              </span>
              <h3 className="fw-bold mt-1 mb-2" style={{ color : "#fbfbfb", fontSize: "1.75rem", letterSpacing: "-0.02em",  }}>
                Upload your docs
              </h3>
              <p className="text-muted mb-0" style={{ fontSize: "1.05rem", lineHeight: 1.7 }}>
                Drag and drop annual reports, 10-K filings, earnings transcripts, or any financial PDF.
                We index every page instantly.
              </p>
            </div>
            <div className="d-none d-md-block flex-shrink-0">
              <MockDocCard />
            </div>
          </div>
          <div className="d-flex align-items-center gap-5 mb-5 flex-md-row-reverse">
            <div className="flex-grow-1" style={{ minWidth: 0 }}>
              <span
                style={{
                  fontSize: "0.80rem",
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  color: "var(--color-text-muted)",
                }}
              >
                STEP 02
              </span>
              <h3 className="fw-bold mt-1 mb-2" style={{ color : "#fbfbfb", fontSize: "1.75rem", letterSpacing: "-0.02em" }}>
                Ask anything
              </h3>
              <p className="text-muted mb-0" style={{ fontSize: "1.05rem", lineHeight: 1.7 }}>
                No formulas. No code. Ask about revenue trends, risk exposure, growth
                projections, or run complex calculations — just type your question.
              </p>
            </div>
            <div className="d-none d-md-block flex-shrink-0">
              <MockChatCard />
            </div>
          </div>
          <div className="d-flex align-items-center gap-5">
            <div className="flex-grow-1" style={{ minWidth: 0 }}>
              <span
                style={{
                  fontSize: "0.80rem",
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  color: "var(--color-text-muted)",
                }}
              >
                STEP 03
              </span>
              <h3 className="fw-bold mt-1 mb-2" style={{ color : "#fbfbfb", fontSize: "1.75rem", letterSpacing: "-0.02em" }}>
                Decide with confidence
              </h3>
              <p className="text-muted mb-0" style={{ fontSize: "1.05rem", lineHeight: 1.7 }}>
                Every answer is cited to its source page, scored for accuracy, and backed
                by automated calculations you can verify. No guesswork.
              </p>
            </div>
            <div className="d-none d-md-block flex-shrink-0">
              <GrowthGraph />
            </div>
          </div>
        </div>
      </section>
      <section className="py-5">
        <div
          className="d-flex align-items-center justify-content-between gap-5 px-5 mx-auto flex-wrap"
          style={{ maxWidth: 1100 }}
        >
          <div>
            <h2
              className="fw-bold mb-2"
              style={{ letterSpacing: "-0.03em", fontSize: "clamp(1.75rem, 3.5vw, 2.5rem)" }}
            >
              Ready to grow smarter?
            </h2>
            <p className="text-muted mb-0" style={{ fontSize: "1.1rem" }}>
              Upload your first document. Get insights in under a minute.
            </p>
          </div>
          <button
            className="btn btn-primary btn-lg px-5 py-3 fw-semibold"
            style={{ borderRadius: "var(--radius-md)", fontSize: "1rem" }}
            onClick={() => navigate("/analyst")}
          >
            Launch FinGrowth
          </button>
        </div>
      </section>
      <footer
        className="px-5 py-4 d-flex align-items-center justify-content-between flex-wrap gap-3"
        style={{ borderTop: "1px solid var(--color-border)", background: "#ffffff" }}
      >
        <div className="d-flex align-items-center gap-2">
          <div className="logo-mark" style={{ width: 22, height: 22, fontSize: "0.55rem" }}>
            <i className="bi bi-graph-up-arrow" />
          </div>
          <span className="fw-semibold" style={{ fontSize: "0.8rem" }}>FinGrowth</span>
        </div>
        <p className="text-muted mb-0" style={{ fontSize: "0.75rem" }}>
          AI-powered financial document analysis.
        </p>
        <div className="d-flex gap-3">
          <a href="#process" className="text-muted" style={{ fontSize: "0.75rem", textDecoration: "none" }}>How It Works</a>
        </div>
      </footer>
    </div>
  );
}
