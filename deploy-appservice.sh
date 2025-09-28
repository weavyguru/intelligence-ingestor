#!/bin/bash

# Azure App Service Deployment Script
# Usage: ./deploy-appservice.sh

set -e

# Configuration
RESOURCE_GROUP="intelligence-ingestor-rg"
LOCATION="eastus"
APP_SERVICE_PLAN="intelligence-ingestor-plan"
WEB_APP_NAME="intelligence-ingestor-app-$(date +%s)" # Unique name
ACR_NAME="intelligenceingestorregistry" # Must be globally unique

# Environment variables
BEARER_TOKEN="your-bearer-token-here"
CHROMA_API_KEY="ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
CHROMA_TENANT="cc8a08d9-0db3-472d-bc29-7a2b7cddbc55"
CHROMA_DATABASE="weavy_community_intelligence"

echo "🚀 Starting Azure App Service deployment..."

# Step 1: Create Resource Group
echo "📦 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# Step 2: Create Azure Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Step 3: Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)

# Step 4: Build and push Docker image
echo "🔨 Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image intelligence-ingestor:latest \
    .

# Step 5: Create App Service Plan (Linux)
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
    --deployment-container-image-name $ACR_LOGIN_SERVER/intelligence-ingestor:latest

# Step 7: Configure container registry credentials
echo "🔐 Configuring container registry..."
az webapp config container set \
    --name $WEB_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --docker-custom-image-name $ACR_LOGIN_SERVER/intelligence-ingestor:latest \
    --docker-registry-server-url https://$ACR_LOGIN_SERVER \
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

# Step 9: Enable continuous deployment
echo "🔄 Enabling continuous deployment..."
az webapp deployment container config \
    --name $WEB_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --enable-cd true

# Step 10: Configure auto-scaling (optional)
echo "📈 Configuring auto-scaling..."
az monitor autoscale create \
    --resource-group $RESOURCE_GROUP \
    --resource $WEB_APP_NAME \
    --resource-type Microsoft.Web/sites \
    --name intelligence-ingestor-autoscale \
    --min-count 1 \
    --max-count 5 \
    --count 1

az monitor autoscale rule create \
    --resource-group $RESOURCE_GROUP \
    --autoscale-name intelligence-ingestor-autoscale \
    --condition "Percentage CPU > 70 avg 5m" \
    --scale out 1

az monitor autoscale rule create \
    --resource-group $RESOURCE_GROUP \
    --autoscale-name intelligence-ingestor-autoscale \
    --condition "Percentage CPU < 30 avg 5m" \
    --scale in 1

# Get the app URL
APP_URL="https://$WEB_APP_NAME.azurewebsites.net"

echo "✅ Deployment complete!"
echo "🌐 Your service is available at: $APP_URL"
echo "🔍 Health check: curl $APP_URL/health"
echo "📚 API docs: $APP_URL/docs"
echo ""
echo "📊 Monitor logs: az webapp log tail --name $WEB_APP_NAME --resource-group $RESOURCE_GROUP"
echo "🔧 Manage app: https://portal.azure.com"