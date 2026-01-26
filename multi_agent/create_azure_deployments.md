# Creating Azure OpenAI Model Deployments

## Quick Reference

You need to create these two deployments in your Azure OpenAI resource:

1. **Deployment Name**: `gpt-4o-mini` → Model: GPT-4o mini
2. **Deployment Name**: `gpt-4o` → Model: GPT-4o

> ⚠️ **Critical**: The deployment names must match exactly what's in `keys.json`

---

## Method 1: Azure Portal (Easiest)

### Step 1: Navigate to Azure OpenAI Studio

1. Open your browser and go to: https://oai.azure.com/
2. Sign in with your Azure credentials
3. Select your resource: **algoagent** (from endpoint: https://algoagent.openai.azure.com/)

### Step 2: Create `gpt-4o-mini` Deployment

1. Click **Deployments** in the left menu
2. Click **+ Create new deployment**
3. Fill in the form:
   - **Select a model**: `gpt-4o-mini`
   - **Model version**: `Latest` or specific version (e.g., `2024-07-18`)
   - **Deployment name**: `gpt-4o-mini` ⚠️ **Must match exactly**
   - **Deployment type**: `Standard`
   - **Tokens per Minute Rate Limit**: `200K` (or your desired limit)
4. Click **Create**

### Step 3: Create `gpt-4o` Deployment

1. Click **+ Create new deployment** again
2. Fill in the form:
   - **Select a model**: `gpt-4o`
   - **Model version**: `Latest` or specific version (e.g., `2024-08-06`)
   - **Deployment name**: `gpt-4o` ⚠️ **Must match exactly**
   - **Deployment type**: `Standard`
   - **Tokens per Minute Rate Limit**: `450K` (or your desired limit)
3. Click **Create**

### Step 4: Verify Deployments

1. Go to **Deployments** page
2. Confirm you see:
   - ✅ `gpt-4o-mini` (Status: Succeeded)
   - ✅ `gpt-4o` (Status: Succeeded)

---

## Method 2: Azure CLI (Automated)

### Prerequisites

1. **Install Azure CLI** (if not already installed):
   ```powershell
   winget install -e --id Microsoft.AzureCLI
   ```

2. **Login to Azure**:
   ```powershell
   az login
   ```

### Get Your Resource Details

First, find your Azure OpenAI resource name and resource group:

```powershell
# List all Azure OpenAI accounts
az cognitiveservices account list --query "[?kind=='OpenAI'].{Name:name, ResourceGroup:resourceGroup, Location:location}" -o table
```

### Create Deployments

Replace `<resource-group>` and `<account-name>` with your actual values:

```powershell
# Set variables
$resourceGroup = "<resource-group>"  # e.g., "algoagent-rg"
$accountName = "algoagent"           # Your Azure OpenAI resource name

# Create gpt-4o-mini deployment
az cognitiveservices account deployment create `
  --resource-group $resourceGroup `
  --name $accountName `
  --deployment-name "gpt-4o-mini" `
  --model-name "gpt-4o-mini" `
  --model-version "2024-07-18" `
  --model-format "OpenAI" `
  --sku-capacity 200 `
  --sku-name "Standard"

# Create gpt-4o deployment
az cognitiveservices account deployment create `
  --resource-group $resourceGroup `
  --name $accountName `
  --deployment-name "gpt-4o" `
  --model-name "gpt-4o" `
  --model-version "2024-08-06" `
  --model-format "OpenAI" `
  --sku-capacity 450 `
  --sku-name "Standard"
```

### Verify Deployments

```powershell
# List all deployments
az cognitiveservices account deployment list `
  --resource-group $resourceGroup `
  --name $accountName `
  --query "[].{Name:name, Model:properties.model.name, Status:properties.provisioningState}" `
  -o table
```

---

## Method 3: Azure REST API

### Get Access Token

```powershell
$token = az account get-access-token --query accessToken -o tsv
```

### Create Deployments via REST

```powershell
# Set variables
$subscriptionId = "<your-subscription-id>"
$resourceGroup = "<resource-group>"
$accountName = "algoagent"
$apiVersion = "2023-05-01"

# Create gpt-4o-mini deployment
$body1 = @{
    sku = @{
        name = "Standard"
        capacity = 200
    }
    properties = @{
        model = @{
            format = "OpenAI"
            name = "gpt-4o-mini"
            version = "2024-07-18"
        }
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.CognitiveServices/accounts/$accountName/deployments/gpt-4o-mini?api-version=$apiVersion" `
  -Method Put `
  -Headers @{Authorization = "Bearer $token"; "Content-Type" = "application/json"} `
  -Body $body1

# Create gpt-4o deployment
$body2 = @{
    sku = @{
        name = "Standard"
        capacity = 450
    }
    properties = @{
        model = @{
            format = "OpenAI"
            name = "gpt-4o"
            version = "2024-08-06"
        }
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://management.azure.com/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.CognitiveServices/accounts/$accountName/deployments/gpt-4o?api-version=$apiVersion" `
  -Method Put `
  -Headers @{Authorization = "Bearer $token"; "Content-Type" = "application/json"} `
  -Body $body2
```

---

## After Creating Deployments

### 1. Update Your `.env` File

Get your API key from Azure Portal:
1. Go to Azure Portal → Your Azure OpenAI resource
2. Click **Keys and Endpoint** in the left menu
3. Copy **KEY 1** or **KEY 2**

Update `.env`:
```bash
API_KEY_azure-gpt4o-mini-01=<paste_your_api_key_here>
API_KEY_azure-gpt4o-01=<paste_your_api_key_here>
```

### 2. Test the Integration

```powershell
cd C:\Users\nyaga\Documents\AlgoAgent\multi_agent
python test_azure_integration.py
```

Expected output:
```
✅ Azure OpenAI provider successfully registered
✅ AZURE_OPENAI_ENDPOINT configured
✅ Found 2 Azure OpenAI key(s)
✅ API call successful!
🎉 All critical tests passed!
```

---

## Troubleshooting

### Error: "The model 'gpt-4o' does not exist"

**Solution**: The model might not be available in your region. Check available models:

```powershell
az cognitiveservices account list-models `
  --resource-group $resourceGroup `
  --name $accountName `
  --query "[?kind=='OpenAI'].name" -o table
```

### Error: "Deployment name already exists"

**Solution**: Either use the existing deployment or delete it first:

```powershell
az cognitiveservices account deployment delete `
  --resource-group $resourceGroup `
  --name $accountName `
  --deployment-name "gpt-4o-mini"
```

### Error: "Quota exceeded"

**Solution**: Check your quota limits:

```powershell
az cognitiveservices usage list `
  --location <your-location> `
  --query "[?name.value=='OpenAI.Standard.gpt-4o']"
```

Request quota increase: https://aka.ms/oai/quotaincrease

---

## Quick Checklist

- [ ] Azure OpenAI resource exists: `algoagent`
- [ ] Deployment `gpt-4o-mini` created
- [ ] Deployment `gpt-4o` created
- [ ] API key copied to `.env`
- [ ] Test script passes: `python test_azure_integration.py`
- [ ] First request succeeds

---

## Links

- **Azure OpenAI Studio**: https://oai.azure.com/
- **Model Availability**: https://learn.microsoft.com/azure/ai-services/openai/concepts/models
- **Deployment Guide**: https://learn.microsoft.com/azure/ai-services/openai/how-to/create-resource
- **Quota Management**: https://learn.microsoft.com/azure/ai-services/openai/quotas-limits
