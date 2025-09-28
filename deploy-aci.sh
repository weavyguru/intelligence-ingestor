#!/bin/bash

# Azure Container Instances Deployment Script
# Usage: ./deploy-aci.sh

set -e

# Configuration
RESOURCE_GROUP="intelligence-ingestor-rg"
LOCATION="eastus"
CONTAINER_NAME="intelligence-ingestor"
IMAGE_NAME="intelligence-ingestor:latest"
ACR_NAME="intelligenceingestorregistry" # Must be globally unique
CONTAINER_INSTANCE_NAME="intelligence-ingestor-ci"

# Environment variables (you'll need to set these)
BEARER_TOKEN="your-bearer-token-here"
CHROMA_API_KEY="ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
CHROMA_TENANT="cc8a08d9-0db3-472d-bc29-7a2b7cddbc55"
CHROMA_DATABASE="weavy_community_intelligence"

echo "🚀 Starting Azure Container Instances deployment..."

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
echo "Registry server: $ACR_LOGIN_SERVER"

# Step 4: Build and push Docker image
echo "🔨 Building Docker image..."
az acr build \
    --registry $ACR_NAME \
    --image $IMAGE_NAME \
    .

# Step 5: Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

# Step 6: Deploy to Container Instances
echo "🚀 Deploying to Azure Container Instances..."
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_INSTANCE_NAME \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME \
    --registry-login-server $ACR_LOGIN_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --dns-name-label $CONTAINER_INSTANCE_NAME \
    --ports 8000 \
    --environment-variables \
        BEARER_TOKEN=$BEARER_TOKEN \
        CHROMA_API_KEY=$CHROMA_API_KEY \
        CHROMA_TENANT=$CHROMA_TENANT \
        CHROMA_DATABASE=$CHROMA_DATABASE \
    --cpu 1 \
    --memory 2

# Step 7: Get the public IP
echo "📋 Getting deployment info..."
FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_INSTANCE_NAME --query ipAddress.fqdn --output tsv)
PUBLIC_IP=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_INSTANCE_NAME --query ipAddress.ip --output tsv)

echo "✅ Deployment complete!"
echo "🌐 Your service is available at:"
echo "   FQDN: http://$FQDN:8000"
echo "   IP: http://$PUBLIC_IP:8000"
echo ""
echo "🔍 Health check: curl http://$FQDN:8000/health"
echo "📚 API docs: http://$FQDN:8000/docs"
echo ""
echo "📊 Monitor logs: az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_INSTANCE_NAME --follow"