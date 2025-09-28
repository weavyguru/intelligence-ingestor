#!/bin/bash

# GitHub Repository Setup Script
# Usage: ./setup_github.sh YOUR_GITHUB_USERNAME

set -e

if [ $# -eq 0 ]; then
    echo "❌ Please provide your GitHub username"
    echo "Usage: ./setup_github.sh YOUR_GITHUB_USERNAME"
    echo "Example: ./setup_github.sh johndoe"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="intelligence-ingestor"

echo "🚀 Setting up GitHub repository for Intelligence Ingestor..."
echo "GitHub Username: $GITHUB_USERNAME"
echo "Repository Name: $REPO_NAME"
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
fi

echo "📝 Generating secure tokens..."
python generate_tokens.py

echo ""
echo "📋 Next steps:"
echo "1. Create a new repository on GitHub:"
echo "   https://github.com/new"
echo "   Repository name: $REPO_NAME"
echo "   Description: Community intelligence data ingestion service for Chroma Cloud"
echo ""

echo "2. Run these commands to push your code:"
echo "   git add ."
echo "   git commit -m 'Initial commit: Intelligence Ingestor with Azure deployment'"
echo "   git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""

echo "3. Create Azure Service Principal:"
echo "   az login"
echo "   SUBSCRIPTION_ID=\$(az account show --query id --output tsv)"
echo "   az ad sp create-for-rbac --name 'GitHubActions-IntelligenceIngestor' --role contributor --scopes /subscriptions/\$SUBSCRIPTION_ID --sdk-auth"
echo ""

echo "4. Set up GitHub repository secrets:"
echo "   Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/secrets/actions"
echo "   Add the secrets shown above"
echo ""

echo "5. Set up GitHub environments:"
echo "   Go to: https://github.com/$GITHUB_USERNAME/$REPO_NAME/settings/environments"
echo "   Create 'staging' and 'production' environments"
echo ""

echo "📚 For detailed instructions, see: GITHUB_SETUP.md"
echo "✅ Setup script complete!"