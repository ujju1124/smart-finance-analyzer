/**
 * Unit tests for UploadPanel component
 *
 * Covers:
 * - Tab toggle rendering and switching (Req 17.1)
 * - Upload PDF tab: file input, validation, privacy notice (Req 17.3, 17.4, 1.1)
 * - Sample data tab: load button (Req 17.2)
 * - Loading state during API calls
 * - Success message with transaction count
 * - Error messages (file type, size limit, rate limit, processing errors)
 * - onDataLoaded callback invocation
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UploadPanel from './UploadPanel.jsx';

// ─── Mock the API client ──────────────────────────────────────────────────────
vi.mock('../api/client.js', () => ({
  uploadPDF: vi.fn(),
  loadSampleData: vi.fn(),
}));

import { uploadPDF, loadSampleData } from '../api/client.js';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function makePDF(name = 'statement.pdf', size = 1024) {
  // Create a File whose .type is application/pdf and whose .size matches
  const file = new File(['x'.repeat(size)], name, { type: 'application/pdf' });
  return file;
}

function renderPanel(props = {}) {
  const onDataLoaded = props.onDataLoaded ?? vi.fn();
  const utils = render(<UploadPanel onDataLoaded={onDataLoaded} {...props} />);
  return { ...utils, onDataLoaded };
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('UploadPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ── Tab rendering (Req 17.1) ─────────────────────────────────────────────

  describe('Tab toggle', () => {
    it('renders both tabs', () => {
      renderPanel();
      expect(screen.getByRole('tab', { name: /upload pdf/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /use sample data/i })).toBeInTheDocument();
    });

    it('defaults to "Upload PDF" tab selected', () => {
      renderPanel();
      expect(screen.getByRole('tab', { name: /upload pdf/i })).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByRole('tab', { name: /use sample data/i })).toHaveAttribute('aria-selected', 'false');
    });

    it('switches to "Use Sample Data" tab on click', async () => {
      renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      expect(screen.getByRole('tab', { name: /use sample data/i })).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByRole('tab', { name: /upload pdf/i })).toHaveAttribute('aria-selected', 'false');
    });

    it('shows file input when "Upload PDF" tab is active', () => {
      renderPanel();
      expect(screen.getByLabelText(/select pdf bank statement/i)).toBeInTheDocument();
    });

    it('hides file input when "Use Sample Data" tab is active', async () => {
      renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      expect(screen.queryByLabelText(/select pdf bank statement/i)).not.toBeVisible();
    });

    it('shows "Load Sample Data" button when sample tab is active', async () => {
      renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      expect(screen.getByRole('button', { name: /load sample data/i })).toBeInTheDocument();
    });

    it('clears error messages when switching tabs', async () => {
      renderPanel();
      // Trigger a file-type error via fireEvent (bypasses userEvent's accept filtering)
      const input = screen.getByLabelText(/select pdf bank statement/i);
      const badFile = new File(['data'], 'doc.txt', { type: 'text/plain' });
      await act(async () => {
        fireEvent.change(input, { target: { files: [badFile] } });
      });
      expect(screen.getByRole('alert')).toBeInTheDocument();

      // Switch tab — error should be gone
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  // ── Privacy notice (Req 17.4) ────────────────────────────────────────────

  describe('Privacy notice', () => {
    it('displays the privacy notice on the upload tab', () => {
      renderPanel();
      expect(
        screen.getByText(/your pdf will be processed locally and deleted immediately after extraction/i)
      ).toBeInTheDocument();
    });
  });

  // ── File validation (Req 1.1, 17.3) ─────────────────────────────────────

  describe('File validation', () => {
    it('accepts a valid PDF under 10 MB', async () => {
      renderPanel();
      const file = makePDF('statement.pdf', 1024);
      const input = screen.getByLabelText(/select pdf bank statement/i);
      await userEvent.upload(input, file);
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      expect(screen.getByText(/selected:/i)).toBeInTheDocument();
    });

    it('rejects a non-PDF file', async () => {
      renderPanel();
      // Use fireEvent.change to bypass userEvent's accept-attribute filtering in jsdom
      const badFile = new File(['data'], 'doc.txt', { type: 'text/plain' });
      const input = screen.getByLabelText(/select pdf bank statement/i);
      await act(async () => {
        fireEvent.change(input, { target: { files: [badFile] } });
      });
      expect(screen.getByRole('alert')).toHaveTextContent(/only pdf files are accepted/i);
    });

    it('rejects a PDF over 10 MB', async () => {
      renderPanel();
      const bigFile = makePDF('big.pdf', 10 * 1024 * 1024 + 1);
      const input = screen.getByLabelText(/select pdf bank statement/i);
      await userEvent.upload(input, bigFile);
      expect(screen.getByRole('alert')).toHaveTextContent(/10 mb size limit/i);
    });

    it('disables the upload button when no file is selected', () => {
      renderPanel();
      const btn = screen.getByRole('button', { name: /upload/i });
      expect(btn).toBeDisabled();
    });

    it('enables the upload button after a valid file is selected', async () => {
      renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      expect(screen.getByRole('button', { name: /upload/i })).not.toBeDisabled();
    });
  });

  // ── Upload PDF success ───────────────────────────────────────────────────

  describe('Upload PDF — success', () => {
    it('shows loading state during upload', async () => {
      uploadPDF.mockReturnValue(new Promise(() => {})); // never resolves
      renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      await userEvent.click(screen.getByRole('button', { name: /upload/i }));
      expect(screen.getByText(/processing/i)).toBeInTheDocument();
    });

    it('displays success message with transaction count', async () => {
      uploadPDF.mockResolvedValueOnce({ success: true, transaction_count: 42, errors: [] });
      const { onDataLoaded } = renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      await userEvent.click(screen.getByRole('button', { name: /upload/i }));

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/42 transactions/i);
      });
    });

    it('calls onDataLoaded with transaction count on success', async () => {
      uploadPDF.mockResolvedValueOnce({ success: true, transaction_count: 55, errors: [] });
      const { onDataLoaded } = renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      await userEvent.click(screen.getByRole('button', { name: /upload/i }));

      await waitFor(() => {
        expect(onDataLoaded).toHaveBeenCalledWith(55);
      });
    });

    it('handles singular "transaction" wording when count is 1', async () => {
      uploadPDF.mockResolvedValueOnce({ success: true, transaction_count: 1, errors: [] });
      renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      await userEvent.click(screen.getByRole('button', { name: /upload/i }));

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/1 transaction\b/i);
      });
    });
  });

  // ── Upload PDF errors ────────────────────────────────────────────────────

  describe('Upload PDF — errors', () => {
    it('shows a generic error message on failure', async () => {
      const err = new Error('Server error');
      uploadPDF.mockRejectedValueOnce(err);
      renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      await userEvent.click(screen.getByRole('button', { name: /upload/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/server error/i);
      });
    });

    it('shows rate limit message on HTTP 429', async () => {
      const err = new Error('Too many requests');
      err.status = 429;
      uploadPDF.mockRejectedValueOnce(err);
      renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      await userEvent.click(screen.getByRole('button', { name: /upload/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/rate limit reached/i);
      });
    });

    it('shows file processing error on HTTP 415', async () => {
      const err = new Error('Unsupported media type');
      err.status = 415;
      uploadPDF.mockRejectedValueOnce(err);
      renderPanel();
      const file = makePDF();
      await userEvent.upload(screen.getByLabelText(/select pdf bank statement/i), file);
      await userEvent.click(screen.getByRole('button', { name: /upload/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/could not be processed/i);
      });
    });
  });

  // ── Sample data (Req 17.2) ───────────────────────────────────────────────

  describe('Load Sample Data', () => {
    it('shows loading state during sample data load', async () => {
      loadSampleData.mockReturnValue(new Promise(() => {}));
      renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      await userEvent.click(screen.getByRole('button', { name: /load sample data/i }));
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('displays success message with transaction count', async () => {
      loadSampleData.mockResolvedValueOnce({ success: true, transaction_count: 120, message: 'Loaded' });
      renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      await userEvent.click(screen.getByRole('button', { name: /load sample data/i }));

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent(/120 transactions/i);
      });
    });

    it('calls onDataLoaded with transaction count on success', async () => {
      loadSampleData.mockResolvedValueOnce({ success: true, transaction_count: 120, message: 'Loaded' });
      const { onDataLoaded } = renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      await userEvent.click(screen.getByRole('button', { name: /load sample data/i }));

      await waitFor(() => {
        expect(onDataLoaded).toHaveBeenCalledWith(120);
      });
    });

    it('shows rate limit error on HTTP 429', async () => {
      const err = new Error('Rate limited');
      err.status = 429;
      loadSampleData.mockRejectedValueOnce(err);
      renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      await userEvent.click(screen.getByRole('button', { name: /load sample data/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/rate limit reached/i);
      });
    });

    it('shows generic error on other failures', async () => {
      loadSampleData.mockRejectedValueOnce(new Error('Network error: Unable to connect'));
      renderPanel();
      await userEvent.click(screen.getByRole('tab', { name: /use sample data/i }));
      await userEvent.click(screen.getByRole('button', { name: /load sample data/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/network error/i);
      });
    });
  });
});
