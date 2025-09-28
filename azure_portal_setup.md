# Azure Portal Service Principal Setup

Since you don't have Azure CLI permissions, here's how to create the service principal through the Azure Portal:

## Step 1: Create App Registration

1. **Go to Azure Portal**: https://portal.azure.com
2. **Search for "App registrations"** in the top search bar
3. **Click "App registrations"** from the results
4. **Click "New registration"** (blue button at the top)
5. **Fill in the form**:
   - **Name**: `GitHubActions-IntelligenceIngestor`
   - **Supported account types**: Select "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank
6. **Click "Register"**

## Step 2: Copy Application (Client) ID and Tenant ID

After registration, you'll see the app overview page:

1. **Copy the "Application (client) ID"** - this will be your `clientId`
2. **Copy the "Directory (tenant) ID"** - this will be your `tenantId`

**Save these values - you'll need them later!**

## Step 3: Create Client Secret

1. **In your app registration**, click "Certificates & secrets" in the left menu
2. **Click "New client secret"**
3. **Fill in**:
   - **Description**: `GitHub Actions Secret`
   - **Expires**: Select "24 months" (or your preferred duration)
4. **Click "Add"**
5. **IMMEDIATELY COPY THE SECRET VALUE** - this will be your `clientSecret`
   - ⚠️ **Important**: You can only see this value once! Copy it now!

## Step 4: Assign Contributor Role

1. **Search for "Subscriptions"** in the Azure Portal search bar
2. **Click on your subscription** (should show your subscription ID: `284ff4e0-b3e1-4b81-a1ca-8fdf363c2175`)
3. **Click "Access control (IAM)"** in the left menu
4. **Click "Add" → "Add role assignment"**
5. **On the Role tab**:
   - **Role**: Search for and select "Contributor"
   - **Click "Next"**
6. **On the Members tab**:
   - **Assign access to**: Select "User, group, or service principal"
   - **Click "Select members"**
   - **Search for**: `GitHubActions-IntelligenceIngestor`
   - **Select your app** from the results
   - **Click "Select"**
7. **Click "Next"** then **"Review + assign"**
8. **Click "Review + assign"** again to confirm

## Step 5: Format for GitHub

Now create the JSON for GitHub secrets using the values you collected:

```json
{
  "clientId": "YOUR_APPLICATION_CLIENT_ID_FROM_STEP_2",
  "clientSecret": "YOUR_SECRET_VALUE_FROM_STEP_3",
  "subscriptionId": "284ff4e0-b3e1-4b81-a1ca-8fdf363c2175",
  "tenantId": "YOUR_DIRECTORY_TENANT_ID_FROM_STEP_2"
}
```

**Example of what it should look like:**
```json
{
  "clientId": "12345678-1234-1234-1234-123456789abc",
  "clientSecret": "abC1Q~secretValueHere123456789",
  "subscriptionId": "284ff4e0-b3e1-4b81-a1ca-8fdf363c2175",
  "tenantId": "87654321-4321-4321-4321-210987654def"
}
```

## Step 6: Add to GitHub Secrets

1. **Go to**: https://github.com/weavyguru/intelligence-ingestor/settings/secrets/actions
2. **Click "New repository secret"**
3. **Name**: `AZURE_CREDENTIALS`
4. **Value**: Paste the JSON from Step 5
5. **Click "Add secret"**

## Step 7: Add Remaining GitHub Secrets

Add these additional secrets (one by one):

1. **BEARER_TOKEN_STAGING**
   - Value: `staging_eICzX-Vtl3Nur3WzvXs8beiKFryhjr4fn1oxYA1ygq0`

2. **BEARER_TOKEN_PRODUCTION**
   - Value: `prod_A-d1t0qJk2FTNgyvt_hopLx3wcAVZ5SwtLLqN4A4bI4`

3. **CHROMA_API_KEY**
   - Value: `ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B`

4. **CHROMA_TENANT**
   - Value: `cc8a08d9-0db3-472d-bc29-7a2b7cddbc55`

5. **CHROMA_DATABASE**
   - Value: `weavy_community_intelligence`

## Step 8: Set Up GitHub Environments

1. **Go to**: https://github.com/weavyguru/intelligence-ingestor/settings/environments
2. **Click "New environment"**
3. **Name**: `staging`
4. **Click "Configure environment"**
5. **Don't add any protection rules** for staging
6. **Click "Save protection rules"**

**Repeat for production environment:**
1. **Click "New environment"** again
2. **Name**: `production`
3. **Click "Configure environment"**
4. **Check "Required reviewers"** and add yourself
5. **Click "Save protection rules"**

## Step 9: Test the Setup

1. **Go to your repository's Actions tab**
2. **Click "Deploy Intelligence Ingestor to Azure"**
3. **Click "Run workflow"**
4. **Select "staging" environment**
5. **Click "Run workflow"**

This will test your setup and deploy to Azure if everything is configured correctly!

## 🔍 Troubleshooting

**If you can't find "App registrations":**
- Make sure you're logged into the correct Azure account
- Check if you have permission to create app registrations
- Try asking your Azure administrator

**If role assignment fails:**
- You might not have Owner/User Access Administrator permissions
- Ask your Azure administrator to assign the Contributor role
- Or ask them to give you permission to assign roles

**If GitHub Actions fails:**
- Check that all 6 secrets are added correctly
- Verify the JSON format has no extra spaces or characters
- Check the GitHub Actions logs for specific error messages