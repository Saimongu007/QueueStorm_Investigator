import { useState, useEffect } from 'react'
import './HealthStatus.css'

function HealthStatus() {
  const [status, setStatus] = useState('checking')
  const [lastChecked, setLastChecked] = useState(null)

  const checkHealth = async () => {
    try {
      const response = await fetch('/api/health')
      if (response.ok) {
        const data = await response.json()
        setStatus(data.status === 'ok' ? 'healthy' : 'unhealthy')
      } else {
        setStatus('unhealthy')
      }
    } catch (err) {
      setStatus('unhealthy')
    }
    setLastChecked(new Date())
  }

  useEffect(() => {
    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy':
        return '✅'
      case 'unhealthy':
        return '❌'
      default:
        return '⏳'
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'healthy':
        return 'Backend Online'
      case 'unhealthy':
        return 'Backend Offline'
      default:
        return 'Checking...'
    }
  }

  return (
    <div className={`health-status status-${status}`}>
      <span className="status-icon">{getStatusIcon()}</span>
      <span className="status-text">{getStatusText()}</span>
      {lastChecked && (
        <span className="status-time">
          Last checked: {lastChecked.toLocaleTimeString()}
        </span>
      )}
    </div>
  )
}

export default HealthStatus
