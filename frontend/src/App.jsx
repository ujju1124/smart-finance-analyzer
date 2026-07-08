import { useState } from 'react';
import UploadPanel from './components/UploadPanel.jsx';
import Dashboard from './components/Dashboard.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import DemoBanner from './components/DemoBanner.jsx';
import './App.css';

/**
 * App
 *
 * Top-level view controller.
 * Views:
 *   'upload'    — UploadPanel (initial state, data not yet loaded)
 *   'dashboard' — Dashboard + ChatPanel side-by-side
 *
 * Demo mode: when isDemoMode is true, loads pre-computed demo data instantly
 * without any API calls and shows a demo banner at the top.
 */
function App() {
  const [view, setView] = useState('upload');
  const [transactionCount, setTransactionCount] = useState(0);
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [showChat, setShowChat] = useState(false);

  function handleDataLoaded(count, isDemo = false) {
    setTransactionCount(count);
    setIsDemoMode(isDemo);
    setView('dashboard');
  }

  function handleReset() {
    setView('upload');
    setIsDemoMode(false);
    setTransactionCount(0);
    setShowChat(false);
  }

  function toggleChat() {
    setShowChat(!showChat);
    // Scroll to chat panel after a brief delay to let it render
    if (!showChat) {
      setTimeout(() => {
        const chatPanel = document.querySelector('.chat-panel');
        if (chatPanel) {
          chatPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 100);
    }
  }

  if (view === 'upload') {
    return <UploadPanel onDataLoaded={handleDataLoaded} />;
  }

  return (
    <div className={`app-dashboard ${showChat ? 'chat-visible' : ''}`}>
      {isDemoMode && <DemoBanner onUploadClick={handleReset} />}
      <Dashboard 
        transactionCount={transactionCount} 
        onReset={handleReset}
        isDemoMode={isDemoMode}
        showChat={showChat}
        onToggleChat={toggleChat}
      />
      {showChat && <ChatPanel isDemoMode={isDemoMode} />}
    </div>
  );
}

export default App;
