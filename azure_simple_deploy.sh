#!/bin/bash

# Simple Azure Deployment Without Container Registry
# Run this in Azure Cloud Shell at https://shell.azure.com

set -e

echo "🚀 Deploying Intelligence Ingestor to Azure (Simple Method)..."

# Configuration
RESOURCE_GROUP="intelligence-ingestor-rg"
LOCATION="eastus"
APP_SERVICE_PLAN="intelligence-ingestor-plan"
WEB_APP_NAME="intelligence-ingestor-app-$(date +%s)"

# Environment variables
BEARER_TOKEN="staging_eICzX-Vtl3Nur3WzvXs8beiKFryhjr4fn1oxYA1ygq0"
CHROMA_API_KEY="ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
CHROMA_TENANT="cc8a08d9-0db3-472d-bc29-7a2b7cddbc55"
CHROMA_DATABASE="weavy_community_intelligence"

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Web App: $WEB_APP_NAME"
echo ""

# Step 1: Create Resource Group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Step 2: Create App Service Plan
echo "📋 Creating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --is-linux \
    --sku B1

# Step 3: Create Web App with Python runtime
echo "🌐 Creating Web App..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --name $WEB_APP_NAME \
    --runtime "PYTHON|3.11" \
    --deployment-source-url https://github.com/weavyguru/intelligence-ingestor.git \
    --deployment-source-branch main

# Step 4: Configure application settings
echo "⚙️ Configuring application settings..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --settings \
        BEARER_TOKEN="$BEARER_TOKEN" \
        CHROMA_API_KEY="$CHROMA_API_KEY" \
        CHROMA_TENANT="$CHROMA_TENANT" \
        CHROMA_DATABASE="$CHROMA_DATABASE" \
        SCM_DO_BUILD_DURING_DEPLOYMENT=true \
        ENABLE_ORYX_BUILD=true

# Step 5: Configure startup command
echo "🔧 Configuring startup command..."
az webapp config set \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --startup-file "python main.py"

# Get the final URL
APP_URL="https://$WEB_APP_NAME.azurewebsites.net"

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your service is available at: $APP_URL"
echo ""
echo "⏱️  Note: The app may take 5-10 minutes to fully start up as it installs dependencies."
echo ""
echo "🔍 Health check: curl $APP_URL/health"
echo "📚 API docs: $APP_URL/docs"
echo ""
echo "🧪 Test your deployment:"
echo "curl -X POST \"$APP_URL/ingest?test=true\" \\"
echo "  -H \"Authorization: Bearer $BEARER_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"platform\": \"Azure\", \"source\": \"Direct\", \"id\": \"test123\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"deeplink\": \"$APP_URL\", \"author\": \"https://github.com/weavyguru\", \"title\": \"Simple Deploy Test\", \"body\": \"Testing simple Azure deployment\", \"isComment\": false}'"
echo ""
echo "📊 Monitor logs: az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo "🔧 Manage in portal: https://portal.azure.com"