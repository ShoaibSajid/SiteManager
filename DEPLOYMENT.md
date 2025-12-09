# Deployment Guide

This Flask application can be deployed to various platforms. Choose the option that works best for you.

## Option 1: Railway (Recommended - Easiest)

Railway is the easiest way to deploy this Flask app.

### Steps:

1. **Sign up for Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy from GitHub**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose this repository
   - Railway will automatically detect it's a Python app

3. **Upload Excel File**
   - In Railway dashboard, go to your project
   - Click on "Variables" tab
   - You'll need to upload the Excel file `Data Jul-Nov 2025.xlsx` to the project
   - Or use Railway's file system to upload it

4. **Deploy**
   - Railway will automatically build and deploy
   - Your app will be live at a URL like: `https://your-app-name.railway.app`

### Alternative: Deploy via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

---

## Option 2: Render (Free Tier Available)

Render offers a free tier perfect for demos.

### Steps:

1. **Sign up for Render**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select this repository

3. **Configure Settings**
   - **Name**: Choose a name for your service
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free (or paid if you need more resources)

4. **Upload Excel File**
   - After deployment, you can upload the Excel file via:
     - Render's file system (SSH into the service)
     - Or modify the app to accept file uploads

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically
   - Your app will be live at: `https://your-app-name.onrender.com`

---

## Option 3: Vercel (Serverless)

Vercel requires converting the Flask app to serverless functions. This is more complex but works well.

### Steps:

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel
   ```

3. **Upload Excel File**
   - You'll need to upload the Excel file to Vercel's file system
   - Or use Vercel's environment variables for file storage
   - Consider using a cloud storage service (S3, Cloudinary) for the Excel file

4. **Note**: Vercel has a 10-second timeout on free tier, which might be too short for large Excel processing. Consider Railway or Render instead.

---

## Option 4: PythonAnywhere (Simple & Free)

Great for Python apps with a simple interface.

### Steps:

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Files**
   - Use the Files tab to upload all your project files
   - Upload the Excel file to the same directory

3. **Create Web App**
   - Go to Web tab
   - Click "Add a new web app"
   - Choose Flask and Python 3.10
   - Set the source code directory

4. **Configure WSGI**
   - Edit the WSGI file to point to your `app.py`

5. **Reload**
   - Click the green reload button
   - Your app will be live at: `yourusername.pythonanywhere.com`

---

## Important Notes

### Excel File Location

All platforms require the Excel file `Data Jul-Nov 2025.xlsx` to be accessible. Options:

1. **Upload to the deployment platform** (easiest for demos)
2. **Use cloud storage** (S3, Google Drive, etc.) and modify the code to fetch from there
3. **Use environment variables** to specify the file path

### Environment Variables

If you need to configure the Excel file path dynamically, you can modify `app.py`:

```python
EXCEL_FILE = os.getenv('EXCEL_FILE', 'Data Jul-Nov 2025.xlsx')
```

Then set `EXCEL_FILE` as an environment variable in your deployment platform.

### File Size Limits

- **Railway**: No strict limits on free tier
- **Render**: 100MB disk space on free tier
- **Vercel**: 50MB function size limit
- **PythonAnywhere**: 512MB on free tier

---

## Quick Start (Recommended: Railway)

1. Push your code to GitHub
2. Go to railway.app and sign up
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Upload the Excel file via Railway's file system
6. Your app is live! 🎉

---

## Troubleshooting

### Port Issues
- Make sure your app binds to `0.0.0.0` and uses the `$PORT` environment variable
- The Procfile already handles this

### Excel File Not Found
- Ensure the Excel file is in the root directory of your project
- Check file permissions
- Verify the file name matches exactly (case-sensitive)

### Dependencies Issues
- Make sure `requirements.txt` includes all dependencies
- Some platforms may need `gunicorn` for production

### Memory Issues
- Large Excel files may cause memory issues on free tiers
- Consider optimizing the data processing or upgrading your plan

