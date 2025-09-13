import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import SystemStatus from './components/SystemStatus';
import './styles/App.css';

function App() {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/activity/status');
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Error fetching system status:', error);
      setSystemStatus({
        jira: { status: 'unhealthy', configured: false },
        github: { status: 'unhealthy', configured: false },
        overall_status: 'unhealthy'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Team Activity Monitor</h1>
        <p>Ask me about your team's activity across JIRA and GitHub</p>
      </header>

      <main className="App-main">
        {loading ? (
          <div className="loading">Loading system status...</div>
        ) : (
          <>
            <SystemStatus status={systemStatus} onRefresh={fetchSystemStatus} />
            <Chat systemStatus={systemStatus} />
          </>
        )}
      </main>

      <footer className="App-footer">
        <p>Team Activity Monitor - Monitor your team's productivity across JIRA and GitHub</p>
      </footer>
    </div>
  );
}

export default App;
