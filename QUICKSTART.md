# DLBot - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Setup (2 minutes)

1. Open the DLBot folder
2. **Double-click `setup.bat`** and wait for it to complete
3. You'll see a message saying "Setup Completed Successfully!"

That's it! All dependencies are installed automatically.

### Step 2: Launch (30 seconds)

**Double-click `run.bat`** to start DLBot

You should see a window with:
- Empty account list
- Start All / Stop All buttons
- Settings button

### Step 3: Add an Account (2 minutes)

1. Click **Settings** button
2. Click **Add Account** tab (if not already there)
3. Click **Add Account** button
4. Fill in the form:

   **For YouTube:**
   - Name: `PewDiePie`
   - Platform: `YouTube`
   - URL: `https://www.youtube.com/c/PewDiePie`
   - Download Path: Click **Browse** and select a folder
   - Click **OK**

   **For Bilibili:**
   - Name: `Creator Name`
   - Platform: `Bilibili`
   - URL: `https://space.bilibili.com/123456789`
   - Download Path: Select folder
   - Click **OK**

5. Click **OK** to close Settings

### Step 4: Start Listening (10 seconds)

Back in main window:
1. Find your account in the list
2. Click **Start** button
3. Watch the status change to "● Listening"

✅ DLBot is now downloading new videos!

---

## 📝 Common Tasks

### Find Downloaded Videos

1. Check the **Download Path** you set
2. Videos will be saved there with the account name

### Change Settings

1. Click **Settings**
2. Go to the tab you need:
   - **Accounts**: Manage your accounts
   - **Storage**: Change download location, check frequency
   - **General**: Theme, tray options

### Stop Listening

Click **Stop** next to an account to pause listening

### Access from System Tray

When closed, DLBot stays in the system tray (bottom-right corner):
1. Right-click the DLBot icon in the tray
2. Select **Show** to open it
3. Select **Hide** to close it
4. Select **Exit** to quit completely

---

## 🆘 Troubleshooting

### "Python is not installed"
- Install Python from https://www.python.org/
- Make sure to **check** "Add Python to PATH"
- Restart your computer

### "No videos downloading"
- Check that the account URL is correct
- Make sure the download folder exists and you have write permission
- Try manually checking with a longer interval

### Setup.bat won't run
- Right-click setup.bat → Run as Administrator
- Make sure you have write permission in the DLBot folder

### DLBot won't start
- Open Command Prompt in DLBot folder
- Run: `python main.py`
- Look for error messages

---

## ⚡ Tips

1. **Multiple Accounts**: Add as many accounts as you want, each runs independently
2. **Lower Check Interval**: Means more frequent checks (but uses more bandwidth)
3. **Different Folders**: Save different creators' content to different folders
4. **Always Run**: You can close/minimize to tray and keep it running in background

---

## 📚 Need More Help?

- **Detailed Guide**: Read `README.md`
- **Developer Info**: Check `DEVELOPER.md`
- **Logs**: Look in `logs/dlbot.log` for errors

---

## ✨ Features at a Glance

✅ Automatically downloads new videos
✅ Supports YouTube and Bilibili
✅ Individual control for each account
✅ Clean, easy-to-use interface
✅ Runs in background
✅ Auto-start on system startup (optional)
✅ Real-time status indicators

---

Enjoy! 🎉
