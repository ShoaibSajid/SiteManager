# Vercel Deployment Fix

## Changes Made

1. **Created `/api/index.py`** - Vercel serverless function handler
   - Properly imports the Flask app
   - Sets Vercel environment variable
   - Exports handler for Vercel

2. **Updated `vercel.json`**
   - Points to `api/index.py` as the entry point
   - Uses `@vercel/python` builder

3. **Updated `app.py`**
   - Uses `/tmp` for uploads on Vercel (serverless requirement)
   - Better error handling for missing Excel files
   - Graceful handling when analyzer can't be created

4. **Updated `requirements.txt`**
   - Added `werkzeug==3.0.1` explicitly

## Important Notes for Vercel

1. **Excel File**: The Excel file `Data Jul-Nov 2025.xlsx` needs to be:
   - Committed to your repository, OR
   - Uploaded via the web interface after deployment

2. **File Storage**: Uploaded files are stored in `/tmp` on Vercel (ephemeral storage)
   - Files are lost between function invocations
   - Consider using Vercel Blob Storage for persistent storage

3. **Function Timeout**: Vercel free tier has 10-second timeout
   - Large Excel files may timeout
   - Consider upgrading or optimizing data processing

## Deployment Steps

1. Make sure all files are committed:
   ```bash
   git add .
   git commit -m "Fix Vercel deployment"
   git push
   ```

2. Vercel will automatically redeploy

3. After deployment, upload the Excel file via the web interface

## Testing Locally

To test the Vercel handler locally:
```bash
python3 -c "import sys; sys.path.insert(0, '.'); from api.index import handler; print('OK')"
```

## If Still Getting Errors

1. Check Vercel logs for the exact error message
2. Verify all dependencies are in `requirements.txt`
3. Make sure the Excel file exists or upload it first
4. Check that `api/index.py` is in the repository

