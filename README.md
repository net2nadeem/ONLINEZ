# 🔥 DamaDam Profile Scraper

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

A high-performance web scraper for DamaDam.pk profiles with Google Sheets integration and optimized browser management.

## ✨ Features

- 🚀 **Lightning Fast**: 70% faster startup with optimized Chrome configuration
- 📊 **Google Sheets Integration**: Direct export with duplicate handling
- 🔄 **Continuous Mode**: Browser reuse for maximum efficiency  
- 🎯 **Smart Data Extraction**: Comprehensive profile information
- 📝 **CSV Export**: Local backup with UTF-8 encoding
- 🔐 **Session Management**: Smart cookie handling and authentication
- 📈 **Progress Tracking**: Real-time statistics and logging
- ⚡ **Error Recovery**: Robust error handling and retry mechanisms

## 📋 Requirements

- Python 3.8 or higher
- Chrome/Chromium browser
- Google Cloud Service Account (for Sheets integration)
- Active DamaDam.pk account

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/damadam-profile-scraper.git
cd damadam-profile-scraper
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Setup Google Sheets (Optional)
1. Create a Google Cloud Service Account
2. Download the JSON credentials
3. Rename to `service_account.json`
4. Share your Google Sheet with the service account email

### 5. Run the Scraper
```bash
python scraper.py
```

## 📁 Project Structure

```
damadam-profile-scraper/
├── scraper.py              # Main scraper script
├── config.py               # Configuration settings
├── utils/
│   ├── __init__.py
│   ├── browser.py          # Browser management
│   ├── auth.py            # Authentication handlers
│   ├── sheets.py          # Google Sheets integration
│   └── data_processor.py  # Data cleaning utilities
├── data/                   # Output directory
│   ├── profiles.csv
│   └── logs/
├── credentials/            # Credentials (gitignored)
│   ├── service_account.json
│   └── cookies.json
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
├── README.md              # This file
└── CONTRIBUTING.md        # Contribution guidelines
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# DamaDam Credentials
DD_USERNAME=your_username
DD_PASSWORD=your_password

# Google Sheets
GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit
ENABLE_SHEETS_EXPORT=true

# Scraping Settings
LOOP_WAIT_MINUTES=15
MIN_DELAY=0.5
MAX_DELAY=1.5
HEADLESS_MODE=true

# Output Settings
CSV_OUTPUT=data/profiles.csv
LOG_LEVEL=INFO
```

### Advanced Configuration (config.py)
```python
# Browser settings
BROWSER_CONFIG = {
    'headless': True,
    'disable_images': True,
    'page_load_timeout': 10,
    'implicit_wait': 5
}

# Data extraction settings
EXTRACTION_CONFIG = {
    'max_retries': 3,
    'retry_delay': 2,
    'batch_size': 5
}
```

## 🔧 Usage Examples

### Basic Usage
```python
from scraper import DamaDamScraper

# Initialize scraper
scraper = DamaDamScraper()

# Run once
profiles = scraper.run_once()
print(f"Scraped {len(profiles)} profiles")

# Continuous mode
scraper.run_continuous(wait_minutes=15)
```

### Custom Configuration
```python
# Custom browser settings
scraper = DamaDamScraper(
    headless=False,
    wait_time=10,
    export_to_sheets=False
)

# Run with custom parameters
profiles = scraper.scrape_users(['user1', 'user2', 'user3'])
```

## 📊 Output Format

### CSV Output
```csv
DATE,TIME,NICKNAME,TAGS,CITY,GENDER,MARRIED,AGE,JOINED,FOLLOWERS,POSTS,PLINK,PIMAGE,INTRO
25-Sep-2025,09:30 AM,username123,,Karachi,Male,Yes,25,2020,150,45,https://...,https://...,Profile intro text
```

### Google Sheets Integration
- Automatic duplicate detection
- Seen count tracking
- Real-time updates
- Batch processing for efficiency

## 🐛 Troubleshooting

### Common Issues

**Browser fails to start**
```bash
# Install Chrome dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver

# Or use system Chrome
sudo apt-get install google-chrome-stable
```

**Google Sheets authentication fails**
1. Verify service account JSON is valid
2. Check if sheet is shared with service account email
3. Ensure Google Sheets API is enabled

**Login fails**
1. Verify credentials in `.env` file
2. Check if account is not locked
3. Try manual login first

**Memory issues**
```python
# Reduce batch size in config.py
EXTRACTION_CONFIG = {
    'batch_size': 3  # Reduced from 5
}
```

## 🔒 Security Best Practices

1. **Never commit credentials** - Use `.env` files
2. **Rotate passwords regularly** - Update credentials monthly
3. **Use service accounts** - Don't use personal Google accounts
4. **Monitor usage** - Check for suspicious activity
5. **Rate limiting** - Don't overwhelm the target site

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Changelog

### v2.0.0 (2025-09-25)
- ⚡ 70% faster browser startup
- 🔄 Browser reuse in continuous mode
- 📊 Enhanced Google Sheets integration
- 🐛 Fixed Chrome DevTools errors
- 📈 Improved progress tracking

### v1.0.0 (Initial Release)
- 🎯 Basic profile scraping
- 📊 CSV export
- 🔐 Cookie-based authentication

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Please respect the target website's terms of service and robots.txt file. The authors are not responsible for any misuse of this software.

## 📞 Support

- 🐛 **Bug Reports**: [Create an issue](https://github.com/yourusername/damadam-profile-scraper/issues)
- 💡 **Feature Requests**: [Start a discussion](https://github.com/yourusername/damadam-profile-scraper/discussions)
- 📧 **Contact**: your.email@example.com

## 🙏 Acknowledgments

- [Selenium WebDriver](https://selenium-python.readthedocs.io/) for browser automation
- [Google Sheets API](https://developers.google.com/sheets/api) for data integration
- [ChromeDriver](https://chromedriver.chromium.org/) for Chrome automation

---

<p align="center">Made with ❤️ by <a href="https://github.com/yourusername">Your Name</a></p>
