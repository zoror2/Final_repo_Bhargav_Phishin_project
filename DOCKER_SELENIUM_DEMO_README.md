# Docker Selenium Feature Extraction Demo

This demo shows how to extract features from URLs for phishing detection using Docker Selenium. It's designed to demonstrate the data extraction process to your team using a small, manageable dataset.

## 📋 Overview

- **Input**: 20 URLs (10 legitimate + 10 phishing) from `small_dataset.csv`
- **Process**: Web scraping using Docker Selenium Chrome 
- **Output**: Extracted features ready for machine learning
- **Purpose**: Team demonstration of data extraction pipeline

## 🎯 What This Demo Shows

1. **Automated Dataset Creation** - Create balanced small datasets
2. **Docker Selenium Setup** - Containerized browser automation  
3. **Feature Extraction** - Both URL-based and web content features
4. **Scalable Architecture** - Easy to expand to larger datasets
5. **Monitoring Capability** - View browser activity via VNC

## 📁 Files Created

```
small_dataset.csv              # Input: 20 balanced URLs
docker_selenium_extractor.py   # Main extraction script
run_demo.py                   # Complete automated setup
test_docker_selenium.py       # Connection testing
extracted_features.csv        # Output: ML-ready features  
extraction_report.json        # Detailed execution log
```

## 🚀 Quick Start (Automated)

**Option 1: Full Automated Demo**
```bash
python run_demo.py
```
This script handles everything automatically:
- Creates the small dataset
- Sets up Docker Selenium
- Installs requirements
- Runs feature extraction
- Shows results summary

## 🔧 Manual Setup (Step by Step)

**Prerequisites:**
- Docker Desktop installed and running
- Python 3.7+

**Step 1: Create Small Dataset**
```bash
python create_small_dataset.py
```

**Step 2: Install Python Requirements**
```bash
pip install -r selenium_requirements.txt
```

**Step 3: Start Docker Selenium**
```bash
# Pull the image
docker pull selenium/standalone-chrome:latest

# Run the container
docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" --name selenium-chrome selenium/standalone-chrome:latest
```

**Step 4: Test Connection**
```bash
python test_docker_selenium.py
```

**Step 5: Run Feature Extraction**
```bash
python docker_selenium_extractor.py
```

## 🖥️ Monitor Browser Activity

While extraction is running, you can watch the browser in real-time:
- **URL**: http://localhost:7900
- **Password**: `secret`

This shows exactly how the scraper interacts with each website.

## 📊 Features Extracted

### URL-Based Features (No Web Scraping Required)
- URL length, domain length, path length
- Number of dots, slashes, hyphens, underscores  
- Presence of IP addresses
- Suspicious keywords count
- HTTPS usage, port detection
- Subdomain analysis

### Web Content Features (Via Selenium)
- Page load success/failure
- Response time
- Page title length, page size
- HTML element counts (forms, links, images, inputs)
- Password field detection  
- External links analysis
- JavaScript/CSS presence

## 📈 Expected Results

**Sample Output:**
```
Total URLs processed: 20
Successful extractions: 18  
Failed extractions: 2
Success rate: 90.0%

Files created:
✓ extracted_features.csv - ML-ready features
✓ extraction_report.json - Detailed log
```

**Feature Count**: ~25 features per URL

## 🎯 Demo Benefits for Your Team

1. **See It Working**: Watch browser automation in real-time
2. **Understanding Scale**: Small dataset shows the process clearly
3. **Feature Insights**: See what data can be extracted from websites
4. **Pipeline Architecture**: Understand the full extraction workflow
5. **Troubleshooting**: Identify common issues with web scraping

## 🔄 Scaling to Production

After the demo, you can easily scale up:

```python
# Instead of 20 URLs, process thousands
df = pd.read_csv('full_urls_dataset.csv')  # 20,000+ URLs

# Add parallel processing
from concurrent.futures import ThreadPoolExecutor

# Add more sophisticated features
# - Screenshot analysis
# - Certificate information  
# - Network timing data
# - HTML structure analysis
```

## 🛠️ Common Issues & Solutions

**Docker Issues:**
```bash
# If container exists
docker stop selenium-chrome && docker rm selenium-chrome

# If port conflicts
docker ps -a  # Check what's using ports 4444/7900

# If memory issues  
docker run ... --shm-size="4g"  # Increase shared memory
```

**Connection Issues:**
```bash
# Check Selenium status
curl http://localhost:4444/wd/hub/status

# View container logs
docker logs selenium-chrome

# Test connection
python test_docker_selenium.py
```

**Extraction Issues:**
- Some phishing URLs may be down (normal)
- Timeout errors are handled gracefully
- Failed extractions still provide URL-based features

## 📚 Next Steps

1. **Review Results**: Examine `extracted_features.csv`
2. **Analyze Features**: See which features distinguish phishing vs legitimate
3. **Scale Up**: Apply to your full dataset
4. **Model Training**: Use features for ML model development
5. **Production Pipeline**: Implement automated feature extraction

## 🧹 Cleanup

Stop and remove Docker container:
```bash
docker stop selenium-chrome
docker rm selenium-chrome
```

## 💡 Team Discussion Points

- **Feature Engineering**: Which features are most valuable?
- **Performance**: How to handle large-scale extraction?
- **Reliability**: Dealing with website timeouts and errors  
- **Updates**: Keeping pace with evolving web technologies
- **Ethics**: Responsible web scraping practices

---

**Ready to start?** Run `python run_demo.py` and watch the magic happen! 🚀