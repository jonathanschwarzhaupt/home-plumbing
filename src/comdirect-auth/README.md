# Comdirect Auth

A small containerized script that completes comdirect's OAuth flow and saves the token to a 1password vault.

## Features

- Completes the oauth flow if token not exists
- Checks if the token needs to be refreshed if exists
- Refreshes and saves token if needs to be refreshed

## Required environment variable

```
COMDIRECT_CLIENT_ID            # your client id
COMDIRECT_CLIENT_SECRET        # your client secret
COMDIRECT_USERNAME             # username you use to log in
COMDIRECT_PASSWORD             # password you use to log in
OP_SERVICE_ACCOUNT_TOKEN       # 1password service account token with write permissions
OP_VAULT_ID                    # 1password id of the vault (op vault list)
```
