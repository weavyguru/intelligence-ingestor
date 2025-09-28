# Azure Deployment Guide for Intelligence Ingestor

This guide provides step-by-step instructions for deploying the Intelligence Ingestor middleware to Azure using three different approaches.

## 🚀 Quick Start

### Prerequisites

1. **Azure CLI** installed and logged in:
   ```bash
   az login
   az account set --subscription "Your-Subscription-Name"
   ```

2. **Docker** installed (for local testing)

3. **Chroma Cloud credentials** (already configured in your `.env`)

### 🎯 Recommended: Azure App Service

For most production workloads, we recommend Azure App Service:

```bash
# Make the script executable
chmod +x deploy-appservice.sh

# Edit the script to set your bearer token
nano deploy-appservice.sh
# Change: BEARER_TOKEN="your-bearer-token-here"
# To: BEARER_TOKEN="your-actual-secure-token"

# Deploy
./deploy-appservice.sh
```

---

## 📋 Detailed Deployment Options

### Option 1: Azure Container Instances (ACI)
**Best for:** Quick testing, low traffic, simple deployments

**Pros:**
- Fastest to deploy
- Pay-per-second billing
- No infrastructure management

**Cons:**
- No auto-scaling
- No SSL termination
- Single container instance

**Steps:**
1. Edit `deploy-aci.sh` and set your `BEARER_TOKEN`
2. Run: `chmod +x deploy-aci.sh && ./deploy-aci.sh`
3. Access your service at the provided FQDN

**Cost:** ~$30/month for 1 vCPU, 2GB RAM

---

### Option 2: Azure App Service (Recommended)
**Best for:** Production workloads, auto-scaling, integrated monitoring

**Pros:**
- Auto-scaling
- SSL certificates
- Deployment slots
- Application Insights integration
- Custom domains

**Cons:**
- Slightly more complex setup
- Higher cost for larger instances

**Steps:**
1. Edit `deploy-appservice.sh` and set your `BEARER_TOKEN`
2. Run: `chmod +x deploy-appservice.sh && ./deploy-appservice.sh`
3. Configure custom domain (optional)
4. Set up Application Insights monitoring

**Cost:** ~$55/month for B1 plan (1 vCPU, 1.75GB RAM)

---

### Option 3: Azure Container Apps (Modern)
**Best for:** Microservices, event-driven, serverless scaling

**Pros:**
- True serverless (scale to zero)
- Automatic HTTPS
- Built-in load balancing
- Event-driven scaling

**Cons:**
- Newer service (less mature)
- More complex for simple use cases

**Steps:**
1. Edit `deploy-containerapp.sh` and set your `BEARER_TOKEN`
2. Run: `chmod +x deploy-containerapp.sh && ./deploy-containerapp.sh`
3. Configure scaling rules as needed

**Cost:** Pay-per-use, ~$0.0024/vCPU-hour when running

---

## 🔧 Configuration

### Environment Variables
All deployment options require these environment variables:

```bash
BEARER_TOKEN="your-secure-bearer-token"           # Generate a strong token
CHROMA_API_KEY="ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
CHROMA_TENANT="cc8a08d9-0db3-472d-bc29-7a2b7cddbc55"
CHROMA_DATABASE="weavy_community_intelligence"
```

### Generating a Secure Bearer Token
```bash
# Generate a secure random token
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🛡️ Security Considerations

### 1. Network Security
```bash
# Create a Virtual Network (for App Service/Container Apps)
az network vnet create \
    --resource-group intelligence-ingestor-rg \
    --name intelligence-ingestor-vnet \
    --address-prefix 10.0.0.0/16 \
    --subnet-name default \
    --subnet-prefix 10.0.1.0/24
```

### 2. Key Vault Integration
```bash
# Create Key Vault
az keyvault create \
    --name intelligence-ingestor-kv \
    --resource-group intelligence-ingestor-rg \
    --location eastus

# Store secrets
az keyvault secret set \
    --vault-name intelligence-ingestor-kv \
    --name bearer-token \
    --value "your-secure-token"

az keyvault secret set \
    --vault-name intelligence-ingestor-kv \
    --name chroma-api-key \
    --value "ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
```

### 3. Managed Identity
```bash
# Enable system-assigned managed identity (App Service)
az webapp identity assign \
    --name your-app-name \
    --resource-group intelligence-ingestor-rg

# Grant Key Vault access
az keyvault set-policy \
    --name intelligence-ingestor-kv \
    --object-id $(az webapp identity show --name your-app-name --resource-group intelligence-ingestor-rg --query principalId --output tsv) \
    --secret-permissions get
```

---

## 📊 Monitoring & Logging

### Application Insights
```bash
# Create Application Insights
az monitor app-insights component create \
    --app intelligence-ingestor-insights \
    --location eastus \
    --resource-group intelligence-ingestor-rg

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
    --app intelligence-ingestor-insights \
    --resource-group intelligence-ingestor-rg \
    --query instrumentationKey \
    --output tsv)

# Configure app setting
az webapp config appsettings set \
    --resource-group intelligence-ingestor-rg \
    --name your-app-name \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

### Log Analytics
```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
    --resource-group intelligence-ingestor-rg \
    --workspace-name intelligence-ingestor-logs
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Build and push to ACR
      run: |
        az acr build \
          --registry intelligenceingestorregistry \
          --image intelligence-ingestor:${{ github.sha }} \
          .

    - name: Deploy to App Service
      run: |
        az webapp config container set \
          --name your-app-name \
          --resource-group intelligence-ingestor-rg \
          --docker-custom-image-name intelligenceingestorregistry.azurecr.io/intelligence-ingestor:${{ github.sha }}
```

---

## 🧪 Testing Your Deployment

### Health Check
```bash
curl https://your-app-url.azurewebsites.net/health
```

### Test Ingest
```bash
curl -X POST "https://your-app-url.azurewebsites.net/ingest?test=true" \
  -H "Authorization: Bearer your-bearer-token" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "Lovable",
    "source": "Reddit",
    "id": "test123",
    "timestamp": "2024-01-15T10:30:00Z",
    "deeplink": "https://reddit.com/r/programming/comments/test123",
    "author": "https://reddit.com/u/testuser",
    "title": "Test Post",
    "body": "This is a test post for Azure deployment",
    "isComment": false
  }'
```

---

## 💰 Cost Optimization

### 1. Auto-scaling Rules
```bash
# Scale based on CPU usage
az monitor autoscale rule create \
    --resource-group intelligence-ingestor-rg \
    --autoscale-name intelligence-ingestor-autoscale \
    --condition "Percentage CPU > 70 avg 5m" \
    --scale out 1

# Scale based on HTTP queue length
az monitor autoscale rule create \
    --resource-group intelligence-ingestor-rg \
    --autoscale-name intelligence-ingestor-autoscale \
    --condition "Http Queue Length > 100 avg 5m" \
    --scale out 2
```

### 2. Deployment Slots (App Service)
```bash
# Create staging slot
az webapp deployment slot create \
    --name your-app-name \
    --resource-group intelligence-ingestor-rg \
    --slot staging

# Deploy to staging first, then swap
az webapp deployment slot swap \
    --name your-app-name \
    --resource-group intelligence-ingestor-rg \
    --slot staging \
    --target-slot production
```

---

## 🚨 Troubleshooting

### Common Issues

1. **Container startup failures**
   ```bash
   # Check logs
   az webapp log tail --name your-app-name --resource-group intelligence-ingestor-rg
   ```

2. **Authentication errors**
   ```bash
   # Verify ACR credentials
   az acr credential show --name intelligenceingestorregistry
   ```

3. **Environment variable issues**
   ```bash
   # List all app settings
   az webapp config appsettings list --name your-app-name --resource-group intelligence-ingestor-rg
   ```

### Performance Monitoring
```bash
# View metrics
az monitor metrics list \
    --resource /subscriptions/your-subscription/resourceGroups/intelligence-ingestor-rg/providers/Microsoft.Web/sites/your-app-name \
    --metric "CpuPercentage" \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-01T23:59:59Z
```

---

## 🎯 Next Steps

1. **Set up monitoring alerts**
2. **Configure backup strategies**
3. **Implement blue-green deployments**
4. **Set up API rate limiting**
5. **Configure custom domains and SSL**

Choose the deployment option that best fits your needs and follow the corresponding script. All options include monitoring, logging, and security best practices for production use.