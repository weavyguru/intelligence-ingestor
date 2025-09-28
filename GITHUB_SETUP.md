# GitHub Actions Azure Deployment Setup

This guide will walk you through setting up your intelligence ingestor project on GitHub with automated Azure deployment using GitHub Actions.

## 🚀 Quick Setup Steps

### 1. Create GitHub Repository

```bash
# Navigate to your project directory
cd /c/Projects/intelligence_ingestor

# Add all files to git
git add .
git commit -m "Initial commit: Intelligence Ingestor with Azure deployment"

# Create repository on GitHub (replace YOUR_USERNAME)
# Go to: https://github.com/new
# Repository name: intelligence-ingestor
# Description: Community intelligence data ingestion service for Chroma Cloud
# Public/Private: Choose based on your preference
# Don't initialize with README (we already have files)

# Add GitHub remote and push
git remote add origin https://github.com/YOUR_USERNAME/intelligence-ingestor.git
git branch -M main
git push -u origin main
```

### 2. Set Up Azure Service Principal

First, create an Azure Service Principal for GitHub Actions to authenticate with Azure:

```bash
# Login to Azure
az login

# Get your subscription ID
az account show --query id --output tsv

# Create service principal (replace SUBSCRIPTION_ID with your actual ID)
az ad sp create-for-rbac \
  --name "GitHubActions-IntelligenceIngestor" \
  --role contributor \
  --scopes /subscriptions/SUBSCRIPTION_ID \
  --sdk-auth

# Copy the entire JSON output - you'll need it for GitHub secrets
```

The output will look like this (save this JSON):
```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

### 3. Configure GitHub Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Click "New repository secret" and add these secrets:

#### Required Secrets:

1. **AZURE_CREDENTIALS**
   - Value: The entire JSON output from the service principal creation above

2. **BEARER_TOKEN_STAGING**
   - Value: Generate a secure token for staging environment
   - Run: `python -c "import secrets; print('staging_' + secrets.token_urlsafe(32))"`

3. **BEARER_TOKEN_PRODUCTION**
   - Value: Generate a secure token for production environment
   - Run: `python -c "import secrets; print('prod_' + secrets.token_urlsafe(32))"`

4. **CHROMA_API_KEY**
   - Value: `ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B`

5. **CHROMA_TENANT**
   - Value: `cc8a08d9-0db3-472d-bc29-7a2b7cddbc55`

6. **CHROMA_DATABASE**
   - Value: `weavy_community_intelligence`

### 4. Set Up Repository Environments

Go to your GitHub repository → Settings → Environments

Create two environments:

#### Staging Environment
- Name: `staging`
- Protection rules: None (for faster development)

#### Production Environment
- Name: `production`
- Protection rules:
  - ✅ Required reviewers (add yourself)
  - ✅ Wait timer: 5 minutes
  - ✅ Restrict pushes to protected branches (main)

## 🔄 Deployment Workflow

### Automatic Deployments

The GitHub Actions workflow will automatically deploy:

- **Staging**: When you push to `develop` branch
- **Production**: When you push to `main` branch

### Manual Deployments

You can also trigger deployments manually:

1. Go to your GitHub repository
2. Click "Actions" tab
3. Click "Deploy Intelligence Ingestor to Azure"
4. Click "Run workflow"
5. Choose environment (staging/production)

## 🌟 Workflow Features

### ✅ What the Workflow Does

1. **Tests**: Runs import tests to verify code integrity
2. **Build**: Creates Docker container and pushes to Azure Container Registry
3. **Deploy**: Deploys to Azure App Service with proper configuration
4. **Auto-scaling**: Sets up CPU-based auto-scaling for production
5. **Health Check**: Verifies deployment is working
6. **Test Ingest**: Performs a test data ingest to validate functionality

### 🏗️ Infrastructure Created

**Staging Environment:**
- Resource Group: `intelligence-ingestor-rg-staging`
- Container Registry: `intelligenceingestorstaging`
- App Service Plan: `intelligence-ingestor-app-plan-staging` (B1)
- Web App: `intelligence-ingestor-app-staging`

**Production Environment:**
- Resource Group: `intelligence-ingestor-rg`
- Container Registry: `intelligenceingestorregistry`
- App Service Plan: `intelligence-ingestor-app-plan` (S1)
- Web App: `intelligence-ingestor-app`
- Auto-scaling: 2-10 instances based on CPU usage

### 📊 Monitoring URLs

After deployment, your services will be available at:

- **Staging**: `https://intelligence-ingestor-app-staging.azurewebsites.net`
- **Production**: `https://intelligence-ingestor-app.azurewebsites.net`

Health checks:
- **Staging**: `https://intelligence-ingestor-app-staging.azurewebsites.net/health`
- **Production**: `https://intelligence-ingestor-app.azurewebsites.net/health`

API documentation:
- **Staging**: `https://intelligence-ingestor-app-staging.azurewebsites.net/docs`
- **Production**: `https://intelligence-ingestor-app.azurewebsites.net/docs`

## 🔧 Development Workflow

### Recommended Git Flow

1. **Feature Development**:
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -m "Add new feature"
   git push origin feature/new-feature
   # Create Pull Request to develop
   ```

2. **Staging Deployment**:
   ```bash
   git checkout develop
   git merge feature/new-feature
   git push origin develop
   # Automatic deployment to staging
   ```

3. **Production Deployment**:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   # Automatic deployment to production (with approval)
   ```

## 🚨 Troubleshooting

### Common Issues

1. **Service Principal Permissions**
   ```bash
   # If deployment fails, check service principal has contributor access
   az role assignment list --assignee YOUR_CLIENT_ID
   ```

2. **Container Registry Names**
   ```bash
   # ACR names must be globally unique. If deployment fails:
   # Edit .github/workflows/deploy-azure.yml
   # Change CONTAINER_REGISTRY to something unique
   ```

3. **App Service Names**
   ```bash
   # App Service names must be globally unique. If deployment fails:
   # Edit .github/workflows/deploy-azure.yml
   # Change AZURE_WEBAPP_NAME to something unique
   ```

### Monitoring Deployments

1. **GitHub Actions Logs**:
   - Go to Actions tab in your repository
   - Click on the workflow run to see detailed logs

2. **Azure Portal**:
   - Visit: https://portal.azure.com
   - Navigate to your resource group
   - Check App Service logs and metrics

3. **Application Logs**:
   ```bash
   # View live logs
   az webapp log tail \
     --name intelligence-ingestor-app \
     --resource-group intelligence-ingestor-rg
   ```

## 💰 Cost Estimates

### Staging Environment
- App Service Plan (B1): ~$13/month
- Container Registry (Basic): ~$5/month
- **Total**: ~$18/month

### Production Environment
- App Service Plan (S1): ~$73/month
- Container Registry (Standard): ~$20/month
- **Total**: ~$93/month

### Cost Optimization Tips

1. **Scale down staging when not in use**:
   ```bash
   # Stop staging app
   az webapp stop --name intelligence-ingestor-app-staging --resource-group intelligence-ingestor-rg-staging

   # Start staging app
   az webapp start --name intelligence-ingestor-app-staging --resource-group intelligence-ingestor-rg-staging
   ```

2. **Use deployment slots for production** (included in S1+ plans):
   - Deploy to staging slot first
   - Swap slots for zero-downtime deployments

## 🎯 Next Steps

1. **Set up monitoring alerts**
2. **Configure custom domains**
3. **Implement API rate limiting**
4. **Set up Application Insights**
5. **Configure backup strategies**

Ready to deploy? Follow the setup steps above and push your code to GitHub!