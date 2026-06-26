import { useState } from 'react'
import './App.css'
import TicketForm from './components/TicketForm'
import ResultDisplay from './components/ResultDisplay'
import HealthStatus from './components/HealthStatus'

function App() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async (ticketData) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/analyze-ticket', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(ticketData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to analyze ticket')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎫 QueueStorm Investigator</h1>
        <p>AI-powered support ticket investigator for digital finance</p>
        <HealthStatus />
      </header>
      
      <main className="app-main">
        <div className="container">
          <TicketForm onSubmit={handleAnalyze} loading={loading} />
          
          {error && (
            <div className="error-container">
              <div className="error-message">
                <span className="error-icon">❌</span>
                <span>{error}</span>
              </div>
            </div>
          )}
          
          {result && <ResultDisplay result={result} />}
        </div>
      </main>
    </div>
  )
}

export default App
