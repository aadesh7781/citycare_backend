# 🏙️ CityCare Backend - Enhanced Edition

## ✨ What's Included:

This is a **pre-configured, ready-to-run** CityCare backend with AI-powered image analysis for smart urgency calculation.

### 🆕 New Features:
- ✅ **AI Image Analysis** - Automatically detects damage severity from photos
- ✅ **Smart Urgency Scoring** - Combines text + image analysis (0-100 scale)
- ✅ **Free API Integration** - Uses Hugging Face (30,000 free requests/month)
- ✅ **Automated Setup** - One-command installation
- ✅ **Pre-configured** - All files ready to go

---

## 🚀 Quick Start (2 Options):

### Option 1: Automated Setup (Recommended)

```bash
# 1. Extract the zip file
unzip citycare_backend_enhanced.zip
cd citycare_backend_enhanced

# 2. Run the setup script
./setup.sh

# That's it! The script will:
# - Create virtual environment
# - Install dependencies
# - Create upload directories
# - Ask for your Hugging Face token
# - Start the server
```

### Option 2: Manual Setup

```bash
# 1. Extract and navigate
unzip citycare_backend_enhanced.zip
cd citycare_backend_enhanced

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API token (see below)
nano .env  # Edit HUGGINGFACE_TOKEN line

# 5. Start server
python app.py
```

---

## 🔑 Get Your FREE Hugging Face API Token:

### Step 1: Create Account (2 minutes)
1. Visit: https://huggingface.co
2. Click "Sign Up" (FREE, no credit card)
3. Verify your email

### Step 2: Create Token (1 minute)
1. Go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. Name: "CityCare"
4. Type: "Read"
5. Click "Generate"
6. Copy the token (starts with "hf_")

### Step 3: Configure (30 seconds)
```bash
# Option A: During setup script
# The setup.sh script will ask you for the token

# Option B: Edit .env file manually
nano .env
# Find this line:
# HUGGINGFACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE
# Replace YOUR_HUGGINGFACE_TOKEN_HERE with your token
```

---

## 📁 Package Structure:

```
citycare_backend_enhanced/
├── app.py                      # Main Flask application
├── config.py                   # Configuration
├── requirements.txt            # Python dependencies (with 'requests')
├── .env                        # Environment variables (CONFIGURED)
├── setup.sh                    # Automated setup script ⭐
├── run.sh                      # Quick run script
├── README.md                   # This file
│
├── routes/
│   ├── auth_routes.py          # Login/register
│   ├── complaint_routes.py     # Complaints (WITH IMAGE ANALYSIS) ⭐
│   ├── officer_routes.py       # Officer functions
│   ├── analytics_routes.py     # Analytics
│   └── authorities_routes.py   # Authorities
│
├── utils/
│   ├── urgency_engine.py       # AI-powered urgency calculator ⭐
│   ├── database.py             # MongoDB connection
│   ├── image_upload.py         # Image handling
│   └── helpers.py              # Helper functions
│
├── middleware/
│   └── auth_middleware.py      # JWT authentication
│
├── models/
│   ├── user.py                 # User model
│   └── complaint.py            # Complaint model
│
└── uploads/                    # Auto-created by setup.sh
    ├── complaints/             # User complaint images
    └── officer_proofs/         # Officer resolution proofs
```

---

## 🎯 What's Already Configured:

### ✅ Database:
- MongoDB connection string: `mongodb://localhost:27017/citycare`
- Database name: `citycare`

### ✅ Server:
- Port: `5000`
- Debug mode: Enabled
- CORS: Enabled for all origins

### ✅ Upload Settings:
- Max file size: 10MB
- Allowed formats: jpg, jpeg, png, gif, webp
- Upload directories: Auto-created

### ✅ AI Image Analysis:
- **urgency_engine.py** - Enhanced with Hugging Face CLIP model
- **complaint_routes.py** - Updated to use image analysis
- Fallback to text-only if API unavailable

### ⚠️ Needs Configuration:
- **HUGGINGFACE_TOKEN** in `.env` file (the setup script helps with this)

---

## 🔧 Running the Server:

### Method 1: Using run.sh (Easiest)
```bash
./run.sh
```

### Method 2: Direct Python
```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run server
python app.py
```

### Method 3: With custom port
```bash
PORT=8000 python app.py
```

---

## 📊 How Image Analysis Works:

### Flow:
```
User submits complaint with photo
         ↓
Backend saves image
         ↓
Text analysis (keywords + category)
         ↓
Image analysis via Hugging Face API ⭐
  - Sends image to CLIP model
  - Model detects damage severity
  - Returns confidence scores
         ↓
Calculate combined urgency
  Base: 30 points
  + Text: 0-40 points
  + Category: 10-35 points  
  + Image: 0-30 points ⭐
  = Total: 0-100 points
         ↓
Save complaint with urgency score
```

### Example Scores:

| Description | Image | Text | Category | Image Boost | Total |
|------------|-------|------|----------|-------------|-------|
| "Small pothole" | No image | 50 | 20 | 0 | **70** |
| "Small pothole" | Minor damage | 50 | 20 | 10 | **80** |
| "Small pothole" | Severe damage | 50 | 20 | 30 | **100** ⚡ |

---

## 🧪 Testing:

### 1. Start the server:
```bash
./run.sh
```

### 2. Test basic endpoint:
```bash
curl http://localhost:5000/
# Should return: {"message": "CityCare API is running"}
```

### 3. Submit a complaint (from Flutter app):
- Upload a photo showing damage
- Check server logs for:
```
📸 Image analysis boost: +25
✅ Calculated urgency: 95 (with image analysis)
```

### 4. Verify in MongoDB:
```bash
mongosh
use citycare
db.complaints.find().sort({urgency: -1}).pretty()
```

---

## 📝 Configuration Files:

### .env (Pre-configured)
```bash
MONGO_URI=mongodb://localhost:27017/citycare
DATABASE_NAME=citycare
JWT_SECRET=citycare-secret-key-2024-change-in-production-please
HUGGINGFACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE  # ⚠️ SET THIS
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000
```

### requirements.txt (Updated)
```
Flask==3.0.0
Flask-CORS==4.0.0
pymongo==4.6.0
python-dotenv==1.0.0
PyJWT==2.8.0
bcrypt==4.1.2
Pillow==10.2.0
requests==2.31.0  # ⭐ NEW - For API calls
```

---

## 🐛 Troubleshooting:

### Issue: "No HUGGINGFACE_TOKEN set"
**Solution:**
```bash
# Edit .env file
nano .env
# Set your token:
HUGGINGFACE_TOKEN=hf_your_actual_token_here
```

### Issue: "MongoDB connection failed"
**Solution:**
```bash
# Check if MongoDB is running
sudo systemctl status mongod  # Linux
brew services list             # macOS

# Start MongoDB
sudo systemctl start mongod   # Linux
brew services start mongodb-community  # macOS
```

### Issue: "Image analysis timed out"
**Solution:**
```bash
# Check internet connection
ping -c 3 api-inference.huggingface.co

# The system automatically falls back to text-only analysis
```

### Issue: "Port 5000 already in use"
**Solution:**
```bash
# Use different port
PORT=8000 python app.py
```

---

## 📈 Monitoring:

### Check logs while running:
```bash
# Server logs show:
✅ Calculated urgency: 85 (with image analysis)
📸 Image analysis boost: +25
```

### Database queries:
```javascript
// MongoDB shell
use citycare

// Get all complaints sorted by urgency
db.complaints.find().sort({urgency: -1})

// Count by status
db.complaints.aggregate([
  {$group: {_id: "$status", count: {$sum: 1}}}
])

// Get high-urgency complaints
db.complaints.find({urgency: {$gte: 80}})
```

---

## 🔒 Security Notes:

### Before Production:
1. **Change JWT Secret:**
```bash
# In .env file
JWT_SECRET=your-very-long-random-secret-here
```

2. **Update CORS:**
```bash
# In .env file
CORS_ORIGINS=https://your-flutter-app.com
```

3. **Use HTTPS:**
```bash
# Use nginx or Apache as reverse proxy
# Or use Gunicorn with SSL certificates
```

4. **Secure MongoDB:**
```bash
# Enable authentication
# Use strong passwords
# Restrict network access
```

---

## 🚀 Deployment:

### Using Gunicorn (Production):
```bash
# Install
pip install gunicorn

# Run
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker:
```bash
# Build
docker build -t citycare-backend .

# Run
docker run -p 5000:5000 citycare-backend
```

### Environment Variables for Production:
```bash
FLASK_ENV=production
FLASK_DEBUG=False
MONGO_URI=mongodb://your-production-db:27017/citycare
JWT_SECRET=your-super-secret-key
```

---

## 📊 API Endpoints:

### Public:
- `POST /auth/register` - User registration
- `POST /auth/login` - User login

### User (requires token):
- `POST /complaints/submit` - Submit complaint (with image analysis)
- `GET /complaints/my-complaints` - Get user's complaints
- `GET /complaints/<id>` - Get complaint details

### Officer (requires officer role):
- `GET /officer/complaints` - Get all complaints (sorted by urgency)
- `GET /officer/complaints/<id>` - Get complaint details
- `PUT /officer/complaints/<id>/status` - Update status (with proof photo)
- `GET /officer/profile` - Get officer profile

### Analytics:
- `GET /analytics/dashboard` - Get analytics data

---

## 💡 Tips:

1. **Monitor API Usage:**
   - Free tier: 30,000 requests/month
   - Check dashboard: https://huggingface.co/settings/billing

2. **Optimize Performance:**
   - Compress images before upload in Flutter app
   - Cache image analysis results for duplicate images
   - Use CDN for static files

3. **Backup Database:**
   ```bash
   mongodump --db citycare --out /backup/$(date +%Y%m%d)
   ```

4. **Update Dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## 📞 Support:

### Need Help?
1. Check logs: `tail -f app.log`
2. Check MongoDB: `mongosh`
3. Test API token: `curl https://api-inference.huggingface.co/status -H "Authorization: Bearer YOUR_TOKEN"`

### Resources:
- Hugging Face Docs: https://huggingface.co/docs/api-inference
- Flask Docs: https://flask.palletsprojects.com
- MongoDB Docs: https://www.mongodb.com/docs

---

## ✅ Checklist:

Before starting:
- [ ] MongoDB installed and running
- [ ] Python 3.8+ installed
- [ ] Extracted zip file
- [ ] Hugging Face account created
- [ ] API token obtained

Setup:
- [ ] Ran `./setup.sh` or manual setup
- [ ] Configured HUGGINGFACE_TOKEN in .env
- [ ] Dependencies installed
- [ ] Upload directories created

Testing:
- [ ] Server starts without errors
- [ ] Can submit complaint with photo
- [ ] See image analysis in logs
- [ ] Urgency scores are correct

---

## 🎉 You're All Set!

Your CityCare backend is configured and ready to run with AI-powered image analysis!

**Start the server:**
```bash
./run.sh
```

**Or use automated setup:**
```bash
./setup.sh
```

Enjoy! 🚀
