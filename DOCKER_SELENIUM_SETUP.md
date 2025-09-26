# Docker Selenium Feature Extraction Setup

This document explains how to use Docker Selenium to extract features from URLs for phishing detection.

## Prerequisites

1. Docker Desktop installed and running
2. Python 3.7+ with required packages

## Docker Setup

First, we'll run a Selenium Grid with Chrome browser using Docker:

```bash
# Pull the Selenium standalone Chrome image
docker pull selenium/standalone-chrome:latest

# Run Selenium Chrome container
docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" --name selenium-chrome selenium/standalone-chrome:latest
```

- Port 4444: WebDriver API
- Port 7900: VNC viewer (password: secret)
- --shm-size="2g": Prevents browser crashes due to insufficient shared memory

## Feature Extraction Script

The script will extract various features from each URL in our small dataset:

### URL-based Features:
- URL length
- Number of dots, slashes, hyphens
- Presence of IP address
- Domain length
- Suspicious keywords

### Content-based Features (via Selenium):
- Page title
- Number of forms
- Number of links
- Presence of HTTPS
- Response time
- Page load success/failure

## Usage

1. Start Docker Selenium container
2. Run the feature extraction script
3. View results in extracted_features.csv
4. Monitor extraction progress via VNC (localhost:7900)

## Files Created:
- `small_dataset.csv`: Input URLs (10 legit + 10 phishing)
- `docker_selenium_extractor.py`: Main extraction script
- `extracted_features.csv`: Output with features
- `extraction_report.json`: Summary report