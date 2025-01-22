# Sales Automation System

A comprehensive sales automation system for managing prospects, tracking email interactions, and monitoring sales pipeline progress.

## Features

- Real-time dashboard with key metrics
- Prospect stage tracking and management
- Email interaction monitoring
- Response rate analytics
- Demo scheduling tracking
- Stage distribution visualization
- Recent activity feed

## System Requirements

- Python 3.8+
- SQLite3
- Modern web browser (Chrome, Firefox, Safari)

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd SalesAutomation
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Set up environment variables in `.env`:
```
JWT_SECRET=your-secret-key
EMAIL_SERVER=your-email-server
EMAIL_USER=your-email-user
EMAIL_PASSWORD=your-email-password
```

## Usage

1. Start the dashboard server:
```bash
python dashboard_server.py
```

2. Start the email monitor (in a separate terminal):
```bash
python quick_monitor.py
```

3. Access the dashboard at http://localhost:5000

## Components

- `dashboard_server.py`: Main web server serving the dashboard
- `quick_api.py`: RESTful API for data access
- `quick_monitor.py`: Email monitoring service
- `quick_status.py`: CLI tool for quick status checks
- `templates/`: HTML templates
- `static/`: JavaScript and CSS files
- `sales_automation.db`: SQLite database

## Process Flow

1. Email Monitor:
   - Continuously checks for new emails
   - Updates prospect status
   - Records interactions

2. Dashboard:
   - Displays real-time metrics
   - Shows prospect pipeline
   - Visualizes stage distribution
   - Lists recent activities

3. API:
   - Handles data requests
   - Manages prospect updates
   - Processes webhooks

## Security

- JWT authentication for API access
- Environment variables for sensitive data
- Secure email handling
- Input validation and sanitization

## Maintenance

1. Database:
   - Regular backups
   - Periodic cleanup of old records
   - Index optimization

2. Monitoring:
   - Email service status
   - API response times
   - Error logging

## Support

For issues or questions:
1. Check the logs in `logs/`
2. Review the ARCHITECTURE.md
3. Contact the development team

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

[License Type] - See LICENSE file for details
