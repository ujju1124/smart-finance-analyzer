/**
 * Unit tests for API client module
 * 
 * Note: These tests verify the structure and error handling of the API client.
 * They use mocks to avoid actual network calls.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  uploadPDF,
  loadSampleData,
  getTransactions,
  getAnalytics,
  sendChatMessage,
  API_BASE_URL,
} from './client.js';

// Mock fetch globally
global.fetch = vi.fn();

describe('API Client', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('uploadPDF', () => {
    it('should send PDF file as FormData to /api/upload', async () => {
      const mockFile = new File(['pdf content'], 'statement.pdf', { type: 'application/pdf' });
      const mockResponse = { success: true, transaction_count: 42, errors: [] };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await uploadPDF(mockFile);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/upload`,
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle upload errors', async () => {
      const mockFile = new File(['pdf content'], 'statement.pdf', { type: 'application/pdf' });

      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'File must be a PDF' }),
      });

      await expect(uploadPDF(mockFile)).rejects.toThrow('File must be a PDF');
    });
  });

  describe('loadSampleData', () => {
    it('should call GET /api/sample', async () => {
      const mockResponse = { success: true, transaction_count: 120, message: 'Sample data loaded' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await loadSampleData();

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/sample`,
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getTransactions', () => {
    it('should call GET /api/transactions without filters', async () => {
      const mockResponse = { transactions: [], total_count: 0 };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getTransactions();

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/transactions`,
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should call GET /api/transactions with query parameters', async () => {
      const mockResponse = { transactions: [], total_count: 0 };
      const filters = {
        date_from: '2024-01-01',
        date_to: '2024-01-31',
        category: 'Food & Dining',
        direction: 'debit',
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getTransactions(filters);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/transactions?date_from=2024-01-01&date_to=2024-01-31&category=Food+%26+Dining&direction=debit`,
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should filter out empty filter values', async () => {
      const mockResponse = { transactions: [], total_count: 0 };
      const filters = {
        date_from: '2024-01-01',
        date_to: '',
        category: null,
        direction: undefined,
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await getTransactions(filters);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/transactions?date_from=2024-01-01`,
        expect.any(Object)
      );
    });
  });

  describe('getAnalytics', () => {
    it('should call GET /api/analytics/{patternType}', async () => {
      const mockResponse = { data: { monday: 1000 }, insight: 'You spend most on Fridays' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getAnalytics('day-of-week');

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/analytics/day-of-week`,
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should validate pattern type', async () => {
      await expect(getAnalytics('invalid-pattern')).rejects.toThrow('Invalid pattern type');
    });

    it('should accept all valid pattern types', async () => {
      const validPatterns = ['day-of-week', 'monthly-trend', 'category-breakdown', 'anomalies'];
      const mockResponse = { data: {}, insight: '' };

      for (const pattern of validPatterns) {
        global.fetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        });

        await expect(getAnalytics(pattern)).resolves.toBeDefined();
      }
    });
  });

  describe('sendChatMessage', () => {
    it('should send POST /api/chat with message', async () => {
      const mockResponse = { response: 'You spent NPR 5000 on groceries last month' };
      const message = 'How much did I spend on groceries?';

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await sendChatMessage(message);

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat`,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message }),
        })
      );
      expect(result).toEqual(mockResponse);
    });

    it('should trim message whitespace', async () => {
      const mockResponse = { response: 'Answer' };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      await sendChatMessage('  message with spaces  ');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({ message: 'message with spaces' }),
        })
      );
    });

    it('should reject empty messages', async () => {
      await expect(sendChatMessage('')).rejects.toThrow('Message cannot be empty');
      await expect(sendChatMessage('   ')).rejects.toThrow('Message cannot be empty');
    });

    it('should reject messages over 500 characters', async () => {
      const longMessage = 'a'.repeat(501);
      await expect(sendChatMessage(longMessage)).rejects.toThrow('Message cannot exceed 500 characters');
    });

    it('should handle rate limit errors', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 429,
        json: async () => ({ detail: 'Rate limit reached. Please try again in a few minutes.' }),
      });

      await expect(sendChatMessage('test')).rejects.toThrow('Rate limit reached');
    });
  });

  describe('Error handling', () => {
    it('should handle network errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network failure'));

      await expect(loadSampleData()).rejects.toThrow('Network error');
    });

    it('should handle HTTP error responses', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ detail: 'Internal server error' }),
      });

      const error = await loadSampleData().catch((e) => e);
      expect(error.status).toBe(500);
      expect(error.message).toContain('Internal server error');
    });

    it('should handle responses without detail field', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: 'Bad request' }),
      });

      await expect(loadSampleData()).rejects.toThrow('Bad request');
    });

    it('should provide default error message when no message is provided', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({}),
      });

      await expect(loadSampleData()).rejects.toThrow('Request failed');
    });
  });
});
