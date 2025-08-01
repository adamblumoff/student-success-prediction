# Google Classroom Integration Setup Guide

## Prerequisites
- Google account with access to Google Cloud Console
- Google Workspace for Education account (for full Classroom access)
- Admin privileges to enable APIs in your organization

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select an existing project
3. Name your project (e.g., "Student Success Prediction")
4. Note the Project ID

## Step 2: Enable Google Classroom API

1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google Classroom API"
3. Click on it and press "Enable"
4. Also enable "Google Drive API" (for file access)

## Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure consent screen first if prompted:
   - Choose "External" for testing or "Internal" if you have Google Workspace
   - Fill in application name: "Student Success Prediction"
   - Add your email as developer contact
4. For OAuth client:
   - Application type: "Desktop application"
   - Name: "Student Success Prediction Desktop"
5. Download the JSON file

## Step 4: Set Up Local Credentials

1. Rename the downloaded file to `google_credentials.json`
2. Place it in the `config/` directory of this project:
   ```
   /student-success-prediction/config/google_credentials.json
   ```

## Step 5: Configure Scopes (Important!)

The application needs these Google Classroom scopes:
- `https://www.googleapis.com/auth/classroom.courses.readonly`
- `https://www.googleapis.com/auth/classroom.rosters.readonly`
- `https://www.googleapis.com/auth/classroom.coursework.students.readonly`
- `https://www.googleapis.com/auth/classroom.student-submissions.students.readonly`

## Step 6: First Time Authentication

1. Start the application: `python3 run_mvp.py`
2. Go to the web interface: http://localhost:8001
3. Click on Google Classroom integration
4. Click "Authenticate with Google Classroom"
5. Complete OAuth flow in browser
6. Grant permissions to your application

## Step 7: Test the Integration

Once authenticated, you should be able to:
- ✅ View your Google Classroom courses
- ✅ Access student rosters
- ✅ See assignment and submission data
- ✅ Generate enhanced risk predictions

## Troubleshooting

### "Access blocked" error
- Your OAuth consent screen needs to be verified by Google for production use
- For testing, add your email to "Test users" in the OAuth consent screen

### "Insufficient permissions" error
- Make sure your Google account has teacher/admin access to the classrooms
- Verify all required APIs are enabled in Google Cloud Console

### "Credentials not found" error
- Check that `config/google_credentials.json` exists and is valid JSON
- Verify the file path is correct relative to the project root

## Production Deployment Notes

For production use:
1. Submit your OAuth consent screen for verification
2. Add your domain to authorized domains
3. Use environment variables for sensitive configuration
4. Consider service account authentication for server-to-server access

## File Structure

```
config/
├── google_credentials.json          # Your OAuth2 credentials (not committed)
├── google_credentials_example.json  # Template file
└── google_token.json               # Generated after first auth (not committed)
```

## Security Notes

- **Never commit** `google_credentials.json` to version control
- The `google_token.json` file contains refresh tokens - keep it secure
- In production, use environment variables or secret management services
- Regularly rotate your OAuth2 credentials

## Support

If you encounter issues:
1. Check the application logs for specific error messages
2. Verify your Google Cloud Console settings
3. Ensure your Google account has appropriate classroom access
4. Test with a simple classroom first before scaling