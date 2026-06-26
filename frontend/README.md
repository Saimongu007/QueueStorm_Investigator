# QueueStorm Investigator - Frontend

React-based frontend interface for the QueueStorm Investigator API.

## Features

- **Real-time Health Monitoring** - Displays backend API health status
- **Interactive Ticket Submission** - Form with validation for all ticket fields
- **Transaction Management** - Add, view, and remove transaction history
- **Comprehensive Results Display** - Visual presentation of analysis results
- **Sample Data Loading** - Quick test with pre-filled sample data
- **Responsive Design** - Works on desktop, tablet, and mobile devices

## Prerequisites

- Node.js 18+ (npm or yarn)
- Backend API running on `http://localhost:8000`

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── HealthStatus.jsx       # Backend health monitor
│   │   ├── HealthStatus.css
│   │   ├── TicketForm.jsx         # Ticket submission form
│   │   ├── TicketForm.css
│   │   ├── ResultDisplay.jsx      # Analysis results display
│   │   └── ResultDisplay.css
│   ├── App.jsx                    # Main application component
│   ├── App.css
│   ├── main.jsx                   # Application entry point
│   └── index.css                  # Global styles
├── index.html
├── vite.config.js                 # Vite configuration with proxy
└── package.json
```

## API Integration

The frontend connects to the backend API through a Vite proxy configured in `vite.config.js`:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

### API Endpoints Used

1. **GET /health** - Health check endpoint
   - Polled every 30 seconds
   - Displays real-time status badge

2. **POST /analyze-ticket** - Ticket analysis endpoint
   - Submits ticket data
   - Receives structured analysis response

## Components

### HealthStatus
Monitors backend availability and displays status indicator.

### TicketForm
Comprehensive form for submitting support tickets with:
- Basic information (ticket ID, complaint, language, channel, user type)
- Campaign context
- Transaction history management
- Sample data loader

### ResultDisplay
Shows analysis results with:
- Key metrics (case type, severity, department, evidence verdict)
- Confidence score visualization
- Relevant transaction details
- Agent summary
- Recommended next actions
- Customer reply draft (with copy button)
- Reason codes
- Raw JSON view for debugging

## Styling

The frontend uses:
- CSS modules for component-specific styles
- Gradient backgrounds and modern UI patterns
- Responsive grid layouts
- Smooth animations and transitions

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

The production build will be generated in the `dist/` directory.

## Development Tips

1. **Backend Connection**: Ensure the backend is running on port 8000 before starting the frontend
2. **Sample Data**: Use the "Load Sample Data" button to quickly test the interface
3. **Health Status**: The health indicator auto-refreshes every 30 seconds
4. **Form Validation**: All required fields are validated before submission

## Environment Variables

Create a `.env` file if you need to customize the backend API URL:

```env
VITE_API_URL=http://localhost:8000
```

Then update `vite.config.js` proxy target accordingly.

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

When adding new features:
1. Follow the existing component structure
2. Use CSS modules for styling
3. Maintain responsive design
4. Update this README with new features
