# 📱 iPhone Testing Guide for Image-to-Song App

## 🎯 **Quick Setup Overview**
Your Image-to-Song mobile app is ready for iPhone testing! Your computer's IP is `192.168.1.131` and the backend will run on port `8002`.

## 📋 **Prerequisites**
- ✅ iPhone with iOS 12+ 
- ✅ Same WiFi network for iPhone and computer
- ✅ Computer running Windows with Flutter installed
- ✅ Backend server running locally

## 🔧 **Step 1: Prepare Your Computer**

### Start the Backend Server
```bash
cd c:\Users\moksh\Desktop\image_to_song
.\backend\venv\Scripts\python.exe main_cpu.py
```
- Wait for: "Uvicorn running on http://0.0.0.0:8002"
- Backend will be accessible at: `http://192.168.1.131:8002`

### Verify Network Access
1. Open browser on your computer
2. Go to: `http://192.168.1.131:8002/health`
3. Should see: `{"status": "healthy", "timestamp": "..."}`

## 📱 **Step 2: iPhone Testing Options**

### Option A: Flutter Build for iOS (Requires Mac/Xcode)
If you have access to a Mac:
```bash
cd mobile_app
flutter build ios
# Use Xcode to install on iPhone
```

### Option B: Cloud Build Service (Recommended)
Use services like:
- **Codemagic** (Free tier available)
- **Bitrise** (Free tier available) 
- **App Center** (Microsoft)

1. Create account on chosen service
2. Connect your GitHub repository
3. Configure iOS build
4. Download .ipa file
5. Install via TestFlight or direct installation

### Option C: Web Testing (Immediate)
Test core functionality in iPhone Safari:
```bash
cd mobile_app
flutter run -d chrome
```
- Open Safari on iPhone
- Go to your computer's IP address with Flutter's port
- Test image upload and analysis

## 🌐 **Step 3: Network Configuration Verification**

### Test Backend Connectivity from iPhone
1. Open Safari on your iPhone
2. Navigate to: `http://192.168.1.131:8002/health`
3. Should see JSON response with "healthy" status

### If Connection Fails:
1. **Check WiFi**: Ensure iPhone and computer on same network
2. **Check Firewall**: Windows may block incoming connections
   - Go to Windows Defender Firewall
   - Allow Python through firewall
3. **Check IP Address**: Run `ipconfig` to verify IP hasn't changed

## 🔥 **Step 4: Windows Firewall Setup**
```powershell
# Allow Python through Windows Firewall
New-NetFirewallRule -DisplayName "Python Backend" -Direction Inbound -Program "C:\Users\moksh\Desktop\image_to_song\backend\venv\Scripts\python.exe" -Action Allow
```

## 🧪 **Step 5: Test the App Features**

### Test Sequence:
1. **🔌 Backend Connection**: Green snackbar "Connected to backend!"
2. **📷 Image Selection**: Tap image area → Select from Photos
3. **🤖 AI Analysis**: Tap "Analyze Image" → Wait for mood/caption
4. **🎵 Music Recommendations**: Automatic mixed recommendations
5. **🎧 Spotify Links**: Tap track links to open Spotify

### Expected Flow:
```
[Select Image] → [Analyze] → [View Results] → [Get Recommendations] → [Open Spotify]
```

## 🚀 **Quick Start Commands**

### Start Backend
```bash
cd c:\Users\moksh\Desktop\image_to_song
.\backend\venv\Scripts\python.exe main_cpu.py
```

### Test Backend
```bash
# In browser: http://192.168.1.131:8002/health
```

### Build for Testing
```bash
cd mobile_app
flutter clean
flutter pub get
flutter build apk --debug  # For Android testing
# OR
flutter build ios  # Requires Xcode on Mac
```

## 🔧 **Troubleshooting**

### Common Issues:

#### "Connection Refused" Error
- ✅ Backend running: Check terminal for "Uvicorn running"
- ✅ Correct IP: Verify `192.168.1.131` is your computer's IP
- ✅ Port open: Check Windows Firewall allows port 8002

#### "Image Upload Failed"
- ✅ iOS permissions: Check Camera/Photos access
- ✅ Backend logs: Look for error messages in terminal
- ✅ File size: Ensure image not too large (max 10MB)

#### "No Recommendations"
- ✅ AI service: Check backend has loaded models
- ✅ Database: Verify recommendation database accessible
- ✅ Internet: Check connection for Spotify API calls

### Debug Mode
Run backend with verbose logging:
```bash
.\backend\venv\Scripts\python.exe main_cpu.py --debug
```

## 📱 **iOS Specific Setup**

### Info.plist Permissions (Already Configured)
```xml
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to take photos for music analysis</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>This app needs photo library access to analyze your images</string>
```

### Network Security (Already Configured)
- HTTP connections allowed for local development
- TLS requirements bypassed for local IP testing

## 🎉 **Success Indicators**

✅ **Backend Running**: Terminal shows "Uvicorn running on http://0.0.0.0:8002"
✅ **Network Access**: iPhone can reach `http://192.168.1.131:8002/health`
✅ **App Connected**: Green snackbar "Connected to backend!"
✅ **Image Analysis**: App shows mood and caption after image upload
✅ **Recommendations**: List of songs appears with Spotify links

## 📞 **Need Help?**

### Check These First:
1. Backend terminal for error messages
2. iPhone WiFi connected to same network as computer
3. Computer IP address hasn't changed (`ipconfig`)
4. Windows Firewall allows Python connections

### Test in Stages:
1. Test backend API directly in computer browser
2. Test backend API from iPhone Safari
3. Test mobile app connectivity
4. Test full image analysis pipeline

Your Image-to-Song app is ready for iPhone testing! 🎵📱
