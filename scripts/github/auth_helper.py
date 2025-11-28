#!/usr/bin/env python3
"""
GitHub App Authentication Helper

This script generates an installation access token from GitHub App credentials
and outputs it to stdout for use in bash scripts.

Environment Variables:
    githubAppId: GitHub App ID
    githubAppInstallationId: GitHub App Installation ID
    githubAppPrivateKey: GitHub App Private Key (base64 encoded PEM format)
"""

import base64
import os
import sys

from github import Auth, GithubIntegration


def get_installation_token():
    """
    Generate an installation access token from GitHub App credentials.

    Returns:
        str: The installation access token

    Raises:
        ValueError: If required environment variables are missing
        Exception: If token generation fails
    """
    # Get credentials from environment
    app_id = os.getenv("githubAppId")  # noqa: SIM112 comes from upstream script
    installation_id = os.getenv(
        "githubAppInstallationId"
    )  # noqa: SIM112 comes from upstream script
    private_key_b64 = os.getenv(
        "githubAppPrivateKey"
    )  # noqa: SIM112 comes from upstream script

    # Validate credentials
    if not app_id:
        raise ValueError("Missing environment variable: githubAppId")
    if not installation_id:
        raise ValueError("Missing environment variable: githubAppInstallationId")
    if not private_key_b64:
        raise ValueError("Missing environment variable: githubAppPrivateKey")

    try:
        # Decode base64-encoded private key
        private_key = base64.b64decode(private_key_b64).decode("utf-8")

        # Create GitHub Integration using new Auth API
        auth = Auth.AppAuth(app_id, private_key)
        integration = GithubIntegration(auth=auth)

        # Get installation access token
        access_token = integration.get_access_token(int(installation_id))

        return access_token.token
    except Exception as e:
        raise Exception(f"Failed to generate installation token: {str(e)}") from e


def main():
    """Main function to get and print the token."""
    try:
        token = get_installation_token()
        print(token)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
