"""
Quick GitHub Models PAT Setup Script

This script helps you:
1. Input your GitHub Personal Access Token
2. Save it to .env in the correct format
3. Verify it works with GitHub Models API
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from openai import OpenAI
except ImportError:
    print("❌ Error: openai package not installed")
    print("   Run: pip install -r requirements_llm.txt")
    sys.exit(1)

def main():
    print("\n" + "="*60)
    print("  GitHub Models - Manual PAT Setup")
    print("="*60)
    print("\nℹ️  Device flow doesn't work for GitHub Models.")
    print("   You need a Personal Access Token (PAT) instead.\n")
    
    print("📋 Steps to create PAT:")
    print("   1. Visit: https://github.com/settings/tokens/new")
    print("   2. Name: 'AlgoAgent LLM Access'")
    print("   3. Select scope: 'models' ✓")
    print("   4. Generate token\n")
    
    # Get token from user
    token = input("📝 Paste your GitHub PAT here: ").strip()
    
    if not token:
        print("❌ No token provided. Exiting.")
        sys.exit(1)
    
    if not token.startswith("github_pat_"):
        print("\n⚠️  Warning: Token doesn't start with 'github_pat_'")
        print("   Are you sure this is a GitHub PAT?")
        confirm = input("   Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            sys.exit(1)
    
    # Get key ID
    key_id = input("\n🔑 Enter key ID (default: github-models-01): ").strip()
    if not key_id:
        key_id = "github-models-01"
    
    # Find .env file
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print(f"\n❌ .env file not found at: {env_path}")
        print("   Creating from .env.example...")
        example_path = env_path.parent / ".env.example"
        if example_path.exists():
            with open(example_path, 'r') as f:
                content = f.read()
            with open(env_path, 'w') as f:
                f.write(content)
            print("✅ Created .env file")
        else:
            print("❌ .env.example not found. Cannot create .env")
            sys.exit(1)
    
    # Add/update token in .env
    env_key = f"API_KEY_{key_id}"
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Check if key exists
    key_exists = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{env_key}="):
            # Replace existing key
            new_lines.append(f"{env_key}={token}\n")
            key_exists = True
        else:
            new_lines.append(line)
    
    if not key_exists:
        # Add new key after the GitHub Models section
        inserted = False
        for i, line in enumerate(new_lines):
            if "# GITHUB MODELS" in line:
                # Find the end of the GitHub Models section
                for j in range(i, len(new_lines)):
                    if new_lines[j].strip() == "" and j > i + 5:
                        new_lines.insert(j, f"{env_key}={token}\n")
                        inserted = True
                        break
                if inserted:
                    break
        
        if not inserted:
            # Append to end if no GitHub Models section found
            new_lines.append(f"\n{env_key}={token}\n")
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"\n✅ Token saved to .env as {env_key}")
    
    # Verify token
    print("\n🔍 Verifying token...")
    try:
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=token
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Token verified!'"}],
            max_tokens=10
        )
        
        print("✅ Token verified successfully!")
        print(f"   Model response: {response.choices[0].message.content}")
        
    except Exception as e:
        error_str = str(e)
        print(f"⚠️  Token saved but verification failed: {error_str[:100]}")
        
        if "401" in error_str or "Unauthorized" in error_str:
            print("\n❌ Token is invalid or missing 'models' permission")
            print("   Please check:")
            print("   1. Token is correct (copy/paste again)")
            print("   2. 'models' scope is selected when creating PAT")
            print("   3. Token hasn't  expired")
        else:
            print(f"\n⚠️  Unexpected error: {error_str}")
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print(f"\n✅ Token saved as {env_key}")
    print("\n📝 Next steps:")
    print(f"   1. Ensure keys.json has key_id: '{key_id}'")
    print("   2. Test with: python run_cli.py")
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
