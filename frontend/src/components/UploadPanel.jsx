import { useState, useRef } from 'react';
import { uploadPDF } from '../api/client.js';
import ApiKeyPrompt from './ApiKeyPrompt.jsx';
import './UploadPanel.css';
import demoAnalysis from '../data/demo_analysis.json';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

/**
 * UploadPanel
 *
 * Props:
 *   onDataLoaded(transactionCount, isDemoMode) — called after a successful upload or
 *   demo load so the parent (App.jsx) can transition to Dashboard view.
 */
function UploadPanel({ onDataLoaded }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [showApiKeyPrompt, setShowApiKeyPrompt] = useState(false);
  const [userApiKey, setUserApiKey] = useState(null);
  const fileInputRef = useRef(null);

  // ─── helpers ────────────────────────────────────────────────────────────────

  function clearMessages() {
    setError('');
    setSuccess('');
  }

  // ─── file selection & validation ────────────────────────────────────────────

  function handleFileChange(e) {
    clearMessages();
    const file = e.target.files[0];
    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (file.type !== 'application/pdf') {
      setError('Only PDF files are accepted. Please select a valid PDF.');
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError('File exceeds the 10 MB size limit. Please use a smaller PDF.');
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setSelectedFile(file);
  }

  // ─── upload PDF ─────────────────────────────────────────────────────────────

  async function handleUpload(e) {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a PDF file before uploading.');
      return;
    }

    clearMessages();
    setLoading(true);
    try {
      const result = await uploadPDF(selectedFile, userApiKey);
      const count = result.transaction_count ?? 0;
      setSuccess(`Successfully imported ${count} transaction${count !== 1 ? 's' : ''}.`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (onDataLoaded) onDataLoaded(count);
    } catch (err) {
      const status = err.status;
      if (status === 429) {
        setShowApiKeyPrompt(true);
      } else if (status === 415 || (err.message && err.message.toLowerCase().includes('pdf'))) {
        setError('The file could not be processed. Make sure it is a valid bank statement PDF.');
      } else {
        setError(err.message || 'An unexpected error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  // ─── load sample data ────────────────────────────────────────────────────────

  function handleLoadDemo() {
    clearMessages();
    
    // Load pre-computed demo analysis instantly (no API call)
    try {
      const count = demoAnalysis.metadata.total_transactions;
      
      // Store demo data in sessionStorage for dashboard to read
      sessionStorage.setItem('demoAnalysis', JSON.stringify(demoAnalysis));
      
      setSuccess(`Demo data loaded instantly — ${count} transactions ready.`);
      
      // Notify parent with isDemoMode=true
      if (onDataLoaded) onDataLoaded(count, true);
    } catch (err) {
      setError('Failed to load demo data. Please try again.');
    }
  }

  // ─── API key prompt handlers ─────────────────────────────────────────────────

  function handleApiKeySubmit(apiKey) {
    setUserApiKey(apiKey);
    setShowApiKeyPrompt(false);
    setError('');
    // Retry the upload with the new key
    if (selectedFile) {
      handleUpload({ preventDefault: () => {} });
    }
  }

  function handleApiKeyDismiss() {
    setShowApiKeyPrompt(false);
    setError('Rate limit reached. Please try again later or use your own API key.');
  }

  // ─── render ─────────────────────────────────────────────────────────────────

  return (
    <div className="upload-panel" role="main">
      <div className="upload-panel__header">
        <h1 className="upload-panel__title">Nepali Finance Analyzer</h1>
        <p className="upload-panel__subtitle">
          AI-powered spending analysis for your bank statements
        </p>
      </div>

      {/* Primary CTA - Upload */}
      <div className="upload-panel__content upload-panel__content--primary">
        <h2 className="upload-panel__section-title">Upload Your Statement</h2>
        <p className="upload-panel__section-subtitle">
          Analyze your own Nabil, NMB, Kumari, or other Nepal bank statement
        </p>

        <form onSubmit={handleUpload} noValidate>
          <label htmlFor="pdf-file-input" className="upload-panel__file-label">
            Select PDF bank statement
          </label>
          <input
            id="pdf-file-input"
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            onChange={handleFileChange}
            disabled={loading}
            className="upload-panel__file-input"
            aria-describedby="pdf-privacy-notice"
          />

          {selectedFile && (
            <p className="upload-panel__selected-file">
              Selected: <strong>{selectedFile.name}</strong>{' '}
              ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
            </p>
          )}

          {/* Privacy notice */}
          <p id="pdf-privacy-notice" className="upload-panel__privacy-notice">
            🔒 Your PDF is processed locally and deleted immediately after extraction. We never store your financial data.
          </p>

          <button
            type="submit"
            className="upload-panel__btn upload-panel__btn--primary"
            disabled={loading || !selectedFile}
          >
            {loading ? (
              <span className="upload-panel__loading" aria-live="polite">
                <span className="upload-panel__spinner" aria-hidden="true" />
                Processing…
              </span>
            ) : (
              'Upload & Analyze'
            )}
          </button>
        </form>
      </div>

      {/* Secondary CTA - Demo */}
      <div className="upload-panel__divider">
        <span>or</span>
      </div>

      <div className="upload-panel__content upload-panel__content--secondary">
        <button
          type="button"
          className="upload-panel__btn upload-panel__btn--demo"
          onClick={handleLoadDemo}
          disabled={loading}
        >
          <span className="upload-panel__demo-icon" aria-hidden="true">⚡</span>
          Try with Demo Data →
        </button>
        <p className="upload-panel__demo-subtitle">
          See how it works instantly — no upload needed
        </p>
      </div>

      {/* Status messages */}
      {error && (
        <div className="upload-panel__message upload-panel__message--error" role="alert">
          {error}
        </div>
      )}
      {success && (
        <div className="upload-panel__message upload-panel__message--success" role="status">
          {success}
        </div>
      )}

      {/* User API key indicator */}
      {userApiKey && (
        <div className="upload-panel__api-key-active" role="status">
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
    </div>
  );
}

export default UploadPanel;
