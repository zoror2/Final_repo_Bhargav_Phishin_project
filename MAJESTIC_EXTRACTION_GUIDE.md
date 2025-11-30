# Majestic Million Feature Extraction Guide

## 🎯 Overview

This script extracts **26 phishing detection features** from the Majestic Million dataset using Docker Selenium. It's designed to be **crash-resistant** and can safely run overnight without losing progress.

## ✨ Key Features

### 🛡️ Crash Recovery
- ✅ **Automatic progress saving** every 100 URLs
- ✅ **Resume from last checkpoint** if stopped or crashed
- ✅ **No data loss** - all extracted features are saved immediately
- ✅ **Safe to stop anytime** - press Ctrl+C or close terminal

### 📊 26 Features Extracted

The script extracts these features for each URL:

1. `url` - The website URL
2. `label` - Classification (0 = legitimate, 1 = phishing)
3. `success` - Whether extraction succeeded
4. `num_events` - Number of interactive elements
5. `ssl_valid` - Has valid SSL certificate
6. `ssl_invalid` - Has invalid SSL certificate
7. `redirects` - Number of redirects
8. `forms` - Number of HTML forms
9. `password_fields` - Number of password input fields
10. `iframes` - Number of iframes
11. `scripts` - Number of script tags
12. `suspicious_keywords` - Count of suspicious words
13. `external_requests` - External domain requests
14. `page_load_time` - Time to load page (seconds)
15. `has_errors` - Whether errors occurred
16. `count_ssl_invalid` - SSL error count
17. `count_webdriver_error` - WebDriver error count
18. `count_ssl_valid` - Valid SSL count
19. `count_redirects` - Redirect count
20. `count_external_requests` - External request count
21. `count_forms_detected` - Forms detected count
22. `count_password_fields` - Password fields count
23. `count_iframes_detected` - Iframes detected count
24. `count_scripts_detected` - Scripts detected count
25. `count_suspicious_keywords` - Suspicious keywords count
26. `count_page_load_time` - Page load time count

## 🚀 Quick Start

### Step 1: Start Docker Selenium

```powershell
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest
```

**Verify it's running:**
```powershell
# Check Docker container
docker ps

# Test Selenium Hub
curl http://localhost:4444/status
```

### Step 2: Ensure Input File Exists

Make sure `majestic_million.csv` is in your project directory:
```
d:\Phishing LSTM Model\majestic_million.csv
```

### Step 3: Run the Extractor

```powershell
python majestic_million_extractor.py
```

The script will:
1. ✅ Check for previous progress
2. ✅ Resume from last checkpoint (if exists)
3. ✅ Connect to Docker Selenium
4. ✅ Start extracting features
5. ✅ Save progress every 100 URLs
6. ✅ Create `final_million_dataset.csv`

## 📊 Monitoring Progress

### Check Progress Once
```powershell
python check_million_progress.py
```

### Watch Progress Continuously (updates every 60 seconds)
```powershell
python check_million_progress.py --watch
```

### Watch Progress with Custom Interval (e.g., every 30 seconds)
```powershell
python check_million_progress.py --watch 30
```

## 📁 Output Files

| File | Description |
|------|-------------|
| `final_million_dataset.csv` | **Main output** - extracted features (CSV format) |
| `extraction_progress_million.json` | Progress tracker for resume capability |
| `extraction_million.log` | Detailed extraction log |
| `extraction_errors_million.log` | Error-only log for troubleshooting |

## ⏸️ Stopping and Resuming

### To Stop Extraction
- Press **Ctrl+C** in the terminal
- Or simply close the terminal window
- All progress is automatically saved!

### To Resume Extraction
Just run the script again:
```powershell
python majestic_million_extractor.py
```

The script will:
1. ✅ Detect previous progress
2. ✅ Load the last checkpoint
3. ✅ Continue from where it stopped
4. ✅ Append new results to existing CSV

**Example resume output:**
```
====================================================================
🔄 RESUMING FROM PREVIOUS RUN
====================================================================
📍 Last processed index: 45,678
✅ Previously successful: 43,210
❌ Previously failed: 2,468
🔒 SSL valid: 38,900
⚠️  SSL invalid: 4,310
⏰ Previous timestamp: 2025-11-11T08:30:45.123456
⌚ Previous elapsed time: 6.42 hours
====================================================================
```

## 🔧 Configuration

You can customize the extraction by editing `majestic_million_extractor.py`:

```python
extractor = MajesticMillionExtractor(
    input_file="majestic_million.csv",        # Input dataset
    output_file="final_million_dataset.csv",   # Output dataset
    checkpoint_interval=100,                   # Save every N URLs (default: 100)
    timeout=15,                                # Timeout per URL in seconds (default: 15)
)
```

### Recommended Settings

| URLs to Process | Checkpoint Interval | Timeout |
|----------------|---------------------|---------|
| < 10,000 | 50 | 20 |
| 10,000 - 100,000 | 100 | 15 |
| 100,000+ | 250 | 10 |

## ⏱️ Performance Estimates

**Processing Rate:** ~2-5 URLs per second (depends on network and Docker performance)

| Total URLs | Estimated Time | Recommended |
|-----------|---------------|-------------|
| 10,000 | 0.5 - 1.5 hours | Single session |
| 100,000 | 5.5 - 14 hours | Overnight run |
| 1,000,000 | 55 - 140 hours | 2-6 days |

## 🐛 Troubleshooting

### Docker Selenium Not Running
**Error:** `Failed to connect to Docker Selenium`

**Solution:**
```powershell
# Start Docker Selenium
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest

# Verify it's running
docker ps
```

### Out of Memory
**Error:** Container crashes or system slows down

**Solution:**
```powershell
# Increase shared memory
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=4g selenium/standalone-chrome:latest
```

### WebDriver Keeps Crashing
**Error:** Many WebDriver errors in log

**Solution:**
1. Increase timeout: Change `timeout=15` to `timeout=30`
2. Restart Docker Selenium:
```powershell
docker stop $(docker ps -q --filter ancestor=selenium/standalone-chrome:latest)
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest
```

### Slow Extraction
**Issue:** Processing < 1 URL per second

**Solutions:**
1. Reduce timeout: `timeout=10`
2. Increase checkpoint interval: `checkpoint_interval=250`
3. Check network connection
4. Restart Docker Selenium

### Progress File Corrupted
**Error:** Cannot load progress file

**Solution:**
```powershell
# Backup corrupted file
mv extraction_progress_million.json extraction_progress_million.json.backup

# Script will start fresh but won't re-extract existing rows in CSV
python majestic_million_extractor.py
```

## 📈 Monitoring While Running

### View Docker Selenium GUI (VNC)
1. Open browser: http://localhost:7900
2. Password: `secret`
3. Watch browser automation in real-time!

### View Logs in Real-Time
```powershell
# Windows PowerShell
Get-Content extraction_million.log -Wait -Tail 20

# Alternative
tail -f extraction_million.log  # If you have Git Bash or WSL
```

### Check Output File Progress
```powershell
# Count rows in output CSV
(Get-Content final_million_dataset.csv).Length - 1  # -1 for header

# View file size
ls final_million_dataset.csv
```

## 🎯 After Extraction Completes

### Verify Output
```powershell
python check_million_progress.py
```

### Upload to Kaggle
1. **File ready:** `final_million_dataset.csv`
2. **Format:** CSV with 26 features
3. **Size:** ~500MB - 1GB (depends on total URLs)
4. **Kaggle notebook:** Upload and train LSTM model

### Combine with Phishing Dataset
For balanced training, combine with phishing URLs (label=1):

```python
import pandas as pd

# Load legitimate sites (Majestic Million)
df_legit = pd.read_csv('final_million_dataset.csv')

# Load phishing sites (your phishing dataset)
df_phish = pd.read_csv('your_phishing_dataset.csv')

# Combine
df_combined = pd.concat([df_legit, df_phish], ignore_index=True)

# Shuffle
df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)

# Save
df_combined.to_csv('combined_training_dataset.csv', index=False)
```

## 💾 Data Safety Guarantees

✅ **Atomic writes** - Files never corrupted during save  
✅ **Checkpoint system** - Progress saved every 100 URLs  
✅ **Resume capability** - Continue from any point  
✅ **Error isolation** - Single URL failures don't stop extraction  
✅ **Backup logs** - Full audit trail of all operations  
✅ **Graceful shutdown** - Ctrl+C saves progress before exit  

## 📞 Support

If you encounter issues:

1. Check logs: `extraction_errors_million.log`
2. Run progress checker: `python check_million_progress.py`
3. Verify Docker: `docker ps`
4. Restart Docker Selenium if needed

---

**Ready to extract features!** 🚀

Run: `python majestic_million_extractor.py`
