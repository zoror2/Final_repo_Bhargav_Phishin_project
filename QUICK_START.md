## 🚀 Quick Start (for the impatient friend)

Don't want to read the long guide? Here's the super quick version:

### 5-Minute Setup
1. **Install Python**: Download from python.org, check "Add to PATH"
2. **Download project**: Get ZIP from GitHub, extract to `C:\ScamiFy`
3. **Install stuff**: 
   ```powershell
   cd "C:\ScamiFy\Scamify-main\Extension\backend"
   pip install Flask tensorflow pandas scikit-learn selenium flask-cors
   ```
4. **Start server**: `python app.py`
5. **Add extension**: Chrome → `chrome://extensions/` → Developer mode ON → Load unpacked → Select `phishing-extension` folder
6. **Done!** Keep the PowerShell window open and browse safely!

### Test it works:
- Go to http://127.0.0.1:5000/health (should show "healthy")  
- Extension icon should appear in Chrome toolbar
- Try the test page in the extension folder

**Remember**: Always start the server (`python app.py`) before using the extension!