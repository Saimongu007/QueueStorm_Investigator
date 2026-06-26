import './ResultDisplay.css'

function ResultDisplay({ result }) {
  const getSeverityColor = (severity) => {
    const colors = {
      low: '#10b981',
      medium: '#f59e0b',
      high: '#ef4444',
      critical: '#dc2626'
    }
    return colors[severity] || '#6b7280'
  }

  const getEvidenceIcon = (verdict) => {
    const icons = {
      consistent: '✅',
      inconsistent: '❌',
      insufficient_data: '⚠️'
    }
    return icons[verdict] || '❓'
  }

  const formatCaseType = (type) => {
    return type.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  const formatDepartment = (dept) => {
    return dept.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ')
  }

  return (
    <div className="result-container">
      <div className="result-header">
        <h2>Analysis Result</h2>
        <div className="ticket-id-badge">
          {result.ticket_id}
        </div>
      </div>

      <div className="result-grid">
        {/* Key Metrics */}
        <div className="result-card metrics-card">
          <h3>Key Metrics</h3>
          <div className="metrics-grid">
            <div className="metric">
              <span className="metric-label">Case Type</span>
              <span className="metric-value case-type">
                {formatCaseType(result.case_type)}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Severity</span>
              <span 
                className="metric-value severity-badge"
                style={{ backgroundColor: getSeverityColor(result.severity) }}
              >
                {result.severity.toUpperCase()}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Department</span>
              <span className="metric-value">
                {formatDepartment(result.department)}
              </span>
            </div>
            <div className="metric">
              <span className="metric-label">Evidence Verdict</span>
              <span className="metric-value">
                {getEvidenceIcon(result.evidence_verdict)} {' '}
                {result.evidence_verdict.replace('_', ' ')}
              </span>
            </div>
          </div>
        </div>

        {/* Confidence & Review */}
        <div className="result-card confidence-card">
          <h3>Assessment</h3>
          <div className="confidence-section">
            <div className="confidence-bar-container">
              <div className="confidence-label">
                <span>Confidence Score</span>
                <span className="confidence-value">
                  {(result.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="confidence-bar">
                <div 
                  className="confidence-fill"
                  style={{ width: `${result.confidence * 100}%` }}
                />
              </div>
            </div>
            <div className="review-status">
              <span className={`review-badge ${result.human_review_required ? 'required' : 'not-required'}`}>
                {result.human_review_required ? '👤 Human Review Required' : '✓ Auto-Processing'}
              </span>
            </div>
          </div>
        </div>

        {/* Transaction Details */}
        {result.relevant_transaction_id && (
          <div className="result-card transaction-card">
            <h3>Relevant Transaction</h3>
            <div className="transaction-id">
              {result.relevant_transaction_id}
            </div>
          </div>
        )}

        {/* Agent Summary */}
        <div className="result-card summary-card">
          <h3>Agent Summary</h3>
          <p className="summary-text">{result.agent_summary}</p>
        </div>

        {/* Recommended Action */}
        <div className="result-card action-card">
          <h3>Recommended Next Action</h3>
          <p className="action-text">{result.recommended_next_action}</p>
        </div>

        {/* Customer Reply */}
        <div className="result-card customer-reply-card">
          <h3>Customer Reply (Draft)</h3>
          <div className="customer-reply-box">
            <p>{result.customer_reply}</p>
          </div>
          <button 
            className="copy-btn"
            onClick={() => {
              navigator.clipboard.writeText(result.customer_reply)
              alert('Customer reply copied to clipboard!')
            }}
          >
            📋 Copy Reply
          </button>
        </div>

        {/* Reason Codes */}
        {result.reason_codes && result.reason_codes.length > 0 && (
          <div className="result-card reason-codes-card">
            <h3>Reason Codes</h3>
            <div className="reason-codes-list">
              {result.reason_codes.map((code, index) => (
                <span key={index} className="reason-code">
                  {code.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Raw JSON View (for debugging) */}
      <details className="raw-json">
        <summary>View Raw JSON Response</summary>
        <pre>{JSON.stringify(result, null, 2)}</pre>
      </details>
    </div>
  )
}

export default ResultDisplay
