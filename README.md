# Energy Meter Monitoring System

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)

A real-time energy meter monitoring system that uses computer vision to capture and process meter readings, calculate bills, and provide a comprehensive dashboard for energy consumption analysis. This system is designed to help users track electricity usage, set cost limits, and receive alerts.

## 📋 Table of Contents
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Contributing](#-contributing)


## ✨ Features

### 1. Camera Feed and Reading Capture
- Real-time camera feed display
- Automatic meter reading capture every 35 seconds
- Support for both single-phase and three-phase meters
- Image enhancement for better reading accuracy
- Initial 5-second delay for setup
- Debug information display

### 2. Dashboard
- Real-time energy consumption monitoring
- Daily cost limit tracking with visual indicators
- Consumption trend analysis
- Peak usage hour visualization
- Average daily usage statistics
- Current bill calculation
- Alert system for cost limit warnings

### 3. Cost Management
- Set daily cost limits
- Visual progress circle showing limit usage
- Color-coded warnings:
  - Blue: Normal usage (<75%)
  - Orange: Moderate usage (75-90%)
  - Red: High usage (>90%)
  - Red filled: Limit exceeded
- Automatic alerts for approaching or exceeding limits

### 4. Data Visualization
- Line chart for consumption trends
- Bar chart for peak usage hours
- Real-time updates every 30 seconds
- Historical data view

## 🚀 Prerequisites

- Python 3.8 or higher
- Google Chrome (for Selenium web scraping)
- Webcam (for meter reading capture)
- Google Gemini API key (for text extraction)

## 💻 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/energy-meter-monitor.git
cd energy-meter-monitor
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

1. Create a `.env` file in the project root and add your Gemini API key:
```env
GEMINI_API_KEY=your_api_key_here
```

2. Initialize the database:
```bash
python -c "from database import init_db; init_db()"
```

3. Download the appropriate ChromeDriver version for your Chrome browser from [here](https://chromedriver.chromium.org/downloads) and place it in the project root.

## 🚀 Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

## 🔐 Demo Credentials

For testing and demonstration purposes, use the following credentials:

- **Username**: `admin`
- **Password**: `1234`

> **Note**: These credentials are for demonstration only. In a production environment, please implement proper user authentication with secure password storage.

4. Navigate to the Dashboard to view real-time meter readings and consumption analytics.

## 📁 Project Structure

```
energy-meter-monitor/
├── app.py                # Main Flask application
├── billing.py            # Billing calculations and tariff logic
├── bill_calc.py          # Selenium-based bill calculation
├── database.py           # Database models and operations
├── extract_text.py       # Text extraction using Gemini Vision API
├── test_billing.py       # Unit tests for billing logic
├── test_image.py         # Tests for image processing
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this file)
├── chromedriver.exe      # ChromeDriver for Selenium
├── readings.db           # SQLite database (created on first run)
├── input/                # Stores captured meter images
└── templates/            # HTML templates
    ├── Login.html        # Login page
    ├── dashboard.html    # Main dashboard
    ├── profile.html      # User profile
    └── alerts.html       # System alerts
```

## 📚 API Documentation

### Authentication
- `POST /login` - User authentication
- `GET /logout` - Logout current user

### Meter Reading
- `GET /video_feed` - Stream live camera feed
- `GET /get_reading` - Get current meter reading
- `GET /get_readings` - Get all historical readings

### Alerts
- `GET /get_alerts` - Get all alerts
- `POST /mark_alert_read/<id>` - Mark alert as read
- `POST /clear_alerts` - Clear all alerts

### Settings
- `POST /update_phase` - Update meter phase (single/three)
- `POST /set_cost_limit` - Set daily cost limit
- `POST /clear_cost_limit` - Clear cost limit

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- Uses [Google's Gemini Vision API](https://ai.google.dev/) for text extraction
- Charts powered by [Chart.js](https://www.chartjs.org/)
│   ├── index.html     # Camera feed page
│   ├── dashboard.html # Dashboard page
│   ├── alerts.html   # Alerts page
│   └── profile.html  # User profile page
├── static/            # Static assets
└── input/            # Captured images storage
```

## API Endpoints

### Camera Feed
- `/video_feed` - Stream camera feed
- `/get_reading` - Get latest reading info
- `/get_status` - Get capture timer status
- `/start_process` - Start reading capture
- `/stop_process` - Stop reading capture
- `/update_phase` - Update meter phase type

### Dashboard
- `/get_dashboard_data` - Get all dashboard statistics
- `/set_cost_limit` - Set daily cost limit
- `/clear_cost_limit` - Clear cost limit
- `/get_readings` - Get reading history
- `/clear_readings` - Clear all readings

### Authentication
- `/login` - User login
- `/logout` - User logout

## Technologies Used

- Python Flask for backend
- OpenCV for image capture and processing
- SQLite for data storage
- Chart.js for data visualization
- HTML/CSS/JavaScript for frontend
- Gemini API for text extraction

## License

This project is licensed under the MIT License - see the LICENSE file for details.
