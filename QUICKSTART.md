# 🚀 QUICK START - CityCare Backend

## ⚡ Get Running in 3 Steps:

### Step 1: Extract & Navigate
```bash
unzip citycare_backend_enhanced.zip
cd citycare_backend_enhanced
```

### Step 2: Get FREE API Token (2 minutes)
1. Visit: **https://huggingface.co/settings/tokens**
2. Sign up (FREE, no credit card)
3. Click "New token" → Select "Read"
4. Copy the token (starts with `hf_`)

### Step 3: Run Setup
```bash
# Linux/Mac
./setup.sh

# Windows
setup.bat
```

**The script will:**
- ✅ Install everything automatically
- ✅ Ask for your API token
- ✅ Start the server

---

## 🎯 Alternative: Manual 3-Command Setup

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure token
./configure_token.sh    # Linux/Mac
configure_token.bat     # Windows

# 3. Run
./run.sh               # Linux/Mac
run.bat                # Windows
```

---

## ✅ Verification

Server started successfully if you see:
```
 * Running on http://127.0.0.1:5000
```

Test it:
```bash
curl http://localhost:5000
# Should return: {"message": "CityCare API is running"}
```

---

## 📱 Connect Your Flutter App

In your Flutter app's `app_config.dart`:
```dart
static const String baseUrl = 'http://localhost:5000';
// Or your server IP: 'http://192.168.1.100:5000'
```

---

## 🔑 Already Have an API Token?

Just paste it when the setup script asks, or:

```bash
# Edit .env file
nano .env

# Find this line:
HUGGINGFACE_TOKEN=YOUR_HUGGINGFACE_TOKEN_HERE

# Replace with your token:
HUGGINGFACE_TOKEN=hf_your_actual_token_here
```

---

## 🐛 Common Issues

### "MongoDB connection failed"
```bash
# Start MongoDB
sudo systemctl start mongod    # Linux
brew services start mongodb-community  # Mac
```

### "Port 5000 already in use"
```bash
# Use different port
PORT=8000 python app.py
```

---

## 📚 Need More Details?

See **README.md** for:
- Complete documentation
- Advanced configuration
- Deployment guide
- Troubleshooting

---

## 🎉 That's It!

Your enhanced CityCare backend is ready with AI-powered image analysis!

**Start server:** `./run.sh` or `run.bat`
