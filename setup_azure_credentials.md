# Azure Service Principal Setup for GitHub Actions

The `--sdk-auth` flag has been deprecated in newer versions of Azure CLI. Here's the updated process:

## Method 1: Using Azure CLI (Recommended)

### Step 1: Create Service Principal

```bash
# Login to Azure
az login

# Get your subscription ID
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
echo "Subscription ID: $SUBSCRIPTION_ID"

# Create service principal
az ad sp create-for-rbac \
  --name "GitHubActions-IntelligenceIngestor" \
  --role contributor \
  --scopes /subscriptions/$SUBSCRIPTION_ID
```

This will output something like:
```json
{
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "displayName": "GitHubActions-IntelligenceIngestor",
  "password": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Step 2: Format for GitHub Actions

Take the output from above and format it like this for the **AZURE_CREDENTIALS** secret:

```json
{
  "clientId": "YOUR_APP_ID_FROM_ABOVE",
  "clientSecret": "YOUR_PASSWORD_FROM_ABOVE",
  "subscriptionId": "YOUR_SUBSCRIPTION_ID",
  "tenantId": "YOUR_TENANT_FROM_ABOVE"
}
```

**Example:**
```json
{
  "clientId": "12345678-1234-1234-1234-123456789012",
  "clientSecret": "abcdefghijklmnopqrstuvwxyz123456789",
  "subscriptionId": "87654321-4321-4321-4321-210987654321",
  "tenantId": "11111111-2222-3333-4444-555555555555"
}
```

### Step 3: Add to GitHub Secrets

1. Go to: https://github.com/weavyguru/intelligence-ingestor/settings/secrets/actions
2. Click "New repository secret"
3. Name: `AZURE_CREDENTIALS`
4. Value: The JSON from Step 2 (copy the entire JSON block)

## Method 2: Using Azure Portal (Alternative)

If Azure CLI isn't working, you can create the service principal through the Azure Portal:

### Step 1: Create App Registration
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "App registrations"
3. Click "New registration"
4. Name: "GitHubActions-IntelligenceIngestor"
5. Click "Register"

### Step 2: Create Client Secret
1. In your new app registration, go to "Certificates & secrets"
2. Click "New client secret"
3. Description: "GitHub Actions Secret"
4. Expires: 24 months
5. Click "Add"
6. **Copy the secret value immediately** (you won't see it again)

### Step 3: Assign Role
1. Go to "Subscriptions" in Azure Portal
2. Select your subscription
3. Go to "Access control (IAM)"
4. Click "Add" → "Add role assignment"
5. Role: "Contributor"
6. Assign access to: "User, group, or service principal"
7. Select your app: "GitHubActions-IntelligenceIngestor"
8. Click "Save"

### Step 4: Get Values
Collect these values:
- **clientId**: Application (client) ID from the app registration overview
- **clientSecret**: The secret value you copied
- **subscriptionId**: Your Azure subscription ID
- **tenantId**: Directory (tenant) ID from the app registration overview

Format as JSON like in Method 1, Step 2.

## Method 3: Using GitHub CLI with Azure Extension

If you have GitHub CLI and want to automate this:

```bash
# Install Azure CLI extension for GitHub
gh extension install github/gh-azure

# Create and configure the service principal
gh azure create-service-principal \
  --name GitHubActions-IntelligenceIngestor \
  --role contributor \
  --repo weavyguru/intelligence-ingestor
```

## Troubleshooting

### Error: "Insufficient privileges"
- Make sure your Azure account has permission to create service principals
- Try using an account with Owner or User Access Administrator role

### Error: "Application already exists"
- The service principal name must be unique
- Try adding a timestamp: `GitHubActions-IntelligenceIngestor-$(date +%s)`

### Error: "--sdk-auth was unexpected"
- You're using the old Azure CLI syntax
- Use the methods above instead

## Testing Your Setup

Once you've added the AZURE_CREDENTIALS secret to GitHub, you can test it by:

1. Going to your repository's Actions tab
2. Running the "Deploy Intelligence Ingestor to Azure" workflow manually
3. Choose "staging" environment to test

The workflow will create all necessary Azure resources and deploy your application.