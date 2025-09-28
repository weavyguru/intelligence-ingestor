#!/bin/bash

# GitHub Push Script
# Usage: ./push_to_github.sh YOUR_GITHUB_USERNAME [REPO_NAME]

set -e

if [ $# -eq 0 ]; then
    echo "Please provide your GitHub username"
    echo "Usage: ./push_to_github.sh YOUR_GITHUB_USERNAME [REPO_NAME]"
    echo "Example: ./push_to_github.sh johndoe intelligence-ingestor"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME=${2:-intelligence-ingestor}

echo "Setting up GitHub repository..."
echo "Username: $GITHUB_USERNAME"
echo "Repository: $REPO_NAME"
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
fi

# Check if files are committed
if [ -z "$(git log --oneline 2>/dev/null)" ]; then
    echo "Committing files..."
    git add .
    git commit -m "Initial commit: Intelligence Ingestor with GitHub Actions Azure deployment"
fi

# Set up remote
echo "Setting up GitHub remote..."
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git

# Set main branch
git branch -M main

echo ""
echo "Repository configured for: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo ""
echo "Next steps:"
echo "1. Create the repository on GitHub: https://github.com/new"
echo "   - Repository name: $REPO_NAME"
echo "   - Description: Community intelligence data ingestion service for Chroma Cloud"
echo "   - Make it public or private as desired"
echo "   - Do NOT initialize with README (we have files already)"
echo ""
echo "2. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "3. If you get authentication errors, you may need to:"
echo "   - Set up a Personal Access Token: https://github.com/settings/tokens"
echo "   - Or use GitHub CLI: gh auth login"
echo ""

# Try to push (this might fail if repo doesn't exist or auth is needed)
echo "Attempting to push to GitHub..."
if git push -u origin main 2>/dev/null; then
    echo "✅ Successfully pushed to GitHub!"
    echo "🌐 Repository: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
else
    echo "⚠️  Push failed - you may need to:"
    echo "   1. Create the repository on GitHub first"
    echo "   2. Set up authentication (Personal Access Token or GitHub CLI)"
    echo "   3. Run: git push -u origin main"
fi

echo ""
echo "📋 Don't forget to set up GitHub secrets for deployment!"
echo "Run: python generate_tokens.py"