# Finding Your 62 Articles

## The 62 articles belong to these 4 users:

1. **Udcd08cd8a445c68f462a739e8898abb9** - Has ~36 articles
2. **U2de324e2a7198cf6ef152ab22afc80ea** - Has 26 articles  
3. **U4e61eb9b003d63f8dc30bb98ae91b859** - Has some articles
4. **test123** - Test user with some articles

## To find YOUR articles:

### Step 1: Get your User ID
1. Go to: https://article-hub-959205905728.asia-northeast1.run.app/dashboard
2. Click the **"Debug"** link (top right corner)
3. Copy your User ID from the popup

### Step 2: Check if you own the articles

Compare your User ID with the list above. 

- **If your ID matches one above**: Your articles should appear! Try:
  - Clear browser cache (Ctrl+Shift+Delete)
  - Logout and login again
  - Open browser console (F12) and check for errors

- **If your ID is different**: The articles belong to another account. You have two options:

### Option A: Migrate ALL articles to your account

I'll create a Cloud Function to migrate all 62 articles to your account. Just tell me your User ID.

### Option B: Test with existing data

Visit this URL to see the articles using a test account:
https://article-hub-959205905728.asia-northeast1.run.app/dashboard?test=true

### Option C: Start fresh

Send URLs to the LINE bot to save new articles to YOUR account.

## Most Likely Scenario

You probably logged in with a different LINE account than the one that saved those 62 articles. The articles are tied to specific LINE User IDs, so they only appear for those users.

## Quick Test

After getting your User ID, test the API directly:
```
https://article-hub-959205905728.asia-northeast1.run.app/api/articles?stage=inbox&user_id=YOUR_USER_ID_HERE
```

This will show if you have any articles in the database.