#!/bin/bash

# Create Azure Service Principal for GitHub Actions
# This script handles the command substitution properly

set -e

echo "🚀 Creating Azure Service Principal for GitHub Actions..."

# Check if Azure CLI is available
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure
echo "🔐 Logging into Azure..."
az login

# Get subscription ID
echo "📋 Getting subscription information..."
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
SUBSCRIPTION_NAME=$(az account show --query name --output tsv)

echo "Using subscription:"
echo "  Name: $SUBSCRIPTION_NAME"
echo "  ID: $SUBSCRIPTION_ID"
echo ""

# Create service principal
echo "🔧 Creating service principal..."
SP_NAME="GitHubActions-IntelligenceIngestor"

# Create the service principal
SP_OUTPUT=$(az ad sp create-for-rbac \
  --name "$SP_NAME" \
  --role contributor \
  --scopes "/subscriptions/$SUBSCRIPTION_ID" \
  --output json)

echo "✅ Service principal created successfully!"
echo ""

# Extract values from the output
APP_ID=$(echo $SP_OUTPUT | jq -r '.appId')
PASSWORD=$(echo $SP_OUTPUT | jq -r '.password')
TENANT=$(echo $SP_OUTPUT | jq -r '.tenant')

# Format for GitHub Actions
echo "📋 GitHub Secret Configuration"
echo "=============================="
echo ""
echo "Secret Name: AZURE_CREDENTIALS"
echo "Secret Value:"
cat << EOF
{
  "clientId": "$APP_ID",
  "clientSecret": "$PASSWORD",
  "subscriptionId": "$SUBSCRIPTION_ID",
  "tenantId": "$TENANT"
}
EOF

echo ""
echo "🔗 Add this secret at:"
echo "   https://github.com/weavyguru/intelligence-ingestor/settings/secrets/actions"
echo ""

# Save to file
cat << EOF > azure-credentials.json
{
  "clientId": "$APP_ID",
  "clientSecret": "$PASSWORD",
  "subscriptionId": "$SUBSCRIPTION_ID",
  "tenantId": "$TENANT"
}
EOF

echo "💾 Credentials also saved to: azure-credentials.json"
echo "   (Delete this file after adding to GitHub secrets)"
echo ""

echo "🎯 Next steps:"
echo "   1. Copy the JSON above to GitHub secrets as AZURE_CREDENTIALS"
echo "   2. Add the other required secrets (run: python generate_tokens.py)"
echo "   3. Set up GitHub environments (staging and production)"
echo "   4. Test deployment from GitHub Actions"