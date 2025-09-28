#!/bin/bash

# Azure Cloud Shell Deployment Script
# Run this in Azure Cloud Shell at https://shell.azure.com

set -e

echo "🚀 Deploying Intelligence Ingestor to Azure..."

# Configuration
RESOURCE_GROUP="intelligence-ingestor-rg"
LOCATION="eastus"
ACR_NAME="intelligenceingestor$(date +%s)"  # Add timestamp for uniqueness
CONTAINER_NAME="intelligence-ingestor"
APP_SERVICE_PLAN="intelligence-ingestor-plan"
WEB_APP_NAME="intelligence-ingestor-app-$(date +%s)"

# Environment variables
BEARER_TOKEN="staging_eICzX-Vtl3Nur3WzvXs8beiKFryhjr4fn1oxYA1ygq0"
CHROMA_API_KEY="ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
CHROMA_TENANT="cc8a08d9-0db3-472d-bc29-7a2b7cddbc55"
CHROMA_DATABASE="weavy_community_intelligence"

echo "📋 Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Container Registry: $ACR_NAME"
echo "  Web App: $WEB_APP_NAME"
echo ""

# Step 1: Create Resource Group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Step 2: Create Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Step 3: Clone repository (if not already done)
if [ ! -d "intelligence-ingestor" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/weavyguru/intelligence-ingestor.git
fi

# Step 4: Build and push Docker image
echo "🔨 Building and pushing Docker image..."
cd intelligence-ingestor

# Build and push to ACR
az acr build --registry $ACR_NAME --image intelligence-ingestor:latest .

# Step 5: Create App Service Plan
echo "📋 Creating App Service Plan..."
az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --is-linux \
    --sku B1

# Step 6: Create Web App
echo "🌐 Creating Web App..."
az webapp create \
    --resource-group $RESOURCE_GROUP \
    --plan $APP_SERVICE_PLAN \
    --name $WEB_APP_NAME \
    --deployment-container-image-name $ACR_NAME.azurecr.io/intelligence-ingestor:latest

# Step 7: Configure container registry credentials
echo "🔐 Configuring container registry..."
az webapp config container set \
    --name $WEB_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_NAME.azurecr.io/intelligence-ingestor:latest \
    --docker-registry-server-url https://$ACR_NAME.azurecr.io \
    --docker-registry-server-user $(az acr credential show --name $ACR_NAME --query username --output tsv) \
    --docker-registry-server-password $(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Step 8: Configure application settings
echo "⚙️ Configuring application settings..."
az webapp config appsettings set \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --settings \
        BEARER_TOKEN="$BEARER_TOKEN" \
        CHROMA_API_KEY="$CHROMA_API_KEY" \
        CHROMA_TENANT="$CHROMA_TENANT" \
        CHROMA_DATABASE="$CHROMA_DATABASE" \
        WEBSITES_PORT=8000

# Get the app URL
APP_URL="https://$WEB_APP_NAME.azurewebsites.net"

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your service is available at: $APP_URL"
echo "🔍 Health check: curl $APP_URL/health"
echo "📚 API docs: $APP_URL/docs"
echo ""
echo "🧪 Test your deployment:"
echo "curl -X POST \"$APP_URL/ingest?test=true\" \\"
echo "  -H \"Authorization: Bearer $BEARER_TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"platform\": \"Azure\", \"source\": \"Manual\", \"id\": \"test123\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"deeplink\": \"$APP_URL\", \"author\": \"https://github.com/weavyguru\", \"title\": \"Manual Test\", \"body\": \"Testing manual Azure deployment\", \"isComment\": false}'"
echo ""
echo "📊 Monitor logs: az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo "🔧 Manage in portal: https://portal.azure.com"