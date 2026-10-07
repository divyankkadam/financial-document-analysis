import React from "react";

function formatConversationTime(value) {
  if (!value) return "";
  return new Date(value).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ConversationHistory({
  conversations,
  activeConversationId,
  onSelect,
  onDelete,
}) {
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
            <i className="bi bi-clock-history" style={{ fontSize: "0.7rem" }} />
          </div>
          <span className="fw-semibold" style={{ fontSize: "0.9rem" }}>
            History
          </span>
        </div>
        <span
          className="badge"
          style={{
            background: "var(--color-primary-light)",
            color: "var(--color-primary)",
            fontSize: "0.7rem",
          }}
        >
          {conversations.length}
        </span>
      </div>

      <div className="card-body p-2 conversation-history" style={{ maxHeight: 260, overflowY: "auto" }}>
        {conversations.length === 0 ? (
          <div className="text-center py-3">
            <i className="bi bi-chat-left-text text-muted" style={{ fontSize: "1.25rem", opacity: 0.3 }} />
            <p className="text-muted app-text-muted mb-0 mt-2" style={{ fontSize: "0.75rem" }}>
              No conversations yet
            </p>
          </div>
        ) : (
          conversations.map((conversation) => {
            const isActive = conversation.id === activeConversationId;
            const messageCount = conversation.messages?.length || 0;

            return (
              <div
                key={conversation.id}
                className="w-100 text-start d-flex align-items-start gap-2"
                role="button"
                tabIndex={0}
                onClick={() => onSelect(conversation.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    onSelect(conversation.id);
                  }
                }}
                style={{
                  padding: "0.45rem 0.55rem",
                  borderRadius: "var(--radius-sm)",
                  marginBottom: 3,
                  background: isActive ? "var(--color-primary-light)" : "transparent",
                  border: isActive ? "1px solid var(--color-primary)" : "1px solid transparent",
                  cursor: "pointer",
                  transition: "all 120ms ease",
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.background = "#f9fafb";
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.background = isActive ? "var(--color-primary-light)" : "transparent";
                }}
              >
                <i
                  className={`bi bi-chat-left-dots mt-0.5 flex-shrink-0 ${
                    isActive ? "text-primary" : "text-muted"
                  }`}
                  style={{ fontSize: "0.75rem" }}
                />
                <div className="overflow-hidden flex-grow-1">
                  <p
                    className={`mb-0 fw-semibold text-truncate ${
                      isActive ? "text-primary" : ""
                    }`}
                    title={conversation.title}
                    style={{ fontSize: "0.8125rem" }}
                  >
                    {conversation.title || "New conversation"}
                  </p>
                  <p className="text-muted mb-0 app-text-compact" style={{ fontSize: "0.7rem" }}>
                    {messageCount} message{messageCount === 1 ? "" : "s"} ·{" "}
                    {formatConversationTime(conversation.updatedAt)}
                  </p>
                </div>
                <button
                  type="button"
                  className="btn btn-sm p-0 flex-shrink-0"
                  style={{ lineHeight: 1, color: "var(--color-text-muted)" }}
                  onClick={(event) => {
                    event.stopPropagation();
                    onDelete(conversation.id);
                  }}
                  title="Delete conversation"
                >
                  <i className="bi bi-trash3" style={{ fontSize: "0.7rem" }} />
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
