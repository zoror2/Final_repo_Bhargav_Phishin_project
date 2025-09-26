# 🛡️ ScamiFy - Complete Setup Guide for Your Friend

## 📋 What is ScamiFy?

ScamiFy is an advanced Chrome extension that protects you from phishing websites using AI. It has two smart AI models:
- **🧠 ANN Model**: Super fast checking (in less than 1 second)
- **🔍 LSTM Model**: Deep analysis (takes 2-3 seconds but very accurate)

The extension warns you before you visit dangerous websites and keeps you safe while browsing!

## 🎯 Requirements

Before starting, make sure you have:
- Windows computer (you're using Windows, so ✅)
- Google Chrome browser
- Python 3.8 or newer (we'll install this)
- About 2GB of free disk space

## 📥 Step 1: Download and Install Python

1. Go to https://python.org/downloads/
2. Click the big yellow "Download Python" button
3. Run the installer and **IMPORTANT**: Check "Add Python to PATH"
4. Click "Install Now"
5. When done, open PowerShell and type: `python --version`
   - You should see something like "Python 3.11.x"

## 📁 Step 2: Get the Project Files

### Option A: Download ZIP (Easiest)
1. Go to your GitHub repository
2. Click the green "Code" button
3. Click "Download ZIP"
4. Extract to a folder like `C:\ScamiFy`

### Option B: Use Git (if you have it)
```powershell
git clone https://github.com/yourusername/ScamiFy.git
cd ScamiFy
```

## 🔧 Step 3: Install Python Dependencies

Open PowerShell in the ScamiFy folder and run:

```powershell
# Navigate to the backend folder
cd "Scamify-main\Extension\backend"

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Install all required packages
pip install -r requirements.txt
```

**If you get an error**, try:
```powershell
# Alternative installation command
pip install Flask==3.0.3 Flask-CORS==4.0.1 numpy==1.26.4 pandas==2.2.3 scikit-learn==1.5.2 joblib==1.4.2 tensorflow==2.18.0 requests==2.32.3 selenium==4.15.0 webdriver-manager==4.0.1
```

## 🚀 Step 4: Start the Backend Server

```powershell
# Make sure you're in the backend folder and venv is activated
cd "Scamify-main\Extension\backend"
venv\Scripts\activate

# Start the server
python app.py
```

You should see:
```
Starting AI Phishing Detection Backend...
ANN model imported successfully
LSTM model imported successfully
Server starting on http://127.0.0.1:5000
```

**Keep this window open!** The server needs to run for the extension to work.

## 🌐 Step 5: Install the Chrome Extension

1. Open Google Chrome
2. Go to `chrome://extensions/`
3. Turn on "Developer mode" (toggle in top-right)
4. Click "Load unpacked"
5. Navigate to your ScamiFy folder
6. Select: `Scamify-main\Extension\phishing-extension`
7. Click "Select Folder"

You should now see ScamiFy in your extensions!

## ✅ Step 6: Test Everything Works

### Test the Backend
1. Go to http://127.0.0.1:5000/health in your browser
2. You should see a JSON response with "status": "healthy"

### Test the Extension
1. Go to any website
2. You should see a small ScamiFy icon in your browser toolbar
3. The extension will automatically check suspicious links

### Test with Demo Page
1. Open: `Scamify-main\Extension\phishing-extension\test-integration.html`
2. Try hovering over the test links
3. You should see warnings for suspicious links

## 🎮 How to Use ScamiFy

### Daily Usage
1. **Start the Backend**: Run `python app.py` in the backend folder
2. **Browse Normally**: The extension works automatically
3. **Check Warnings**: If you see a warning, read it carefully before proceeding

### What You'll See
- **✅ Green**: Safe websites
- **⚠️ Yellow**: Suspicious websites (be careful)
- **❌ Red**: Dangerous phishing websites (don't proceed)

## 🔧 Common Problems and Solutions

### Problem: "ModuleNotFoundError"
**Solution**: Make sure you activated the virtual environment
```powershell
cd "Scamify-main\Extension\backend"
venv\Scripts\activate
pip install -r requirements.txt
```

### Problem: "Server not starting"
**Solution**: 
1. Check if port 5000 is in use: `netstat -ano | findstr :5000`
2. Kill any process using port 5000
3. Try again

### Problem: "Extension not loading"
**Solution**:
1. Make sure Developer mode is ON in `chrome://extensions/`
2. Try removing and re-adding the extension
3. Check for any errors in the extension details

### Problem: "ANN model not found"
**Solution**: The extension will work with a fallback model. It's still functional!

### Problem: "LSTM model not available"  
**Solution**: Make sure you have all the model files in the backend folder.

## 📁 Important Files (Don't Delete These!)

```
ScamiFy/
├── Scamify-main/Extension/backend/
│   ├── app.py (Main server file)
│   ├── requirements.txt (Python packages)
│   └── models/ (AI model files)
├── Scamify-main/Extension/phishing-extension/
│   ├── manifest.json (Extension config)
│   └── content-fixed.js (Main extension code)
└── basic_lstm_model_best.h5 (AI model)
```

## 🛠️ Advanced Features (Optional)

### Running Tests
```powershell
cd "Scamify-main\Extension\backend"
python test_fixed_endpoints.py
```

### Viewing Live Stats
- Open the extension popup to see scanning statistics
- Check http://127.0.0.1:5000/health for system health

## 🆘 Getting Help

### Check Server Status
Go to: http://127.0.0.1:5000/health

### Common Commands
```powershell
# Check if Python is installed
python --version

# Check if server is running
curl http://127.0.0.1:5000/health

# Restart the server
# Press Ctrl+C to stop, then run python app.py again
```

### If Nothing Works
1. Make sure Python is installed and in PATH
2. Make sure all packages are installed (`pip list`)
3. Make sure the server is running (you should see it in PowerShell)
4. Try reloading the Chrome extension
5. Check the Chrome console for errors (F12)

## 🎉 You're All Set!

Once everything is working:
1. Keep the PowerShell window open (this is your server)
2. The extension will protect you automatically
3. You can close and reopen Chrome - the extension stays installed
4. When you restart your computer, you'll need to start the server again

## 💡 Pro Tips

- **Always start the server first**, then use the extension
- **Don't close the PowerShell window** while browsing
- **Trust the warnings** - the AI is very accurate
- **You can always proceed** if you're sure a site is safe (click "Proceed Anyway")

---

**🎊 Congratulations! You now have enterprise-level phishing protection!**

If you have any issues, check this guide again or ask for help!