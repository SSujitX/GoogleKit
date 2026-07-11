# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a vulnerability

Please report security issues privately via GitHub Security Advisories on the
[GoogleKit repository](https://github.com/SSujitX/GoogleKit), or email the maintainer
listed in `pyproject.toml`.

Do **not** open a public issue for vulnerabilities that could expose credentials,
tokens, or private key material.

Include:

- A description of the issue and impact
- Steps to reproduce (without real secrets)
- Affected versions if known

We aim to acknowledge reports within a reasonable timeframe and coordinate a fix
before any public disclosure.

## Credential safety

GoogleKit never requires committing secrets. Follow these practices:

- Keep `client_secret*.json`, service-account keys, and OAuth tokens out of git
- Prefer OS user config paths for tokens (default `FileTokenStore` location)
- Restrict file permissions on credential and token files where the OS allows
- Rotate compromised keys immediately in Google Cloud Console
- Use least-privilege OAuth scopes (`ScopeProfile` / presets)
- Remember that service accounts do not automatically access personal Drive files
  unless those files are shared with the service account, or Workspace domain-wide
  delegation is configured

GoogleKit redacts secrets from logs where practical. Never print credential JSON,
access tokens, refresh tokens, or private keys in applications or CI logs.
