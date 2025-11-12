"""
Secret storage integration for API keys.

Actual API keys/secrets are stored in external secret managers:
- HashiCorp Vault
- AWS Secrets Manager
- Azure Key Vault
- Environment variables (development only)

This module provides a unified interface to fetch secrets.
"""
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SecretStoreError(Exception):
    """Raised when secret retrieval fails."""
    pass


def fetch_api_secret(key_id: str) -> str:
    """
    Fetch API secret from configured secret store.
    
    Args:
        key_id: Internal key identifier
        
    Returns:
        The actual API key/secret
        
    Raises:
        SecretStoreError: If secret cannot be retrieved
    """
    store_type = os.environ.get('SECRET_STORE_TYPE', 'env')
    
    if store_type == 'env':
        return _fetch_from_env(key_id)
    elif store_type == 'vault':
        return _fetch_from_vault(key_id)
    elif store_type == 'aws':
        return _fetch_from_aws(key_id)
    elif store_type == 'azure':
        return _fetch_from_azure(key_id)
    else:
        raise SecretStoreError(f"Unknown secret store type: {store_type}")


def _fetch_from_env(key_id: str) -> str:
    """
    Fetch secret from environment variable.
    
    Development/testing only - not for production use.
    Environment variable format: API_KEY_{key_id} (exact match)
    """
    env_var = f"API_KEY_{key_id}"
    secret = os.environ.get(env_var)
    
    if not secret:
        raise SecretStoreError(f"Environment variable {env_var} not set")
    
    logger.debug(f"Fetched secret for {key_id} from environment")
    return secret


def _fetch_from_vault(key_id: str) -> str:
    """
    Fetch secret from HashiCorp Vault.
    
    Requires: hvac library
    """
    try:
        import hvac
    except ImportError:
        raise SecretStoreError("hvac library not installed (pip install hvac)")
    
    vault_addr = os.environ.get('VAULT_ADDR')
    vault_token = os.environ.get('VAULT_TOKEN')
    vault_path = os.environ.get('VAULT_SECRET_PATH', 'secret/llm')
    
    if not vault_addr or not vault_token:
        raise SecretStoreError("VAULT_ADDR and VAULT_TOKEN must be set")
    
    try:
        client = hvac.Client(url=vault_addr, token=vault_token)
        
        if not client.is_authenticated():
            raise SecretStoreError("Vault authentication failed")
        
        secret_path = f"{vault_path}/{key_id}"
        response = client.secrets.kv.v2.read_secret_version(path=secret_path)
        
        secret = response['data']['data'].get('api_key')
        if not secret:
            raise SecretStoreError(f"No 'api_key' field in {secret_path}")
        
        logger.info(f"Fetched secret for {key_id} from Vault")
        return secret
        
    except Exception as e:
        raise SecretStoreError(f"Vault error for {key_id}: {str(e)}")


def _fetch_from_aws(key_id: str) -> str:
    """
    Fetch secret from AWS Secrets Manager.
    
    Requires: boto3 library
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise SecretStoreError("boto3 library not installed (pip install boto3)")
    
    region = os.environ.get('AWS_REGION', 'us-east-1')
    secret_prefix = os.environ.get('AWS_SECRET_PREFIX', 'llm/')
    
    try:
        client = boto3.client('secretsmanager', region_name=region)
        secret_name = f"{secret_prefix}{key_id}"
        
        response = client.get_secret_value(SecretId=secret_name)
        
        if 'SecretString' in response:
            secret_data = json.loads(response['SecretString'])
            secret = secret_data.get('api_key')
            
            if not secret:
                raise SecretStoreError(f"No 'api_key' field in {secret_name}")
            
            logger.info(f"Fetched secret for {key_id} from AWS Secrets Manager")
            return secret
        else:
            raise SecretStoreError(f"Binary secrets not supported for {secret_name}")
            
    except ClientError as e:
        raise SecretStoreError(f"AWS Secrets Manager error for {key_id}: {str(e)}")


def _fetch_from_azure(key_id: str) -> str:
    """
    Fetch secret from Azure Key Vault.
    
    Requires: azure-keyvault-secrets, azure-identity libraries
    """
    try:
        from azure.keyvault.secrets import SecretClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        raise SecretStoreError(
            "Azure libraries not installed (pip install azure-keyvault-secrets azure-identity)"
        )
    
    vault_url = os.environ.get('AZURE_VAULT_URL')
    if not vault_url:
        raise SecretStoreError("AZURE_VAULT_URL must be set")
    
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        
        secret_name = key_id.replace('_', '-')  # Azure Key Vault naming restrictions
        secret = client.get_secret(secret_name)
        
        logger.info(f"Fetched secret for {key_id} from Azure Key Vault")
        return secret.value
        
    except Exception as e:
        raise SecretStoreError(f"Azure Key Vault error for {key_id}: {str(e)}")


def test_secret_access(key_id: str) -> bool:
    """
    Test if a secret can be retrieved.
    
    Returns:
        True if secret accessible, False otherwise
    """
    try:
        secret = fetch_api_secret(key_id)
        return bool(secret)
    except SecretStoreError:
        return False
