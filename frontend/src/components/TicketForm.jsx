import { useState } from 'react'
import './TicketForm.css'

function TicketForm({ onSubmit, loading }) {
  const [ticketId, setTicketId] = useState('')
  const [complaint, setComplaint] = useState('')
  const [language, setLanguage] = useState('en')
  const [channel, setChannel] = useState('in_app_chat')
  const [userType, setUserType] = useState('customer')
  const [campaignContext, setCampaignContext] = useState('')
  const [transactions, setTransactions] = useState([])
  const [showTransactionForm, setShowTransactionForm] = useState(false)

  const [newTransaction, setNewTransaction] = useState({
    transaction_id: '',
    timestamp: '',
    type: 'transfer',
    amount: '',
    counterparty: '',
    status: 'completed'
  })

  const handleAddTransaction = () => {
    if (newTransaction.transaction_id && newTransaction.amount) {
      setTransactions([...transactions, {
        ...newTransaction,
        amount: parseFloat(newTransaction.amount)
      }])
      setNewTransaction({
        transaction_id: '',
        timestamp: '',
        type: 'transfer',
        amount: '',
        counterparty: '',
        status: 'completed'
      })
      setShowTransactionForm(false)
    }
  }

  const handleRemoveTransaction = (index) => {
    setTransactions(transactions.filter((_, i) => i !== index))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    const ticketData = {
      ticket_id: ticketId,
      complaint: complaint,
      language: language || undefined,
      channel: channel || undefined,
      user_type: userType || undefined,
      campaign_context: campaignContext || undefined,
      transaction_history: transactions.length > 0 ? transactions : undefined
    }

    onSubmit(ticketData)
  }

  const loadSampleData = () => {
    setTicketId('TKT-SAMPLE-001')
    setComplaint('I sent 5000 taka to a wrong number around 2pm today.')
    setLanguage('en')
    setChannel('in_app_chat')
    setUserType('customer')
    setCampaignContext('')
    setTransactions([
      {
        transaction_id: 'TXN-9101',
        timestamp: '2026-04-14T14:08:22Z',
        type: 'transfer',
        amount: 5000,
        counterparty: '+8801719876543',
        status: 'completed'
      }
    ])
  }

  return (
    <div className="ticket-form-container">
      <div className="form-header">
        <h2>Submit Support Ticket</h2>
        <button 
          type="button" 
          className="sample-btn"
          onClick={loadSampleData}
        >
          Load Sample Data
        </button>
      </div>

      <form onSubmit={handleSubmit} className="ticket-form">
        <div className="form-section">
          <h3>Basic Information</h3>
          
          <div className="form-group">
            <label htmlFor="ticketId">Ticket ID *</label>
            <input
              id="ticketId"
              type="text"
              value={ticketId}
              onChange={(e) => setTicketId(e.target.value)}
              placeholder="e.g., TKT-001"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="complaint">Complaint *</label>
            <textarea
              id="complaint"
              value={complaint}
              onChange={(e) => setComplaint(e.target.value)}
              placeholder="Describe the issue..."
              rows="5"
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="language">Language</label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              >
                <option value="en">English</option>
                <option value="bn">Bangla</option>
                <option value="mixed">Mixed</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="channel">Channel</label>
              <select
                id="channel"
                value={channel}
                onChange={(e) => setChannel(e.target.value)}
              >
                <option value="in_app_chat">In-App Chat</option>
                <option value="call_center">Call Center</option>
                <option value="email">Email</option>
                <option value="merchant_portal">Merchant Portal</option>
                <option value="field_agent">Field Agent</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="userType">User Type</label>
              <select
                id="userType"
                value={userType}
                onChange={(e) => setUserType(e.target.value)}
              >
                <option value="customer">Customer</option>
                <option value="merchant">Merchant</option>
                <option value="agent">Agent</option>
                <option value="unknown">Unknown</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="campaignContext">Campaign Context (Optional)</label>
            <input
              id="campaignContext"
              type="text"
              value={campaignContext}
              onChange={(e) => setCampaignContext(e.target.value)}
              placeholder="e.g., Eid cashback campaign"
            />
          </div>
        </div>

        <div className="form-section">
          <div className="section-header">
            <h3>Transaction History</h3>
            <button
              type="button"
              className="add-transaction-btn"
              onClick={() => setShowTransactionForm(!showTransactionForm)}
            >
              {showTransactionForm ? 'Cancel' : '+ Add Transaction'}
            </button>
          </div>

          {showTransactionForm && (
            <div className="transaction-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Transaction ID *</label>
                  <input
                    type="text"
                    value={newTransaction.transaction_id}
                    onChange={(e) => setNewTransaction({
                      ...newTransaction,
                      transaction_id: e.target.value
                    })}
                    placeholder="TXN-9101"
                  />
                </div>

                <div className="form-group">
                  <label>Timestamp</label>
                  <input
                    type="datetime-local"
                    value={newTransaction.timestamp}
                    onChange={(e) => setNewTransaction({
                      ...newTransaction,
                      timestamp: e.target.value ? new Date(e.target.value).toISOString() : ''
                    })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Type</label>
                  <select
                    value={newTransaction.type}
                    onChange={(e) => setNewTransaction({
                      ...newTransaction,
                      type: e.target.value
                    })}
                  >
                    <option value="transfer">Transfer</option>
                    <option value="payment">Payment</option>
                    <option value="cash_in">Cash In</option>
                    <option value="cash_out">Cash Out</option>
                    <option value="settlement">Settlement</option>
                    <option value="refund">Refund</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Amount *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newTransaction.amount}
                    onChange={(e) => setNewTransaction({
                      ...newTransaction,
                      amount: e.target.value
                    })}
                    placeholder="5000"
                  />
                </div>

                <div className="form-group">
                  <label>Status</label>
                  <select
                    value={newTransaction.status}
                    onChange={(e) => setNewTransaction({
                      ...newTransaction,
                      status: e.target.value
                    })}
                  >
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                    <option value="pending">Pending</option>
                    <option value="reversed">Reversed</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Counterparty</label>
                <input
                  type="text"
                  value={newTransaction.counterparty}
                  onChange={(e) => setNewTransaction({
                    ...newTransaction,
                    counterparty: e.target.value
                  })}
                  placeholder="+8801719876543 or MERCHANT-123"
                />
              </div>

              <button
                type="button"
                className="save-transaction-btn"
                onClick={handleAddTransaction}
              >
                Save Transaction
              </button>
            </div>
          )}

          {transactions.length > 0 && (
            <div className="transactions-list">
              {transactions.map((txn, index) => (
                <div key={index} className="transaction-item">
                  <div className="transaction-info">
                    <div className="transaction-main">
                      <span className="transaction-id">{txn.transaction_id}</span>
                      <span className={`transaction-status status-${txn.status}`}>
                        {txn.status}
                      </span>
                    </div>
                    <div className="transaction-details">
                      <span>{txn.type}</span>
                      <span className="amount">৳{txn.amount.toFixed(2)}</span>
                      {txn.counterparty && <span>{txn.counterparty}</span>}
                    </div>
                  </div>
                  <button
                    type="button"
                    className="remove-btn"
                    onClick={() => handleRemoveTransaction(index)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <button 
          type="submit" 
          className="submit-btn"
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Analyze Ticket'}
        </button>
      </form>
    </div>
  )
}

export default TicketForm
