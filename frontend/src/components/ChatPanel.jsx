import { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../api/client.js';
import ApiKeyPrompt from './ApiKeyPrompt.jsx';
import './ChatPanel.css';

/**
 * ChatPanel
 *
 * Props:
 *   isDemoMode — whether we're in demo mode
 *
 * Renders a fixed-height conversational chat panel.
 * - Maintains a message history (user + assistant turns).
 * - Sends user messages to the /api/chat endpoint via sendChatMessage().
 * - Shows a loading indicator while a request is in-flight.
 * - Auto-scrolls to the latest message.
 * - Handles rate-limit errors (429) and general errors gracefully.
 */
function ChatPanel({ isDemoMode = false }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: isDemoMode 
        ? "Hi! You're in demo mode. I can answer questions about RAM BAHADUR SHRESTHA's spending from the demo data — for example: \"What did they spend most on?\" or \"Any unusual transactions?\""
        : 'Hi! Ask me anything about your transactions — for example: "What did I spend most on last month?" or "Any unusual spending this week?"',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showApiKeyPrompt, setShowApiKeyPrompt] = useState(false);
  const [userApiKey, setUserApiKey] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Scroll to latest message whenever messages update
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function handleSend(e) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    // Add user message immediately
    const userMsg = { role: 'user', text: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const result = await sendChatMessage(trimmed, userApiKey);
      const reply = result.response ?? result.message ?? 'No response received.';
      setMessages((prev) => [...prev, { role: 'assistant', text: reply }]);
    } catch (err) {
      let errText;
      if (err.status === 429) {
        setShowApiKeyPrompt(true);
        errText = 'Rate limit reached. Please provide your API key to continue.';
      } else {
        errText = err.message || 'Something went wrong. Please try again.';
      }
      setMessages((prev) => [...prev, { role: 'assistant', text: errText, isError: true }]);
    } finally {
      setLoading(false);
      // Restore focus to input after reply arrives
      inputRef.current?.focus();
    }
  }

  function handleApiKeySubmit(apiKey) {
    setUserApiKey(apiKey);
    setShowApiKeyPrompt(false);
    // Retry sending the last user message
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
    if (lastUserMsg) {
      handleSend({ preventDefault: () => {} });
    }
  }

  function handleApiKeyDismiss() {
    setShowApiKeyPrompt(false);
  }

  function handleKeyDown(e) {
    // Ctrl+Enter or Cmd+Enter to send
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      handleSend(e);
    }
  }

  return (
    <section className="chat-panel" aria-label="Chat with your data">
      <div className="chat-panel__header">
        <h2 className="chat-panel__title">Ask about your spending</h2>
      </div>

      {/* Scrollable message history */}
      <div className="chat-panel__messages" role="log" aria-live="polite">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`chat-panel__bubble chat-panel__bubble--${msg.role}${
              msg.isError ? ' chat-panel__bubble--error' : ''
            }`}
          >
            <span className="chat-panel__bubble-label">
              {msg.role === 'user' ? 'You' : 'Assistant'}
            </span>
            <p className="chat-panel__bubble-text">{msg.text}</p>
          </div>
        ))}

        {loading && (
          <div className="chat-panel__bubble chat-panel__bubble--assistant chat-panel__bubble--loading">
            <span className="chat-panel__bubble-label">Assistant</span>
            <span className="chat-panel__dots" aria-label="Thinking…">
              <span />
              <span />
              <span />
            </span>
          </div>
        )}

        {/* Sentinel element for auto-scroll */}
        <div ref={bottomRef} />
      </div>

      {/* Sticky input bar */}
      <form className="chat-panel__input-bar" onSubmit={handleSend} noValidate>
        <textarea
          ref={inputRef}
          className="chat-panel__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your transactions…"
          rows={2}
          maxLength={500}
          disabled={loading}
          aria-label="Message input"
        />
        <button
          type="submit"
          className="chat-panel__send-btn"
          disabled={!input.trim() || loading}
          aria-label="Send message"
        >
          Send
        </button>
      </form>
      <p className="chat-panel__hint">Press Ctrl+Enter to send</p>

      {/* User API key indicator */}
      {userApiKey && (
        <div className="chat-panel__api-key-active" role="status">
          ✓ Using your API key
        </div>
      )}

      {/* API key prompt modal */}
      {showApiKeyPrompt && (
        <ApiKeyPrompt
          onSubmit={handleApiKeySubmit}
          onDismiss={handleApiKeyDismiss}
        />
      )}
    </section>
  );
}

export default ChatPanel;
