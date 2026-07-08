/**
 * API Client for Nepali Finance Analyzer
 * 
 * Provides fetch wrapper functions for all backend endpoints.
 * API base URL is configurable for development vs production.
 */

// API base URL - configurable for different environments
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Base fetch wrapper with error handling
 * @param {string} url - The endpoint URL
 * @param {object} options - Fetch options
 * @param {string|null} userApiKey - Optional user-provided Groq API key (session only, never persisted)
 * @returns {Promise<object>} - Parsed JSON response
 * @throws {Error} - Network or HTTP errors with structured error messages
 */
async function fetchAPI(url, options = {}, userApiKey = null) {
  const headers = {
    ...options.headers,
  };
  
  // Add user API key header if provided (session only - never stored)
  if (userApiKey) {
    headers['X-Groq-API-Key'] = userApiKey;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    });

    // Parse response body
    const data = await response.json();

    // Handle HTTP error responses
    if (!response.ok) {
      const error = new Error(data.message || data.detail || 'Request failed');
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (error) {
    // Network errors or parsing errors
    if (!error.status) {
      error.message = 'Network error: Unable to connect to the server';
    }
    throw error;
  }
}

/**
 * Upload a PDF bank statement for processing
 * @param {File} file - The PDF file to upload
 * @param {string|null} userApiKey - Optional user-provided Groq API key
 * @returns {Promise<{success: boolean, transaction_count: number, errors: string[], message?: string}>}
 */
export async function uploadPDF(file, userApiKey = null) {
  const formData = new FormData();
  formData.append('file', file);

  return fetchAPI('/api/upload', {
    method: 'POST',
    body: formData,
    // Don't set Content-Type header - browser will set it with boundary for multipart/form-data
  }, userApiKey);
}

/**
 * Load bundled sample transaction data
 * @returns {Promise<{success: boolean, transaction_count: number, message: string}>}
 */
export async function loadSampleData() {
  return fetchAPI('/api/sample', {
    method: 'GET',
  });
}

/**
 * Get transactions with optional filters
 * @param {object} filters - Optional filter parameters
 * @param {string} filters.date_from - Filter transactions from this date (YYYY-MM-DD)
 * @param {string} filters.date_to - Filter transactions until this date (YYYY-MM-DD)
 * @param {string} filters.category - Filter by category
 * @param {string} filters.direction - Filter by direction ('debit' or 'credit')
 * @returns {Promise<{transactions: Array, total_count: number}>}
 */
export async function getTransactions(filters = {}) {
  // Build query parameters from filters
  const params = new URLSearchParams();
  
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      params.append(key, value);
    }
  });

  const queryString = params.toString();
  const url = queryString ? `/api/transactions?${queryString}` : '/api/transactions';

  return fetchAPI(url, {
    method: 'GET',
  });
}

/**
 * Get analytics data for a specific pattern type
 * @param {string} patternType - The analytics pattern type
 *   Options: 'day-of-week', 'monthly-trend', 'category-breakdown', 'anomalies', 'transactions-timeline'
 * @param {string|null} userApiKey - Optional user-provided Groq API key
 * @returns {Promise<{data: object, insight: string}>}
 */
export async function getAnalytics(patternType, userApiKey = null) {
  // Validate pattern type
  const validPatterns = ['day-of-week', 'monthly-trend', 'category-breakdown', 'anomalies', 'transactions-timeline'];
  if (!validPatterns.includes(patternType)) {
    throw new Error(`Invalid pattern type: ${patternType}. Must be one of: ${validPatterns.join(', ')}`);
  }

  return fetchAPI(`/api/analytics/${patternType}`, {
    method: 'GET',
  }, userApiKey);
}

/**
 * Send a chat message and get RAG-based response
 * @param {string} message - The user's question/message
 * @param {string|null} userApiKey - Optional user-provided Groq API key
 * @returns {Promise<{response: string, error?: string}>}
 */
export async function sendChatMessage(message, userApiKey = null) {
  if (!message || message.trim().length === 0) {
    throw new Error('Message cannot be empty');
  }

  if (message.length > 500) {
    throw new Error('Message cannot exceed 500 characters');
  }

  return fetchAPI('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: message.trim() }),
  }, userApiKey);
}

/**
 * Clear all transactions from the database
 * Note: This is typically called internally when loading new data
 * @returns {Promise<{success: boolean}>}
 */
export async function clearTransactions() {
  return fetchAPI('/api/transactions/clear', {
    method: 'DELETE',
  });
}

// Export API base URL for reference
export { API_BASE_URL };
