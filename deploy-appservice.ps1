# Azure App Service Deployment Script (PowerShell)
# Usage: .\deploy-appservice.ps1

# Configuration
$ResourceGroup = "intelligence-ingestor-rg"
$Location = "eastus"
$AppServicePlan = "intelligence-ingestor-plan"
$WebAppName = "intelligence-ingestor-app-$(Get-Date -Format 'yyyyMMddHHmmss')"
$ACRName = "intelligenceingestorregistry$(Get-Random -Maximum 9999)"

# Environment variables - CHANGE THESE
$BearerToken = "your-bearer-token-here"  # Generate a secure token
$ChromaApiKey = "ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B"
$ChromaTenant = "cc8a08d9-0db3-472d-bc29-7a2b7cddbc55"
$ChromaDatabase = "weavy_community_intelligence"

Write-Host "🚀 Starting Azure App Service deployment..." -ForegroundColor Green

# Step 1: Create Resource Group
Write-Host "📦 Creating resource group..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location

# Step 2: Create Azure Container Registry
Write-Host "🐳 Creating Azure Container Registry..." -ForegroundColor Yellow
az acr create --resource-group $ResourceGroup --name $ACRName --sku Basic --admin-enabled true

# Step 3: Get ACR login server
$ACRLoginServer = az acr show --name $ACRName --query loginServer --output tsv

# Step 4: Build and push Docker image
Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
az acr build --registry $ACRName --image intelligence-ingestor:latest .

# Step 5: Create App Service Plan
Write-Host "📋 Creating App Service Plan..." -ForegroundColor Yellow
az appservice plan create --name $AppServicePlan --resource-group $ResourceGroup --is-linux --sku B1

# Step 6: Create Web App
Write-Host "🌐 Creating Web App..." -ForegroundColor Yellow
az webapp create --resource-group $ResourceGroup --plan $AppServicePlan --name $WebAppName --deployment-container-image-name "$ACRLoginServer/intelligence-ingestor:latest"

# Step 7: Configure container registry
Write-Host "🔐 Configuring container registry..." -ForegroundColor Yellow
$ACRUsername = az acr credential show --name $ACRName --query username --output tsv
$ACRPassword = az acr credential show --name $ACRName --query passwords[0].value --output tsv

az webapp config container set --name $WebAppName --resource-group $ResourceGroup --docker-custom-image-name "$ACRLoginServer/intelligence-ingestor:latest" --docker-registry-server-url "https://$ACRLoginServer" --docker-registry-server-user $ACRUsername --docker-registry-server-password $ACRPassword

# Step 8: Configure application settings
Write-Host "⚙️ Configuring application settings..." -ForegroundColor Yellow
az webapp config appsettings set --resource-group $ResourceGroup --name $WebAppName --settings BEARER_TOKEN="$BearerToken" CHROMA_API_KEY="$ChromaApiKey" CHROMA_TENANT="$ChromaTenant" CHROMA_DATABASE="$ChromaDatabase" WEBSITES_PORT=8000

# Step 9: Enable continuous deployment
Write-Host "🔄 Enabling continuous deployment..." -ForegroundColor Yellow
az webapp deployment container config --name $WebAppName --resource-group $ResourceGroup --enable-cd true

$AppUrl = "https://$WebAppName.azurewebsites.net"

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "🌐 Your service is available at: $AppUrl" -ForegroundColor Cyan
Write-Host "🔍 Health check: curl $AppUrl/health" -ForegroundColor White
Write-Host "📚 API docs: $AppUrl/docs" -ForegroundColor White
Write-Host ""
Write-Host "📊 Monitor logs: az webapp log tail --name $WebAppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host "🔧 Manage app: https://portal.azure.com" -ForegroundColor White

# Test the deployment
Write-Host "🧪 Testing deployment..." -ForegroundColor Yellow
Start-Sleep -Seconds 30  # Wait for app to start
try {
    $HealthResponse = Invoke-RestMethod -Uri "$AppUrl/health" -Method Get
    Write-Host "✅ Health check passed: $($HealthResponse | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Health check failed - app may still be starting up" -ForegroundColor Yellow
    Write-Host "Check logs: az webapp log tail --name $WebAppName --resource-group $ResourceGroup" -ForegroundColor White
}