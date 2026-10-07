import React, { useState, useEffect } from "react";
import { v4 as uuidv4 } from "uuid";
import { listDocuments } from "../services/api";

import AppHeader from "../components/AppHeader";
import UploadPanel from "../components/UploadPanel";
import DocSelector from "../components/DocSelector";
import ChatPanel from "../components/ChatPanel";
import Sidebar from "../components/Sidebar";
import ConversationHistory from "../components/ConversationHistory";

const SESSION_STORAGE_KEY = "financialAnalyst.sessionId";
const LEGACY_CHAT_STORAGE_KEY = "financialAnalyst.chatMessages";
const CONVERSATIONS_STORAGE_KEY = "financialAnalyst.conversations";
const ACTIVE_CONVERSATION_KEY = "financialAnalyst.activeConversationId";

function createConversation(messages = []) {
  const firstQuestion = messages.find((msg) => msg.role === "user")?.content;
  return {
    id: uuidv4(),
    sessionId: uuidv4(),
    title: firstQuestion || "New conversation",
    messages,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

function getStoredSessionId() {
  const existing = localStorage.getItem(SESSION_STORAGE_KEY);
  if (existing) return existing;
  const next = uuidv4();
  localStorage.setItem(SESSION_STORAGE_KEY, next);
  return next;
}

function loadConversations() {
  try {
    const saved = localStorage.getItem(CONVERSATIONS_STORAGE_KEY);
    const parsed = saved ? JSON.parse(saved) : [];
    if (Array.isArray(parsed) && parsed.length > 0) return parsed;
  } catch (_) {}

  try {
    const legacy = localStorage.getItem(LEGACY_CHAT_STORAGE_KEY);
    const messages = legacy ? JSON.parse(legacy) : [];
    if (Array.isArray(messages) && messages.length > 0) {
      const conversation = createConversation(messages);
      conversation.sessionId = getStoredSessionId();
      localStorage.setItem(CONVERSATIONS_STORAGE_KEY, JSON.stringify([conversation]));
      localStorage.setItem(ACTIVE_CONVERSATION_KEY, conversation.id);
      localStorage.removeItem(LEGACY_CHAT_STORAGE_KEY);
      return [conversation];
    }
  } catch (_) {}

  const conversation = createConversation();
  localStorage.setItem(CONVERSATIONS_STORAGE_KEY, JSON.stringify([conversation]));
  localStorage.setItem(ACTIVE_CONVERSATION_KEY, conversation.id);
  return [conversation];
}

function getInitialActiveConversationId(conversations) {
  const savedId = localStorage.getItem(ACTIVE_CONVERSATION_KEY);
  if (savedId && conversations.some((c) => c.id === savedId)) return savedId;
  return conversations[0]?.id || "";
}

function titleFromMessages(messages) {
  const firstQuestion = messages.find((msg) => msg.role === "user")?.content;
  if (!firstQuestion) return "New conversation";
  return firstQuestion.length > 54
    ? `${firstQuestion.slice(0, 54)}...`
    : firstQuestion;
}

function getInitialConversationState() {
  const conversations = loadConversations();
  return {
    conversations,
    activeConversationId: getInitialActiveConversationId(conversations),
  };
}

export default function Analyst() {
  const [documents, setDocuments] = useState([]);
  const [initialConversationState] = useState(getInitialConversationState);
  const [conversations, setConversations] = useState(
    initialConversationState.conversations
  );
  const [activeConversationId, setActiveConversationId] = useState(
    initialConversationState.activeConversationId
  );
  const [loadingDocs, setLoadingDocs] = useState(true);

  const activeConversation =
    conversations.find((c) => c.id === activeConversationId) ||
    conversations[0];
  const sessionId = activeConversation?.sessionId || "";

  useEffect(() => {
    listDocuments()
      .then((data) => setDocuments(data.documents || []))
      .catch(() => {})
      .finally(() => setLoadingDocs(false));
  }, []);

  useEffect(() => {
    localStorage.setItem(CONVERSATIONS_STORAGE_KEY, JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    if (activeConversationId) {
      localStorage.setItem(ACTIVE_CONVERSATION_KEY, activeConversationId);
    }
  }, [activeConversationId]);

  const handleUploaded = (newDocs) => {
    setDocuments((prev) => {
      const existingIds = new Set(prev.map((d) => d.doc_id));
      return [...prev, ...newDocs.filter((d) => !existingIds.has(d.doc_id))];
    });
  };

  const handleDeleted = (docId) => {
    setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
  };

  const handleNewChat = () => {
    const conversation = createConversation();
    setConversations((prev) => [conversation, ...prev]);
    setActiveConversationId(conversation.id);
  };

  const handleDeleteConversation = (conversationId) => {
    setConversations((prev) => {
      const remaining = prev.filter((c) => c.id !== conversationId);
      if (remaining.length === 0) {
        const conversation = createConversation();
        setActiveConversationId(conversation.id);
        return [conversation];
      }
      if (conversationId === activeConversationId) {
        const nextActive = [...remaining].sort(
          (a, b) => (b.updatedAt || 0) - (a.updatedAt || 0)
        )[0];
        setActiveConversationId(nextActive.id);
      }
      return remaining;
    });
  };

  const updateActiveMessages = (updater) => {
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConversationId) return c;
        const nextMessages =
          typeof updater === "function"
            ? updater(c.messages || [])
            : updater;
        return {
          ...c,
          title: titleFromMessages(nextMessages),
          messages: nextMessages,
          updatedAt: Date.now(),
        };
      })
    );
  };

  const sortedConversations = [...conversations].sort(
    (a, b) => (b.updatedAt || 0) - (a.updatedAt || 0)
  );

  return (
    <div className="min-vh-100 d-flex flex-column" style={{ background: "var(--color-bg)" }}>
      <AppHeader actionLabel="Home" actionTo="/" />

      <div className="flex-grow-1 px-4 py-3">
        <div className="row g-3">
          <div className="col-xl-3 col-lg-4 d-flex flex-column gap-3">
            <UploadPanel onUploaded={handleUploaded} />

            {loadingDocs ? (
              <div className="card">
                <div className="card-body text-center py-4">
                  <div className="spinner-border spinner-border-sm text-primary" />
                  <p className="text-muted app-text-muted mb-0 mt-2">Loading documents...</p>
                </div>
              </div>
            ) : (
              <DocSelector
                documents={documents}
                selectedDocId={null}
                onSelect={() => {}}
                onDeleted={handleDeleted}
                readOnly={true}
              />
            )}

            <ConversationHistory
              conversations={sortedConversations}
              activeConversationId={activeConversationId}
              onSelect={setActiveConversationId}
              onDelete={handleDeleteConversation}
            />

            <Sidebar documents={documents} sessionId={sessionId} />
          </div>
          <div className="col-xl-9 col-lg-8">
            <ChatPanel
              sessionId={sessionId}
              messages={activeConversation?.messages || []}
              onMessagesChange={updateActiveMessages}
              onNewChat={handleNewChat}
              onAnswer={() => {}}
              hasDocuments={documents.length > 0}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
