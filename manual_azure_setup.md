# Manual Azure Service Principal Setup

Since command substitution isn't working in your shell, here are the manual steps:

## Step 1: Get Your Subscription ID

```bash
az login
az account show --query id --output tsv
```

**Copy the subscription ID from the output** (it looks like: `12345678-1234-1234-1234-123456789012`)

## Step 2: Create Service Principal

Replace `YOUR_SUBSCRIPTION_ID` with the ID from Step 1:

```bash
az ad sp create-for-rbac \
  --name "GitHubActions-IntelligenceIngestor" \
  --role contributor \
  --scopes "/subscriptions/YOUR_SUBSCRIPTION_ID"
```

**Example with a real subscription ID:**
```bash
az ad sp create-for-rbac \
  --name "GitHubActions-IntelligenceIngestor" \
  --role contributor \
  --scopes "/subscriptions/12345678-1234-1234-1234-123456789012"
```

## Step 3: Format the Output

The command above will output something like:
```json
{
  "appId": "87654321-4321-4321-4321-210987654321",
  "displayName": "GitHubActions-IntelligenceIngestor",
  "password": "abcdefghijklmnopqrstuvwxyz123456",
  "tenant": "11111111-2222-3333-4444-555555555555"
}
```

## Step 4: Convert for GitHub

Take the values from Step 3 and create this JSON for GitHub secrets:

```json
{
  "clientId": "87654321-4321-4321-4321-210987654321",
  "clientSecret": "abcdefghijklmnopqrstuvwxyz123456",
  "subscriptionId": "12345678-1234-1234-1234-123456789012",
  "tenantId": "11111111-2222-3333-4444-555555555555"
}
```

**Map the values:**
- `clientId` = `appId` from Step 3
- `clientSecret` = `password` from Step 3
- `subscriptionId` = Your subscription ID from Step 1
- `tenantId` = `tenant` from Step 3

## Step 5: Add to GitHub

1. Go to: https://github.com/weavyguru/intelligence-ingestor/settings/secrets/actions
2. Click "New repository secret"
3. Name: `AZURE_CREDENTIALS`
4. Value: The JSON from Step 4

## Alternative: Use PowerShell Script

If you're on Windows, the PowerShell script should work better:

```powershell
.\create_service_principal.ps1
```

## Quick Reference

Here's what you need in total for GitHub secrets:

1. **AZURE_CREDENTIALS** - JSON from above
2. **BEARER_TOKEN_STAGING** - `staging_eICzX-Vtl3Nur3WzvXs8beiKFryhjr4fn1oxYA1ygq0`
3. **BEARER_TOKEN_PRODUCTION** - `prod_A-d1t0qJk2FTNgyvt_hopLx3wcAVZ5SwtLLqN4A4bI4`
4. **CHROMA_API_KEY** - `ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B`
5. **CHROMA_TENANT** - `cc8a08d9-0db3-472d-bc29-7a2b7cddbc55`
6. **CHROMA_DATABASE** - `weavy_community_intelligence`