# Getting Started - Manual Azure Deployment

Since you can create Azure resources but not service principals, let's get your intelligence ingestor running manually first. We can add automated CI/CD later when you get the right permissions.

## 🎯 Quick Start (Recommended)

### Option 1: One-Click Deploy with Azure Cloud Shell

This is the fastest way to get up and running:

1. **Open Azure Cloud Shell**: https://shell.azure.com
2. **Run the deployment script**:
   ```bash
   curl -s https://raw.githubusercontent.com/weavyguru/intelligence-ingestor/main/azure_cloud_shell_deploy.sh | bash
   ```

That's it! The script will:
- Create resource group
- Create container registry
- Build your Docker image
- Deploy to App Service
- Configure all environment variables

### Option 2: Manual Steps (If you prefer control)

Follow the detailed guide in: `azure_manual_deployment.md`

## 🚀 What You'll Get

After deployment, you'll have:

- **Azure App Service** running your intelligence ingestor
- **Container Registry** with your Docker image
- **Public URL** for your API (e.g., `https://intelligence-ingestor-app-123.azurewebsites.net`)
- **Automatic scaling** and monitoring through Azure

## 🧪 Testing Your Deployment

Once deployed, test with:

### Health Check
```bash
curl https://your-app-url.azurewebsites.net/health
```

### API Documentation
Visit: `https://your-app-url.azurewebsites.net/docs`

### Test Ingest
```bash
curl -X POST "https://your-app-url.azurewebsites.net/ingest?test=true" \
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

## 🔄 Making Updates

When you make code changes:

1. **Push to GitHub** (your repository is already set up)
2. **Rebuild in Azure Cloud Shell**:
   ```bash
   cd intelligence-ingestor
   git pull origin main
   az acr build --registry your-registry-name --image intelligence-ingestor:latest .
   ```
3. **Restart your app** in Azure Portal to pick up the new image

## 🎯 Adding CI/CD Later

Once you get service principal permissions:

1. Your infrastructure is already created ✅
2. Just add the GitHub secrets for Azure credentials
3. GitHub Actions will automatically deploy to your existing setup

No need to recreate anything - the foundation is already there!

## 💰 Cost

**Expected monthly cost**: ~$60-80
- App Service B1: ~$55/month
- Container Registry: ~$5/month
- Minimal data transfer costs

## 📚 Additional Resources

- **Manual deployment guide**: `azure_manual_deployment.md`
- **Cloud Shell script**: `azure_cloud_shell_deploy.sh`
- **GitHub Actions setup** (for later): `GITHUB_SETUP.md`

## 🆘 Need Help?

If you run into issues:

1. **Check the deployment logs** in Azure Portal
2. **View container logs** in your App Service
3. **Test locally first** with `python main.py`
4. **Verify environment variables** are set correctly

**Start with the Cloud Shell approach** - it handles all the complexity for you!