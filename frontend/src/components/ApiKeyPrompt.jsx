import { useState } from 'react';
import './ApiKeyPrompt.css';

/**
 * ApiKeyPrompt
 * 
 * Displays when rate limit is reached, allowing user to provide their own Groq API key.
 * 
 * Props:
 *   onSubmit(apiKey) — called when user submits their API key
 *   onDismiss() — called when user dismisses the prompt
 * 
 * SECURITY NOTE:
 * - User API key is held ONLY in React state (session memory)
 * - Never persisted to localStorage, sessionStorage, or sent to backend database
 * - Cleared on component unmount or when user loads different data
 * - Only sent as X-Groq-API-Key header with API requests during this session
 * - This preserves the "documents are not stored" privacy claim
 */
function ApiKeyPrompt({ onSubmit, onDismiss }) {
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = apiKey.trim();
    if (!trimmed) return;

    setLoading(true);
    onSubmit(trimmed);
    // Parent component will handle loading state
  }

  return (
    <div className="api-key-prompt" role="dialog" aria-labelledby="api-key-title" aria-modal="true">
      <div className="api-key-prompt__backdrop" onClick={onDismiss} />
      <div className="api-key-prompt__card">
        <h3 id="api-key-title" className="api-key-prompt__title">
          ⚠️ Rate Limit Reached
        </h3>
        <p className="api-key-prompt__description">
          AI insights temporarily unavailable. Enter your free Groq API key to continue:
        </p>

        <form onSubmit={handleSubmit} className="api-key-prompt__form">
          <input
            type="text"
            className="api-key-prompt__input"
            placeholder="gsk_..."
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            disabled={loading}
            aria-label="Groq API key"
            autoFocus
          />
          
          <div className="api-key-prompt__actions">
            <button
              type="button"
              className="api-key-prompt__btn api-key-prompt__btn--secondary"
              onClick={onDismiss}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="api-key-prompt__btn api-key-prompt__btn--primary"
              disabled={!apiKey.trim() || loading}
            >
              {loading ? 'Connecting...' : 'Use My Key'}
            </button>
          </div>
        </form>

        <p className="api-key-prompt__help">
          <a
            href="https://console.groq.com"
            target="_blank"
            rel="noopener noreferrer"
            className="api-key-prompt__link"
          >
            Get a free key at console.groq.com
          </a>
          {' '}— takes 30 seconds.
        </p>

        <p className="api-key-prompt__privacy">
          🔒 Your key is used only for this session and never stored.
        </p>
      </div>
    </div>
  );
}

export default ApiKeyPrompt;
