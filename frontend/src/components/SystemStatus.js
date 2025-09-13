import React, { useState } from 'react';

const SystemStatus = ({ status, onRefresh }) => {
  const [isCollapsed, setIsCollapsed] = useState(true);

  if (!status) return null;

  const getStatusIcon = (systemStatus) => {
    if (systemStatus === 'healthy') return '✅';
    if (systemStatus === 'unhealthy') return '❌';
    return '⚠️';
  };

  const getStatusColor = (systemStatus) => {
    if (systemStatus === 'healthy') return '#28a745';
    if (systemStatus === 'unhealthy') return '#dc3545';
    return '#ffc107';
  };

  return (
    <div className="system-status">
      <div className="status-header" onClick={() => setIsCollapsed(!isCollapsed)}>
        <div className="status-main">
          <span className="status-icon">
            {getStatusIcon(status.overall_status)}
          </span>
          <span className="status-text" style={{ color: getStatusColor(status.overall_status) }}>
            System Status: {status.overall_status}
          </span>
        </div>
        <div className="status-controls">
          <button onClick={onRefresh} className="refresh-button" title="Refresh Status">
            🔄
          </button>
          <button className="toggle-button">
            {isCollapsed ? '▼' : '▲'}
          </button>
        </div>
      </div>

      {!isCollapsed && (
        <div className="status-details">
          <div className="integration-status">
            <div className="integration-item">
              <div className="integration-header">
                <span className="integration-icon">
                  {getStatusIcon(status.jira?.status)}
                </span>
                <span className="integration-name">JIRA</span>
              </div>
              <div className="integration-info">
                <span className={`status-badge ${status.jira?.status}`}>
                  {status.jira?.status}
                </span>
                <div className="integration-details">
                  <span>Configured: {status.jira?.configured ? 'Yes' : 'No'}</span>
                  <span>Connected: {status.jira?.connected ? 'Yes' : 'No'}</span>
                </div>
              </div>
            </div>

            <div className="integration-item">
              <div className="integration-header">
                <span className="integration-icon">
                  {getStatusIcon(status.github?.status)}
                </span>
                <span className="integration-name">GitHub</span>
              </div>
              <div className="integration-info">
                <span className={`status-badge ${status.github?.status}`}>
                  {status.github?.status}
                </span>
                <div className="integration-details">
                  <span>Configured: {status.github?.configured ? 'Yes' : 'No'}</span>
                  <span>Connected: {status.github?.connected ? 'Yes' : 'No'}</span>
                </div>
              </div>
            </div>
          </div>

          {status.overall_status !== 'healthy' && (
            <div className="status-help">
              <h4>Need Help?</h4>
              <ul>
                {!status.jira?.configured && (
                  <li>Configure JIRA by setting JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in your environment</li>
                )}
                {!status.github?.configured && (
                  <li>Configure GitHub by setting GITHUB_TOKEN in your environment</li>
                )}
                {(status.jira?.configured && !status.jira?.connected) && (
                  <li>Check your JIRA credentials and server URL</li>
                )}
                {(status.github?.configured && !status.github?.connected) && (
                  <li>Verify your GitHub token has the correct permissions</li>
                )}
              </ul>
            </div>
          )}

          {status.timestamp && (
            <div className="status-timestamp">
              Last updated: {new Date(status.timestamp).toLocaleString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SystemStatus;
