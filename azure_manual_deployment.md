# Manual Azure Deployment Guide

Since you can create web apps but not service principals, let's deploy manually through the Azure Portal first. This will create your foundation, and we can add automated CI/CD later.

## 🚀 Method 1: Azure Container Instances (Quickest)

### Step 1: Build and Push Docker Image

First, let's get your Docker image ready. You can either:

**Option A: Use Azure Cloud Shell (Recommended)**
1. Go to: https://shell.azure.com
2. Upload your project files or clone from GitHub:
   ```bash
   git clone https://github.com/weavyguru/intelligence-ingestor.git
   cd intelligence-ingestor
   ```

**Option B: Use Local Docker (if you have Docker Desktop)**
1. Build locally and push to a registry

### Step 2: Create Container Registry

1. **Go to Azure Portal**: https://portal.azure.com
2. **Click "Create a resource"**
3. **Search for "Container Registry"**
4. **Click "Create"**
5. **Fill in**:
   - **Subscription**: Your subscription
   - **Resource group**: Create new → `intelligence-ingestor-rg`
   - **Registry name**: `intelligenceingestor` (must be globally unique)
   - **Location**: East US
   - **SKU**: Basic
6. **Click "Review + create"** → **"Create"**

### Step 3: Build and Push Image (Azure Cloud Shell)

1. **Open Azure Cloud Shell**: https://shell.azure.com
2. **Clone your repository**:
   ```bash
   git clone https://github.com/weavyguru/intelligence-ingestor.git
   cd intelligence-ingestor
   ```
3. **Build and push to your registry**:
   ```bash
   # Login to your container registry
   az acr login --name intelligenceingestor

   # Build and push
   az acr build --registry intelligenceingestor --image intelligence-ingestor:latest .
   ```

### Step 4: Create Container Instance

1. **In Azure Portal**, click "Create a resource"
2. **Search for "Container Instances"**
3. **Click "Create"**
4. **Fill in Basics**:
   - **Subscription**: Your subscription
   - **Resource group**: `intelligence-ingestor-rg`
   - **Container name**: `intelligence-ingestor`
   - **Region**: East US
   - **Image source**: Azure Container Registry
   - **Registry**: `intelligenceingestor`
   - **Image**: `intelligence-ingestor`
   - **Image tag**: `latest`
5. **Click "Next: Networking"**
6. **Networking**:
   - **Networking type**: Public
   - **DNS name label**: `intelligence-ingestor-demo` (or your preferred name)
   - **Ports**: 8000 (TCP)
7. **Click "Next: Advanced"**
8. **Environment variables** (click "Add"):
   - `BEARER_TOKEN` = `staging_eICzX-Vtl3Nur3WzvXs8beiKFryhjr4fn1oxYA1ygq0`
   - `CHROMA_API_KEY` = `ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B`
   - `CHROMA_TENANT` = `cc8a08d9-0db3-472d-bc29-7a2b7cddbc55`
   - `CHROMA_DATABASE` = `weavy_community_intelligence`
9. **Click "Review + create"** → **"Create"**

## 🌐 Method 2: Azure App Service (More Features)

### Step 1: Create App Service Plan

1. **In Azure Portal**, click "Create a resource"
2. **Search for "App Service Plan"**
3. **Click "Create"**
4. **Fill in**:
   - **Subscription**: Your subscription
   - **Resource group**: Use existing → `intelligence-ingestor-rg`
   - **Name**: `intelligence-ingestor-plan`
   - **Operating System**: Linux
   - **Region**: East US
   - **Pricing Tier**: B1 Basic (or F1 Free for testing)
5. **Click "Review + create"** → **"Create"**

### Step 2: Create Web App

1. **Click "Create a resource"**
2. **Search for "Web App"**
3. **Click "Create"**
4. **Fill in**:
   - **Subscription**: Your subscription
   - **Resource group**: `intelligence-ingestor-rg`
   - **Name**: `intelligence-ingestor-app` (must be globally unique)
   - **Publish**: Container
   - **Operating System**: Linux
   - **Region**: East US
   - **App Service Plan**: `intelligence-ingestor-plan`
5. **Click "Next: Container"**
6. **Container settings**:
   - **Image Source**: Azure Container Registry
   - **Registry**: `intelligenceingestor`
   - **Image**: `intelligence-ingestor`
   - **Tag**: `latest`
7. **Click "Review + create"** → **"Create"**

### Step 3: Configure Environment Variables

1. **Go to your new Web App**
2. **Click "Configuration" in left menu**
3. **Click "New application setting"** for each:
   - `BEARER_TOKEN` = `staging_eICzX-Vtl3Nur3WzvXs8beiKFryhjr4fn1oxYA1ygq0`
   - `CHROMA_API_KEY` = `ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B`
   - `CHROMA_TENANT` = `cc8a08d9-0db3-472d-bc29-7a2b7cddbc55`
   - `CHROMA_DATABASE` = `weavy_community_intelligence`
   - `WEBSITES_PORT` = `8000`
4. **Click "Save"**

## 🧪 Testing Your Deployment

Once deployed, your service will be available at:

**Container Instances**: `http://intelligence-ingestor-demo.eastus.azurecontainer.io:8000`
**App Service**: `https://intelligence-ingestor-app.azurewebsites.net`

### Test Endpoints:

1. **Health Check**:
   ```
   GET /health
   ```

2. **API Documentation**:
   ```
   GET /docs
   ```

3. **Test Ingest**:
   ```bash
   curl -X POST "https://your-app-url/ingest?test=true" \
     -H "Authorization: Bearer staging_eICzX-Vtl3Nur3WzvXs8beiKFryhjr4fn1oxYA1ygq0" \
     -H "Content-Type: application/json" \
     -d '{
       "platform": "Manual",
       "source": "Azure",
       "id": "test123",
       "timestamp": "2024-01-15T10:30:00Z",
       "deeplink": "https://portal.azure.com",
       "author": "https://github.com/weavyguru",
       "title": "Manual Deployment Test",
       "body": "Testing manual Azure deployment",
       "isComment": false
     }'
   ```

## 🔄 Updating Your App

When you make code changes:

### Option 1: Rebuild in Cloud Shell
```bash
cd intelligence-ingestor
git pull origin main
az acr build --registry intelligenceingestor --image intelligence-ingestor:latest .
```

### Option 2: Manual Container Update
1. Go to your Container Instance/Web App
2. Click "Restart" to pull the latest image

## 🎯 Setting Up CI/CD Later

Once you get service principal permissions, you can:

1. **Add the service principal** to your existing resource group
2. **Update GitHub secrets** with Azure credentials
3. **GitHub Actions will automatically deploy** to your existing infrastructure

Your foundation will already be set up, so the CI/CD will just update the existing resources!

## 💰 Cost Estimates

**Container Instances**: ~$30/month for 1 vCPU, 2GB RAM
**App Service B1**: ~$55/month for 1 vCPU, 1.75GB RAM
**Container Registry**: ~$5/month for Basic tier

## 🔧 Troubleshooting

### Build Fails in Cloud Shell
- Make sure you're in the correct directory
- Check if the registry name is correct and unique
- Verify you have permissions to the container registry

### App Won't Start
- Check the container logs in Azure Portal
- Verify environment variables are set correctly
- Make sure WEBSITES_PORT is set to 8000 for App Service

### Can't Access the App
- Check if the container/app is running
- Verify the networking configuration
- Make sure port 8000 is exposed

**Start with Container Instances** - it's the quickest to get running!