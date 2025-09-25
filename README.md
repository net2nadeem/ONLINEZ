# 🚀 DamaDam Profile Scraper (GitHub Actions)

Automated profile scraper for DamaDam.pk that runs every 15 minutes on GitHub Actions and exports data to Google Sheets.

## ✨ Features

- 🔄 **Automated Execution**: Runs every 15 minutes automatically
- ☁️ **Cloud-Based**: No need to keep your PC running
- 🔒 **Secure**: Passwords stored in GitHub Secrets
- 📊 **Google Sheets Integration**: Direct export to spreadsheet
- 🚀 **Optimized**: Fast scraping with smart duplicate handling
- 📝 **Detailed Logging**: Complete execution logs

## 📋 Prerequisites

1. **GitHub Account** (free)
2. **Google Account** with Google Sheets access
3. **DamaDam Account** with login credentials
4. **Basic understanding** of copy-paste operations

## 🛠️ Setup Instructions

### Step 1: Create GitHub Repository

1. **Go to GitHub.com** and log in
2. **Click "New Repository"** (green button)
3. **Repository Name**: `damadam-scraper` (or any name you prefer)
4. **Set to Public** (required for free GitHub Actions)
5. **Check "Add README file"**
6. **Click "Create Repository"**

### Step 2: Upload Code Files

1. **In your new repository**, click **"Add file" → "Create new file"**
2. **Create these files one by one:**

#### File 1: `main.py`
- Copy the entire `main.py` code from above
- Paste it in GitHub

#### File 2: `requirements.txt`
- Copy the requirements.txt content
- Paste it in GitHub

#### File 3: `.github/workflows/scraper.yml`
- **Important**: Create folder structure first
- Type `.github/workflows/scraper.yml` as filename
- Copy the workflow YAML content
- Paste it in GitHub

### Step 3: Create Google Service Account

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create New Project** or select existing one
3. **Enable Google Sheets API**:
   - Go to "APIs & Services" → "Library"
   - Search "Google Sheets API"
   - Click "Enable"
4. **Create Service Account**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Name: `damadam-scraper`
   - Click "Create and Continue"
   - Skip roles for now, click "Done"
5. **Generate JSON Key**:
   - Click on your service account email
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key"
   - Choose "JSON" format
   - Download the JSON file

### Step 4: Setup Google Sheets

1. **Create New Google Sheet**: https://sheets.google.com/
2. **Name it**: `DamaDam Profiles` (or any name)
3. **Copy the Sheet URL** from address bar
4. **Share with Service Account**:
   - Click "Share" button in Google Sheets
   - Add the service account email (from JSON file)
   - Give "Editor" permissions
   - Uncheck "Notify people"
   - Click "Share"

### Step 5: Add GitHub Secrets

1. **In your GitHub repository**, go to **"Settings"** tab
2. **Click "Secrets and variables"** → **"Actions"**
3. **Click "New repository secret"** and add these secrets:

#### Required Secrets:
| Secret Name | Value | Example |
|-------------|-------|---------|
| `DAMADAM_USERNAME` | Your DamaDam username | `username` |
| `DAMADAM_PASSWORD` | Your DamaDam password | `password` |
| `GOOGLE_SHEET_URL` | Your Google Sheet URL | `https://docs.google.com/spreadsheets/d/...` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Entire JSON file content | `{"type": "service_account",...}` |

#### How to add each secret:
1. Click "New repository secret"
2. Enter "Name" (exactly as shown above)
3. Paste the "Value"
4. Click "Add secret"
5. Repeat for all 4 secrets

### Step 6: Test the Setup

1. **Go to "Actions" tab** in your repository
2. **Click "DamaDam Profile Scraper"** workflow
3. **Click "Run workflow"** button (manual test)
4. **Click green "Run workflow"** button
5. **Wait 2-3 minutes** and check if it runs successfully

## 🎯 How It Works

```
┌─────────────────┐    ┌──────────────┐    ┌──────────────┐
│   GitHub Actions │───▶│   Scraper    │───▶│ Google Sheets │
│   (Every 15 min) │    │   (Cloud)    │    │   (Results)   │
└─────────────────┘    └──────────────┘    └──────────────┘
```

1. **Every 15 minutes**, GitHub Actions automatically runs the scraper
2. **Scraper logs in** to DamaDam using your credentials
3. **Fetches online users** and scrapes their profiles
4. **Exports data** directly to your Google Sheets
5. **Handles duplicates** by updating seen count

## 📊 Google Sheets Output

Your spreadsheet will have these columns:
- **DATE, TIME**: When profile was scraped
- **NICKNAME**: Username
- **CITY, GENDER, MARRIED, AGE**: Profile details
- **JOINED**: When they joined DamaDam
- **FOLLOWERS, POSTS**: Activity metrics
- **PLINK**: Profile URL
- **PIMAGE**: Profile image URL
- **INTRO**: User bio/introduction
- **SCOUNT**: How many times seen online

## 🔧 Troubleshooting

### Common Issues:

#### 1. "Secrets not found" error
- **Solution**: Double-check secret names are EXACTLY as specified
- Make sure no extra spaces or typos

#### 2. "Google Sheets access denied"
- **Solution**: Make sure you shared the sheet with service account email
- Check the service account has "Editor" permissions

#### 3. "Login failed"
- **Solution**: Verify your DamaDam username/password are correct
- Check if your account is not temporarily blocked

#### 4. Workflow not running automatically
- **Solution**: Make sure repository is **Public** (private repos have limited free Actions)
- Check if you have enough GitHub Actions minutes

### Check Logs:
1. Go to **"Actions"** tab in GitHub
2. Click on latest run
3. Click on **"scrape-profiles"** job
4. Expand any step to see detailed logs

## ⚙️ Customization

### Change Schedule:
Edit `.github/workflows/scraper.yml`:
```yaml
schedule:
  - cron: '*/30 * * * *'  # Every 30 minutes
  - cron: '0 */2 * * *'   # Every 2 hours
  - cron: '0 9 * * *'     # Daily at 9 AM
```

### Change Delays:
Edit `main.py` variables:
```python
MIN_DELAY = 1.0  # Minimum delay between requests
MAX_DELAY = 2.0  # Maximum delay between requests
```

## 🛡️ Security Notes

- ✅ **Passwords are encrypted** in GitHub Secrets
- ✅ **No sensitive data** in code
- ✅ **Google API** uses service account (secure)
- ✅ **Logs don't show** passwords or keys

## 📱 Monitoring

### Check if it's working:
1. **Google Sheets**: New data appears every 15 minutes
2. **GitHub Actions**: Green checkmarks in Actions tab
3. **Logs**: Detailed execution logs in Actions

### Get notifications:
- GitHub will email you if workflow fails
- Check your Google Sheet for regular updates

## 🆘 Support

If you encounter issues:
1. **Check the logs** in GitHub Actions
2. **Verify all secrets** are set correctly
3. **Test Google Sheets** access manually
4. **Ensure DamaDam login** works in browser

## 📈 Performance

- **Runs every 15 minutes** automatically
- **~50-100 profiles** per run (depending on online users)
- **Smart duplicate handling** (updates seen count)
- **Optimized for cloud** execution

---

### 🎉 That's it! Your scraper will now run automatically every 15 minutes and save all data to your Google Sheet!
