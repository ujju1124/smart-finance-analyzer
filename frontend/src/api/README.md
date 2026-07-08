# API Client Module

This module provides a centralized API client for communicating with the Nepali Finance Analyzer backend.

## Configuration

The API base URL is configurable via environment variables:

```env
VITE_API_BASE_URL=http://localhost:8000
```

In development, the default is `http://localhost:8000`. For production, update the `.env` file with your production API URL.

## Available Functions

### `uploadPDF(file)`

Upload a PDF bank statement for processing.

**Parameters:**
- `file` (File): The PDF file to upload

**Returns:**
```javascript
{
  success: boolean,
  transaction_count: number,
  errors: string[],
  message?: string
}
```

**Example:**
```javascript
import { uploadPDF } from './api/client.js';

const file = event.target.files[0];
try {
  const result = await uploadPDF(file);
  console.log(`Uploaded ${result.transaction_count} transactions`);
} catch (error) {
  console.error('Upload failed:', error.message);
}
```

### `loadSampleData()`

Load bundled sample transaction data.

**Returns:**
```javascript
{
  success: boolean,
  transaction_count: number,
  message: string
}
```

**Example:**
```javascript
import { loadSampleData } from './api/client.js';

try {
  const result = await loadSampleData();
  console.log(`Loaded ${result.transaction_count} sample transactions`);
} catch (error) {
  console.error('Failed to load sample data:', error.message);
}
```

### `getTransactions(filters)`

Retrieve transactions with optional filters.

**Parameters:**
- `filters` (object, optional):
  - `date_from` (string): Filter from date (YYYY-MM-DD)
  - `date_to` (string): Filter to date (YYYY-MM-DD)
  - `category` (string): Filter by category
  - `direction` (string): Filter by direction ('debit' or 'credit')

**Returns:**
```javascript
{
  transactions: Array<Transaction>,
  total_count: number
}
```

**Example:**
```javascript
import { getTransactions } from './api/client.js';

// Get all transactions
const all = await getTransactions();

// Get filtered transactions
const filtered = await getTransactions({
  date_from: '2024-01-01',
  date_to: '2024-01-31',
  category: 'Food & Dining',
  direction: 'debit'
});
```

### `getAnalytics(patternType)`

Get analytics data for a specific pattern type.

**Parameters:**
- `patternType` (string): One of:
  - `'day-of-week'`: Spending patterns by day of week
  - `'monthly-trend'`: Monthly spending trends
  - `'category-breakdown'`: Spending distribution by category
  - `'anomalies'`: Unusual spending spikes

**Returns:**
```javascript
{
  data: object,      // Structure varies by pattern type
  insight: string    // AI-generated one-sentence insight
}
```

**Example:**
```javascript
import { getAnalytics } from './api/client.js';

try {
  const dayOfWeek = await getAnalytics('day-of-week');
  console.log('Data:', dayOfWeek.data);
  console.log('Insight:', dayOfWeek.insight);
} catch (error) {
  console.error('Analytics failed:', error.message);
}
```

### `sendChatMessage(message)`

Send a chat message and get a RAG-based response about spending patterns.

**Parameters:**
- `message` (string): The user's question (1-500 characters)

**Returns:**
```javascript
{
  response: string,
  error?: string
}
```

**Example:**
```javascript
import { sendChatMessage } from './api/client.js';

try {
  const result = await sendChatMessage('How much did I spend on groceries last month?');
  console.log('AI Response:', result.response);
} catch (error) {
  if (error.status === 429) {
    console.error('Rate limit reached. Please try again later.');
  } else {
    console.error('Chat error:', error.message);
  }
}
```

## Error Handling

All functions throw errors with the following structure:

```javascript
{
  message: string,    // Human-readable error message
  status?: number,    // HTTP status code (if applicable)
  data?: object       // Additional error details from server
}
```

**Common Error Scenarios:**

1. **Network Errors**: Connection failures
   ```javascript
   error.message === 'Network error: Unable to connect to the server'
   ```

2. **HTTP 400**: Bad Request (invalid input)
   ```javascript
   error.status === 400
   ```

3. **HTTP 404**: No transactions exist
   ```javascript
   error.status === 404
   ```

4. **HTTP 429**: Rate limit exceeded
   ```javascript
   error.status === 429
   error.message === 'Rate limit reached. Please try again in a few minutes.'
   ```

5. **HTTP 500**: Server error
   ```javascript
   error.status === 500
   ```

## Testing

Run unit tests:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

Run tests with UI:
```bash
npm run test:ui
```

## Development vs Production

**Development:**
```env
VITE_API_BASE_URL=http://localhost:8000
```

**Production:**
```env
VITE_API_BASE_URL=https://your-production-domain.com
```

Make sure to update the `.env` file before building for production:
```bash
npm run build
```

## API Endpoints Reference

| Function | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| `uploadPDF` | POST | `/api/upload` | Upload PDF statement |
| `loadSampleData` | GET | `/api/sample` | Load sample data |
| `getTransactions` | GET | `/api/transactions` | List/filter transactions |
| `getAnalytics` | GET | `/api/analytics/{type}` | Get analytics |
| `sendChatMessage` | POST | `/api/chat` | RAG chat |

## Rate Limits

The backend uses Groq API with free tier limits:
- **llama-3.3-70b**: ~1,000 requests/day, 100K tokens/day
- **llama-3.1-8b**: ~14,400 requests/day

If rate limits are exceeded, the API will return HTTP 429 with a clear error message asking the user to retry later.
