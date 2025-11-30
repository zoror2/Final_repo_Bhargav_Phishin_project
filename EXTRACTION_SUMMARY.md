# 🚀 Majestic Million Feature Extraction - Complete Setup

## 📝 What I Created For You

I've created a **production-grade, crash-resistant feature extraction system** that will safely extract 26 phishing detection features from your `majestic_million.csv` dataset. Here's what you have:

### ✨ Files Created

| File | Purpose |
|------|---------|
| `majestic_million_extractor.py` | **Main extraction script** - Extracts all 26 features with crash recovery |
| `check_million_progress.py` | **Progress monitor** - Check extraction progress anytime |
| `verify_final_dataset.py` | **Dataset verifier** - Analyze final output quality |
| `RUN_MAJESTIC_EXTRACTION.bat` | **Easy launcher** - Double-click to start extraction |
| `MAJESTIC_EXTRACTION_GUIDE.md` | **Complete guide** - Detailed documentation |

---

## 🎯 Key Features

### 🛡️ Crash Recovery System

**THE MOST IMPORTANT FEATURE YOU REQUESTED:**

✅ **Auto-save every 100 URLs** - Progress saved continuously  
✅ **Resume from any point** - If stopped, run again to continue  
✅ **No data loss** - All extracted features preserved  
✅ **Atomic writes** - Files never corrupted  
✅ **Safe to stop anytime** - Press Ctrl+C safely  

**How it works:**

```
1. Every 100 URLs processed → Automatically saved to CSV
2. Progress tracker updated → JSON file with checkpoint
3. If stopped/crashed → Run script again
4. Script detects progress → Resumes from last checkpoint
5. Appends new results → No re-processing of completed URLs
```

### 📊 26 Features Extracted

Exactly as you specified:

```
url, label, success, num_events, ssl_valid, ssl_invalid, redirects, 
forms, password_fields, iframes, scripts, suspicious_keywords, 
external_requests, page_load_time, has_errors, count_ssl_invalid, 
count_webdriver_error, count_ssl_valid, count_redirects, 
count_external_requests, count_forms_detected, count_password_fields, 
count_iframes_detected, count_scripts_detected, count_suspicious_keywords, 
count_page_load_time
```

### 💾 Output Format

**CSV file:** `final_million_dataset.csv`

```csv
url,label,success,num_events,ssl_valid,ssl_invalid,redirects,forms,...
https://example.com,0,1,45,1,0,0,3,1,2,15,2,5,1.23,0,0,0,1,0,5,3,1,2,15,2,1
https://site.org,0,1,23,1,0,1,2,0,1,8,0,3,0.89,0,0,0,1,1,3,2,0,1,8,0,1
...
```

**Perfect for Kaggle LSTM training!**

---

## 🚀 How to Use

### Step 1: Start Docker Selenium

```powershell
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest
```

Verify it's running:
```powershell
docker ps
```

### Step 2: Start Extraction

**Option A - Easy Way (Double-click):**
```
Double-click: RUN_MAJESTIC_EXTRACTION.bat
```

**Option B - Command Line:**
```powershell
python majestic_million_extractor.py
```

### Step 3: Monitor Progress

**In another terminal:**
```powershell
# Check once
python check_million_progress.py

# Watch continuously (updates every 60 seconds)
python check_million_progress.py --watch

# Watch with custom interval (e.g., every 30 seconds)
python check_million_progress.py --watch 30
```

### Step 4: Let It Run Overnight

- ✅ Script will run safely overnight
- ✅ Progress saved every 100 URLs
- ✅ If anything crashes, just run again
- ✅ Will resume automatically

---

## ⏸️ Stopping & Resuming

### To Stop Extraction (SAFE)

**Method 1:** Press `Ctrl+C` in terminal
- Script will save current progress
- Exit gracefully

**Method 2:** Close terminal window
- Last checkpoint (every 100 URLs) is saved
- Safe to do this anytime

**Method 3:** Computer crashes/restarts
- Progress saved up to last checkpoint
- No worries!

### To Resume Extraction

Just run the same command again:
```powershell
python majestic_million_extractor.py
```

**What happens:**
1. Script detects `extraction_progress_million.json`
2. Reads last processed index
3. Skips already-processed URLs
4. Continues from where it stopped
5. Appends new results to existing CSV

**Example output when resuming:**
```
====================================================================
🔄 RESUMING FROM PREVIOUS RUN
====================================================================
📍 Last processed index: 12,500
✅ Previously successful: 11,890
❌ Previously failed: 610
🔒 SSL valid: 10,200
⏰ Previous timestamp: 2025-11-11T08:30:45
⌚ Previous elapsed time: 1.75 hours
====================================================================
```

---

## 📊 What Gets Saved

### During Extraction (Every 100 URLs)

**File: `final_million_dataset.csv`**
- Appended with new results
- CSV format, ready for Kaggle
- Never loses data

**File: `extraction_progress_million.json`**
```json
{
  "last_processed_index": 12500,
  "total_processed": 12500,
  "successful": 11890,
  "failed": 610,
  "ssl_valid": 10200,
  "ssl_invalid": 1690,
  "timeout_errors": 320,
  "webdriver_errors": 290,
  "timestamp": "2025-11-11T08:30:45.123456",
  "elapsed_hours": 1.75
}
```

**File: `extraction_million.log`**
- Detailed log of all operations
- Timestamps for everything
- Useful for debugging

**File: `extraction_errors_million.log`**
- Only errors logged here
- Easy to review failures
- URLs that failed extraction

---

## 🔍 Progress Monitoring

### Real-Time Progress Display

While extraction is running, you'll see:

```
✅ [  12,543/1,000,000]  1.3% | Rate: 3.45/s | ETA: 79.5h | ✅11890 ❌653 (94.8%) | URL: https://example.com...
```

What this means:
- `✅` = Last URL succeeded
- `12,543/1,000,000` = Progress
- `1.3%` = Completion percentage
- `Rate: 3.45/s` = URLs per second
- `ETA: 79.5h` = Estimated time remaining
- `✅11890 ❌653` = Success/failure counts
- `(94.8%)` = Success rate
- `URL: ...` = Current URL being processed

### Progress Checker Output

```
====================================================================
📊 MAJESTIC MILLION EXTRACTION - PROGRESS MONITOR
====================================================================
🕐 Current time: 2025-11-11 10:30:45
====================================================================

📝 PROGRESS FILE STATUS
----------------------------------------------------------------------
✅ Progress file found: extraction_progress_million.json
📍 Last processed index: 12,500
📊 Total processed: 12,500
✅ Successful: 11,890
❌ Failed: 610
🔒 SSL Valid: 10,200
⚠️  SSL Invalid: 1,300
🕐 Last update: 2025-11-11T10:30:42.123456
⌚ Elapsed time: 1.75 hours
📈 Success rate: 95.12%

📁 OUTPUT FILE STATUS
----------------------------------------------------------------------
✅ Output file found: final_million_dataset.csv
📦 File size: 12.45 MB
📝 Total rows extracted: 12,500
📋 Total columns: 26

📈 OVERALL PROGRESS
----------------------------------------------------------------------
✅ Completed: 12,500 / ~1,000,000 (1.25%)
📋 Remaining: ~987,500 URLs
⏱️  Current rate: 1.98 URLs/second
⏰ Estimated time remaining: 138.5 hours (5.8 days)
🎯 Estimated completion: 2025-11-17 01:05:23
```

---

## ⏱️ Performance Estimates

Based on typical Docker Selenium performance:

| Scenario | URLs/second | Time for 1M URLs |
|----------|-------------|------------------|
| Fast | 5.0 | ~55 hours (~2.3 days) |
| Normal | 3.0 | ~92 hours (~3.8 days) |
| Slow | 2.0 | ~139 hours (~5.8 days) |

**Factors affecting speed:**
- Network speed
- Docker resources
- Website response times
- System load

---

## 🎯 After Extraction Completes

### Step 1: Verify Dataset

```powershell
python verify_final_dataset.py
```

This will show:
- ✅ Row count verification
- ✅ Column verification (all 26 features)
- ✅ Data quality checks
- ✅ Missing value analysis
- ✅ Feature statistics
- ✅ Success rate summary

### Step 2: Upload to Kaggle

Your `final_million_dataset.csv` is ready!

**For balanced training, combine with phishing data:**

```python
import pandas as pd

# Your extracted legitimate sites
df_legit = pd.read_csv('final_million_dataset.csv')

# Your phishing dataset (label=1)
df_phish = pd.read_csv('phishing_dataset.csv')

# Combine
df_combined = pd.concat([df_legit, df_phish], ignore_index=True)

# Shuffle
df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)

# Save for Kaggle
df_combined.to_csv('kaggle_training_dataset.csv', index=False)
```

### Step 3: Train LSTM Model on Kaggle

Upload `final_million_dataset.csv` (or combined dataset) to Kaggle and train your LSTM model using all 26 features!

---

## 🛠️ Troubleshooting

### Docker Selenium Not Running

**Error:** `Failed to connect to Docker Selenium`

**Fix:**
```powershell
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest
```

### Extraction is Slow

**If < 1 URL/second:**

1. **Reduce timeout:**
   - Edit `majestic_million_extractor.py`
   - Change `timeout=15` to `timeout=10`

2. **Restart Docker Selenium:**
```powershell
docker stop $(docker ps -q --filter ancestor=selenium/standalone-chrome)
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest
```

### Out of Memory

**Error:** Docker container crashes

**Fix:**
```powershell
# Increase shared memory
docker run -d -p 4444:4444 -p 7900:7900 --shm-size=4g selenium/standalone-chrome:latest
```

### Progress File Corrupted

**Rare, but if it happens:**
```powershell
# Backup corrupted file
mv extraction_progress_million.json extraction_progress_million.json.backup

# Run extraction again (won't re-process existing CSV rows)
python majestic_million_extractor.py
```

---

## 💡 Pro Tips

### 1. Monitor Multiple Ways

**Terminal 1:** Run extraction
```powershell
python majestic_million_extractor.py
```

**Terminal 2:** Watch progress
```powershell
python check_million_progress.py --watch 60
```

**Browser:** Watch Selenium in action
```
http://localhost:7900
Password: secret
```

### 2. Run Overnight Safely

1. Start extraction before bed
2. Let it run overnight
3. Check progress in the morning
4. If stopped, run again to resume

**No data will be lost!**

### 3. Estimate Completion

From progress checker:
```
⏰ Estimated time remaining: 138.5 hours (5.8 days)
🎯 Estimated completion: 2025-11-17 01:05:23
```

Plan accordingly!

### 4. Check Errors Periodically

```powershell
# View recent errors
tail -n 20 extraction_errors_million.log

# Or in PowerShell
Get-Content extraction_errors_million.log -Tail 20
```

---

## 📋 Summary Checklist

Before starting:
- [ ] Docker Selenium running (`docker ps`)
- [ ] `majestic_million.csv` exists in directory
- [ ] Python packages installed (`selenium`, `pandas`, `requests`)

During extraction:
- [ ] Monitor progress occasionally
- [ ] Check Docker Selenium status if issues
- [ ] Let it run undisturbed

If stopped:
- [ ] Don't panic! Progress is saved
- [ ] Just run the script again
- [ ] It will resume automatically

After completion:
- [ ] Run `verify_final_dataset.py`
- [ ] Check output quality
- [ ] Upload to Kaggle
- [ ] Train LSTM model

---

## 🎉 Final Notes

### What Makes This Crash-Resistant

1. **Checkpoint System**
   - Saves every 100 URLs
   - Atomic file writes
   - Never corrupts data

2. **Resume Capability**
   - Detects previous progress
   - Skips completed URLs
   - Continues where stopped

3. **Error Isolation**
   - Single URL failure doesn't stop extraction
   - WebDriver auto-recovery
   - Graceful degradation

4. **Safe Shutdown**
   - Ctrl+C saves progress
   - Cleanup on exit
   - No orphaned processes

### Your Data is SAFE

✅ Even if computer crashes  
✅ Even if Docker stops  
✅ Even if power goes out  
✅ Even if you force-close terminal  

**Maximum data loss:** Last 100 URLs (between checkpoints)

**Reality:** Usually 0 data loss because saves are atomic and frequent!

---

## 🚀 Ready to Start!

**Quick Start:**

1. **Start Docker:**
   ```powershell
   docker run -d -p 4444:4444 -p 7900:7900 --shm-size=2g selenium/standalone-chrome:latest
   ```

2. **Run Extraction:**
   ```powershell
   python majestic_million_extractor.py
   ```

3. **Monitor (optional):**
   ```powershell
   python check_million_progress.py --watch
   ```

4. **Walk Away!**
   - Let it run overnight
   - Progress is automatically saved
   - Resume anytime if stopped

**That's it!** The script handles everything else.

---

## 📞 Need Help?

**Check logs:**
- `extraction_million.log` - Full log
- `extraction_errors_million.log` - Errors only

**Check progress:**
```powershell
python check_million_progress.py
```

**Verify output:**
```powershell
python verify_final_dataset.py
```

---

**Good luck with your LSTM training on Kaggle! 🎯**

The extracted dataset will be perfect for training your phishing detection model!
