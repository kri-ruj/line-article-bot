# GitHub Repository Setup Guide

## Install GitHub CLI (gh)

### Windows (Choose one method):

#### Method 1: Using winget (Recommended)
```bash
winget install --id GitHub.cli
```

#### Method 2: Using Chocolatey
```bash
choco install gh
```

#### Method 3: Using Scoop
```bash
scoop install gh
```

#### Method 4: Download Installer
1. Go to: https://cli.github.com/
2. Download the MSI installer for Windows
3. Run the installer

---

## Setup GitHub CLI

### 1. Authenticate with GitHub
```bash
gh auth login
```
- Choose: GitHub.com
- Choose: HTTPS
- Authenticate with browser or token
- Follow the prompts

### 2. Verify Authentication
```bash
gh auth status
```

---

## Create Repository

### Create a new repository for your LINE bot:
```bash
# Navigate to your project folder
cd "C:\Users\Bright\Personal lINE\line-article-bot"

# Initialize git if not already done
git init

# Create repository on GitHub
gh repo create line-article-bot --public --source=. --remote=origin --push

# Or with description
gh repo create line-article-bot --public --description "LINE bot that saves articles to Google Sheets" --source=. --remote=origin --push
```

### Alternative: Interactive creation
```bash
gh repo create
```
Then follow the prompts:
- Repository name: line-article-bot
- Description: LINE bot that saves articles to Google Sheets
- Visibility: Public/Private
- Add a README: No (we already have one)
- Add .gitignore: No (we already have one)
- Choose license: MIT (optional)

---

## Common gh repo commands

### Create repository (various options):
```bash
# Create public repo
gh repo create my-repo --public

# Create private repo
gh repo create my-repo --private

# Create with description
gh repo create my-repo --public --description "My awesome project"

# Create and clone
gh repo create my-repo --public --clone

# Create from existing local folder
gh repo create my-repo --public --source=. --remote=origin

# Create and push existing code
gh repo create my-repo --public --source=. --remote=origin --push

# Create in an organization
gh repo create org-name/repo-name --public

# Create with specific .gitignore and license
gh repo create my-repo --public --gitignore Python --license MIT
```

### View repository:
```bash
# Open in browser
gh repo view --web

# View repo info
gh repo view

# View specific repo
gh repo view username/repo-name
```

### Clone repository:
```bash
gh repo clone username/repo-name
```

### Fork repository:
```bash
gh repo fork username/repo-name
```

### Delete repository:
```bash
gh repo delete username/repo-name --confirm
```

---

## Complete Setup for Your LINE Bot

### Step-by-step commands:
```bash
# 1. Install GitHub CLI (if not installed)
winget install --id GitHub.cli

# 2. Authenticate
gh auth login

# 3. Navigate to project
cd "C:\Users\Bright\Personal lINE\line-article-bot"

# 4. Initialize git
git init

# 5. Add all files
git add .

# 6. Initial commit
git commit -m "Initial commit: LINE article bot with Google Sheets integration"

# 7. Create and push to GitHub
gh repo create line-article-bot --public --description "LINE bot that saves articles to Google Sheets" --source=. --remote=origin --push

# 8. View your repo
gh repo view --web
```

---

## After Creating Repository

### Set up GitHub Actions (optional):
```bash
# Create workflow directory
mkdir -p .github/workflows

# You can then add CI/CD workflows for automated deployment
```

### Add collaborators:
```bash
gh repo add-collaborator username
```

### Create issues:
```bash
gh issue create --title "Setup LINE credentials" --body "Need to add LINE bot credentials"
```

### Create pull request:
```bash
gh pr create --title "Add new feature" --body "Description of changes"
```

---

## Quick Reference

```bash
# Check if gh is installed
gh --version

# Login status
gh auth status

# List your repos
gh repo list

# Create public repo with everything
gh repo create line-article-bot \
  --public \
  --description "LINE bot for saving articles to Google Sheets" \
  --source=. \
  --remote=origin \
  --push \
  --license MIT

# Open repo in browser
gh repo view --web
```

---

## Troubleshooting

### If 'gh' command not found:
1. Restart terminal after installation
2. Check PATH environment variable
3. Try full path: `"C:\Program Files\GitHub CLI\gh.exe"`

### If authentication fails:
```bash
# Try with token
gh auth login --with-token < token.txt

# Or browser authentication
gh auth login --web
```

### If push fails:
```bash
# Check remotes
git remote -v

# Set upstream
git push -u origin main
```