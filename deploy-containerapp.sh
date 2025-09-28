#!/bin/bash

# Azure Container Apps Deployment Script
# Usage: ./deploy-containerapp.sh

set -e

# Configuration
RESOURCE_GROUP="intelligence-ingestor-rg"
LOCATION="eastus"
CONTAINER_APP_ENV="intelligence-ingestor-env"
CONTAINER_APP_NAME="intelligence-ingestor-ca"
ACR_NAME="intelligenceingestorregistry"

# Environment variables
BEARER_TOKEN="your-bearer-token-here"
CHROMA_API_KEY="ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
CHROMA_TENANT="cc8a08d9-0db3-472d-bc29-7a2b7cddbc55"
CHROMA_DATABASE="weavy_community_intelligence"

echo "🚀 Starting Azure Container Apps deployment..."

# Step 1: Install Container Apps extension
echo "🔧 Installing Azure Container Apps extension..."
az extension add --name containerapp --upgrade

# Step 2: Register providers
echo "📋 Registering Azure providers..."
az provider register --namespace Microsoft.App
az provider register --namespace Microsoft.OperationalInsights

# Step 3: Create Resource Group
echo "📦 Creating resource group..."
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION

# Step 4: Create Azure Container Registry
echo "🐳 Creating Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true

# Step 5: Build and push Docker image
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
echo "🔨 Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image intelligence-ingestor:latest \
    .

# Step 6: Create Container Apps Environment
echo "🌐 Creating Container Apps Environment..."
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION

# Step 7: Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Step 8: Create Container App
echo "🚀 Creating Container App..."
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $ACR_LOGIN_SERVER/intelligence-ingestor:latest \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --target-port 8000 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 10 \
    --cpu 1.0 \
    --memory 2.0Gi \
    --env-vars \
        BEARER_TOKEN="$BEARER_TOKEN" \
        CHROMA_API_KEY="$CHROMA_API_KEY" \
        CHROMA_TENANT="$CHROMA_TENANT" \
        CHROMA_DATABASE="$CHROMA_DATABASE"

# Step 9: Get the app URL
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo "✅ Deployment complete!"
echo "🌐 Your service is available at: https://$APP_URL"
echo "🔍 Health check: curl https://$APP_URL/health"
echo "📚 API docs: https://$APP_URL/docs"
echo ""
echo "📊 Monitor logs: az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --follow"
echo "🔧 Manage app: https://portal.azure.com"