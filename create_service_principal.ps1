# Create Azure Service Principal for GitHub Actions
# Run this in PowerShell with Azure CLI installed

Write-Host "Creating Azure Service Principal for GitHub Actions..." -ForegroundColor Green

# Check if Azure CLI is installed
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✅ Azure CLI version: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI not found. Please install it first:" -ForegroundColor Red
    Write-Host "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Login to Azure
Write-Host "🔐 Logging into Azure..." -ForegroundColor Yellow
az login

# Get subscription info
$subscription = az account show --output json | ConvertFrom-Json
$subscriptionId = $subscription.id
$subscriptionName = $subscription.name

Write-Host "📋 Using subscription:" -ForegroundColor Cyan
Write-Host "   Name: $subscriptionName" -ForegroundColor White
Write-Host "   ID: $subscriptionId" -ForegroundColor White
Write-Host ""

# Create service principal
Write-Host "🔧 Creating service principal..." -ForegroundColor Yellow
$spName = "GitHubActions-IntelligenceIngestor"

try {
    $spOutput = az ad sp create-for-rbac --name $spName --role contributor --scopes "/subscriptions/$subscriptionId" --output json
    $sp = $spOutput | ConvertFrom-Json

    Write-Host "✅ Service principal created successfully!" -ForegroundColor Green
    Write-Host ""

    # Format for GitHub Actions
    $githubCredentials = @{
        clientId = $sp.appId
        clientSecret = $sp.password
        subscriptionId = $subscriptionId
        tenantId = $sp.tenant
    } | ConvertTo-Json -Depth 3

    Write-Host "📋 GitHub Secret Configuration" -ForegroundColor Cyan
    Write-Host "==============================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Secret Name: AZURE_CREDENTIALS" -ForegroundColor Yellow
    Write-Host "Secret Value:" -ForegroundColor Yellow
    Write-Host $githubCredentials -ForegroundColor White
    Write-Host ""
    Write-Host "🔗 Add this secret at:" -ForegroundColor Cyan
    Write-Host "   https://github.com/weavyguru/intelligence-ingestor/settings/secrets/actions" -ForegroundColor Blue
    Write-Host ""

    # Save to file
    $githubCredentials | Out-File -FilePath "azure-credentials.json" -Encoding UTF8
    Write-Host "💾 Credentials also saved to: azure-credentials.json" -ForegroundColor Green
    Write-Host "   (Delete this file after adding to GitHub secrets)" -ForegroundColor Yellow

} catch {
    Write-Host "❌ Failed to create service principal:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "   1. Make sure you have sufficient permissions in Azure" -ForegroundColor White
    Write-Host "   2. Try a different service principal name" -ForegroundColor White
    Write-Host "   3. Check if the service principal already exists" -ForegroundColor White
}

Write-Host ""
Write-Host "🎯 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Copy the JSON above to GitHub secrets as AZURE_CREDENTIALS" -ForegroundColor White
Write-Host "   2. Add the other required secrets (run: python generate_tokens.py)" -ForegroundColor White
Write-Host "   3. Set up GitHub environments (staging and production)" -ForegroundColor White
Write-Host "   4. Test deployment from GitHub Actions" -ForegroundColor White