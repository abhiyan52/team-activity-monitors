import React, { useState } from 'react';

const Message = ({ message }) => {
  const [showDetails, setShowDetails] = useState(false);

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const renderJiraDetails = (jiraData) => {
    if (!jiraData || !jiraData.issues || jiraData.issues.length === 0) {
      return <p>No JIRA issues found.</p>;
    }

    return (
      <div className="jira-details">
        <h4>JIRA Issues ({jiraData.filtered_count})</h4>
        <div className="issues-list">
          {jiraData.issues.slice(0, 5).map((issue) => (
            <div key={issue.key} className="issue-item">
              <div className="issue-header">
                <a href={issue.url} target="_blank" rel="noopener noreferrer" className="issue-key">
                  {issue.key}
                </a>
                <span className={`issue-status status-${issue.status.toLowerCase().replace(' ', '-')}`}>
                  {issue.status}
                </span>
              </div>
              <p className="issue-summary">{issue.summary}</p>
              {issue.assignee && (
                <p className="issue-assignee">Assignee: {issue.assignee}</p>
              )}
            </div>
          ))}
          {jiraData.issues.length > 5 && (
            <p className="more-items">...and {jiraData.issues.length - 5} more issues</p>
          )}
        </div>
      </div>
    );
  };

  const renderGitHubDetails = (githubData) => {
    if (!githubData) {
      return <p>No GitHub data found.</p>;
    }

    return (
      <div className="github-details">
        {githubData.commits && githubData.commits.length > 0 && (
          <div className="commits-section">
            <h4>Recent Commits ({githubData.commits.length})</h4>
            <div className="commits-list">
              {githubData.commits.slice(0, 5).map((commit) => (
                <div key={commit.sha} className="commit-item">
                  <div className="commit-header">
                    <a href={commit.url} target="_blank" rel="noopener noreferrer" className="commit-sha">
                      {commit.sha.substring(0, 8)}
                    </a>
                    <span className="commit-repo">{commit.repository}</span>
                  </div>
                  <p className="commit-message">{commit.message.split('\n')[0]}</p>
                  <p className="commit-author">By {commit.author} on {new Date(commit.date).toLocaleDateString()}</p>
                </div>
              ))}
              {githubData.commits.length > 5 && (
                <p className="more-items">...and {githubData.commits.length - 5} more commits</p>
              )}
            </div>
          </div>
        )}

        {githubData.pull_requests && githubData.pull_requests.length > 0 && (
          <div className="prs-section">
            <h4>Pull Requests ({githubData.pull_requests.length})</h4>
            <div className="prs-list">
              {githubData.pull_requests.slice(0, 5).map((pr) => (
                <div key={pr.number} className="pr-item">
                  <div className="pr-header">
                    <a href={pr.url} target="_blank" rel="noopener noreferrer" className="pr-number">
                      #{pr.number}
                    </a>
                    <span className={`pr-state state-${pr.state}`}>
                      {pr.merged ? 'Merged' : pr.state}
                    </span>
                  </div>
                  <p className="pr-title">{pr.title}</p>
                  <p className="pr-meta">By {pr.author} in {pr.repository}</p>
                </div>
              ))}
              {githubData.pull_requests.length > 5 && (
                <p className="more-items">...and {githubData.pull_requests.length - 5} more pull requests</p>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`message ${message.type} ${message.isError ? 'error' : ''}`}>
      <div className="message-header">
        <span className="message-sender">
          {message.type === 'user' ? 'You' : 'Assistant'}
        </span>
        <span className="message-timestamp">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
      
      <div className="message-content">
        <div className="message-text">
          {message.content}
        </div>
        
        {message.data && (
          <div className="message-actions">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="toggle-details-button"
            >
              {showDetails ? 'Hide Details' : 'Show Details'}
            </button>
          </div>
        )}
      </div>

      {showDetails && message.data && (
        <div className="message-details">
          {message.data.jira && renderJiraDetails(message.data.jira)}
          {message.data.github && renderGitHubDetails(message.data.github)}
          
          {message.data.query_metadata && (
            <div className="query-metadata">
              <h4>Query Information</h4>
              <p><strong>Original Query:</strong> {message.data.query_metadata.original_query}</p>
              {message.data.query_metadata.team_members && (
                <p><strong>Team Members:</strong> {message.data.query_metadata.team_members.join(', ')}</p>
              )}
              {message.data.query_metadata.date_range && (
                <p><strong>Date Range:</strong> {message.data.query_metadata.date_range.start} to {message.data.query_metadata.date_range.end}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Message;
