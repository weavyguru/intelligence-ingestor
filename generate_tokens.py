#!/usr/bin/env python3
"""
Generate secure tokens for GitHub repository secrets
Run this script to generate the bearer tokens needed for your GitHub secrets.
"""

import secrets

def generate_secure_token(prefix="", length=32):
    """Generate a secure URL-safe token"""
    token = secrets.token_urlsafe(length)
    if prefix:
        return f"{prefix}_{token}"
    return token

def main():
    print("🔐 Generating secure tokens for GitHub repository secrets...\n")

    # Generate tokens
    staging_token = generate_secure_token("staging", 32)
    production_token = generate_secure_token("prod", 32)

    print("📋 Copy these values to your GitHub repository secrets:")
    print("=" * 60)

    print(f"\n🟡 BEARER_TOKEN_STAGING:")
    print(f"   {staging_token}")

    print(f"\n🟢 BEARER_TOKEN_PRODUCTION:")
    print(f"   {production_token}")

    print(f"\n📝 Additional secrets you'll need:")
    print("   CHROMA_API_KEY: ck-D8S37tEEaVKAQqyw2mGy8sSswmAfKaYqxEWBuYGMHT5B")
    print("   CHROMA_TENANT: cc8a08d9-0db3-472d-bc29-7a2b7cddbc55")
    print("   CHROMA_DATABASE: weavy_community_intelligence")

    print("\n🔑 Don't forget to create your Azure Service Principal:")
    print("   az ad sp create-for-rbac --name 'GitHubActions-IntelligenceIngestor' --role contributor --scopes /subscriptions/YOUR_SUBSCRIPTION_ID --sdk-auth")

    print("\n💡 Save these tokens securely - they won't be shown again!")
    print("=" * 60)

if __name__ == "__main__":
    main()