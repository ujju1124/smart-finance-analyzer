import { useState } from 'react';
import './DemoBanner.css';

/**
 * DemoBanner
 * 
 * Persistent banner shown at the top of the dashboard in demo mode.
 * Informs users they're viewing AI-generated sample data and provides
 * options to upload their own statement or view the demo PDF.
 * 
 * Props:
 *   onUploadClick() - callback to return to upload screen
 */
function DemoBanner({ onUploadClick }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <div className="demo-banner" role="alert">
      <div className="demo-banner__content">
        <div className="demo-banner__main">
          <span className="demo-banner__icon" aria-hidden="true">📊</span>
          <div className="demo-banner__text">
            <strong>Demo Mode</strong> — You're viewing AI-generated sample data.
          </div>
          <div className="demo-banner__actions">
            <button
              type="button"
              className="demo-banner__btn demo-banner__btn--primary"
              onClick={onUploadClick}
            >
              Upload My Statement
            </button>
            <a
              href="/demo_bank_statement.pdf"
              download="demo_bank_statement.pdf"
              className="demo-banner__btn demo-banner__btn--secondary"
            >
              Download Demo PDF
            </a>
            <button
              type="button"
              className="demo-banner__btn demo-banner__btn--link"
              onClick={() => setShowDetails(!showDetails)}
              aria-expanded={showDetails}
            >
              {showDetails ? 'Hide details' : 'About this data'} {showDetails ? '▲' : '▼'}
            </button>
          </div>
        </div>

        {showDetails && (
          <div className="demo-banner__details">
            <p className="demo-banner__details-text">
              This demo uses AI-generated fictional transactions for a fictional account holder (<strong>Ram Bahadur Shrestha</strong>). No real financial data is used. The PDF was generated specifically to demonstrate the analyzer's capabilities across realistic spending categories and patterns found in typical Nepali bank statements.
            </p>
            <p className="demo-banner__details-text">
              <strong>Demo features:</strong> 296 transactions spanning 4 months • Realistic merchant names (Bhatbhateni, Daraz, Foodmandu, etc.) • Multiple categories (Groceries, Food & Dining, Transport, Utilities, Shopping) • Salary deposits and common expenses • Pattern analysis showing day-of-week trends, monthly spending, and anomaly detection.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DemoBanner;
