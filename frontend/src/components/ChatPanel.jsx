import React, { useState, useRef, useEffect } from "react";
import { streamQuery } from "../services/api";
import EvalBadge from "./EvalBadge";
import ReactMarkdown from "react-markdown";
import DocSearchedBadge from "./DocSearchedBadge";

const SUGGESTED = [
  "What are the key revenue trends over the last 3 years?",
  "Summarize the main financial risks mentioned",
  "What are the major growth drivers?",
  "Compare profit margins across business segments",
  "Find any mention of declining performance",
];

function StatusBubble({ messages }) {
  if (!messages.length) return null;
  const msg = messages[messages.length - 1];
  // pipeline jargon is meaningless to the user
  const friendly = msg
    .replace(/retrieving.*?chunks/i, "Searching your documents")
    .replace(/expanding.*?queries/i, "Expanding search")
    .replace(/routing.*?document/i, "Finding best match")
    .replace(/CRAG.*?filtering/i, "Filtering results")
    .replace(/Self-RAG.*?eval/i, "Checking answer quality")
    .replace(/generating.*?answer/i, "Generating answer");
  return (
    <div className="d-flex align-items-start gap-2 mb-3">
      <div className="spinner-border spinner-border-sm text-primary mt-1 flex-shrink-0" style={{ width: 16, height: 16 }} />
      <div className="text-muted app-text-muted">{friendly}</div>
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";

  return (
    <div className={`d-flex mb-4 ${isUser ? "justify-content-end" : ""}`}>
      {!isUser && (
        <div
          className="d-flex align-items-center justify-content-center me-2.5 flex-shrink-0"
          style={{
            width: 32,
            height: 32,
            borderRadius: "var(--radius-sm)",
            background: "var(--color-primary-light)",
            color: "var(--color-primary)",
          }}
        >
          <i className="bi bi-robot small" />
        </div>
      )}

      <div style={{ maxWidth: "82%" }}>
        <div
          style={{
            borderRadius: isUser ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
            padding: "0.65rem 0.95rem",
            background: isUser ? "var(--color-primary)" : "var(--color-surface)",
            color: isUser ? "#ffffff" : "var(--color-text)",
            border: isUser ? "none" : "1px solid var(--color-border)",
            fontSize: "0.9375rem",
            lineHeight: 1.6,
          }}
        >
          {isUser ? (
            <p className="mb-0 chat-user-message" style={{ color: "#ffffff" }}>{msg.content}</p>
          ) : (
            <div className="assistant-answer">
              <ReactMarkdown>{msg.content || "…"}</ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && msg.payload && (
          <div className="mt-1.5 px-1">
            <DocSearchedBadge
              docsSearched={msg.payload.docs_searched}
              routingReason={msg.payload.routing_reason}
            />
            <EvalBadge
              confidence={msg.payload.confidence}
              metrics={msg.payload.metrics}
              retryCount={msg.payload.retry_count}
            />
            {msg.payload.sub_questions?.length > 0 && (
              <div className="mt-2">
                <p className="app-text-muted text-muted mb-1 fw-semibold">
                  Related areas explored:
                </p>
                <ul className="app-text-muted text-muted mb-0 ps-3">
                  {msg.payload.sub_questions.map((q, i) => (
                    <li key={i}>{q}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ChatPanel({
  sessionId,
  messages,
  onMessagesChange,
  onNewChat,
  onAnswer,
  hasDocuments,
}) {
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [statusMsgs, setStatusMsgs] = useState([]);

  const bottomRef = useRef();
  const cancelRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, statusMsgs]);

  useEffect(() => {
    cancelRef.current?.();
    setStatusMsgs([]);
    setStreaming(false);
  }, [sessionId]);

  const sendQuery = (query) => {
    if (!query.trim() || streaming || !hasDocuments) return;

    setInput("");
    setStatusMsgs([]);

    const userMsg = { role: "user", content: query };
    const botMsg = { role: "assistant", content: "", payload: null };
    const botIndex = messages.length + 1;

    onMessagesChange((prev) => [...prev, userMsg, botMsg]);
    setStreaming(true);

    cancelRef.current = streamQuery({
      query,
      sessionId,
      onStatus: (msg) => setStatusMsgs((prev) => [...prev, msg]),
      onAnswer: (payload) => {
        setStreaming(false);
        setStatusMsgs([]);
        onMessagesChange((prev) =>
          prev.map((m, i) =>
            i === botIndex
              ? { role: "assistant", content: payload.answer, payload }
              : m
          )
        );
        onAnswer?.(payload);
      },
      onError: (err) => {
        setStreaming(false);
        setStatusMsgs([]);
        onMessagesChange((prev) =>
          prev.map((m, i) =>
            i === botIndex
              ? { role: "assistant", content: `⚠ Error: ${err}`, payload: null }
              : m
          )
        );
      },
    });
  };

  return (
    <div
      className="card d-flex flex-column"
      style={{ height: "calc(100vh - 120px)", minHeight: 560 }}
    >
      <div
        className="card-header d-flex align-items-center gap-2"
        style={{ borderBottom: "1px solid var(--color-border-light)" }}
      >
        <span className="fw-semibold" style={{ fontSize: "0.9rem" }}>
          Financial Analyst
        </span>

        <button
          className="btn btn-sm btn-outline-primary ms-auto"
          onClick={onNewChat}
          disabled={streaming}
          title="New chat"
          style={{ borderRadius: "var(--radius-sm)" }}
        >
          <i className="bi bi-plus-lg me-1" />
          New Chat
        </button>

        {!hasDocuments && (
          <span
            className="badge"
            style={{
              background: "#fef3c7",
              color: "#92400e",
              fontWeight: 500,
            }}
          >
            Upload documents to begin
          </span>
        )}
      </div>

      <div className="flex-grow-1 overflow-auto p-4">
        {messages.length === 0 && (
          <div className="text-center py-5">
            <div
              className="d-inline-flex align-items-center justify-content-center mb-3"
              style={{
                width: 56,
                height: 56,
                borderRadius: "var(--radius-md)",
                background: "var(--color-primary-light)",
                color: "var(--color-primary)",
              }}
            >
              <i className="bi bi-bar-chart-line fs-4" />
            </div>
            <p className="text-muted mt-2 app-text-muted" style={{ fontSize: "0.95rem" }}>
              Upload a report and ask any financial question
            </p>

            {hasDocuments && (
              <div className="d-flex flex-wrap gap-2 justify-content-center mt-4" style={{ maxWidth: 640, margin: "1.5rem auto 0" }}>
                {SUGGESTED.map((s, i) => (
                  <button
                    key={i}
                    className="btn btn-sm btn-outline-secondary text-start"
                    style={{ borderRadius: "var(--radius-sm)", maxWidth: 300, fontSize: "0.8125rem" }}
                    onClick={() => sendQuery(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}

        {streaming && <StatusBubble messages={statusMsgs} />}
        <div ref={bottomRef} />
      </div>

      <div
        className="card-footer"
        style={{
          background: "var(--color-surface)",
          borderTop: "1px solid var(--color-border-light)",
          padding: "0.875rem 1rem",
        }}
      >
        <div className="input-group">
          <input
            type="text"
            className="form-control"
            placeholder={
              hasDocuments
                ? "Ask anything about your financial reports..."
                : "Upload documents first"
            }
            value={input}
            disabled={!hasDocuments || streaming}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendQuery(input)}
            style={{ borderRadius: "var(--radius-sm) 0 0 var(--radius-sm)" }}
          />
          <button
            className="btn btn-primary px-3"
            disabled={!hasDocuments || streaming || !input.trim()}
            onClick={() => sendQuery(input)}
            style={{
              borderRadius: "0 var(--radius-sm) var(--radius-sm) 0",
              minWidth: 44,
            }}
          >
            {streaming ? (
              <span className="spinner-border spinner-border-sm" />
            ) : (
              <i className="bi bi-send-fill" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
