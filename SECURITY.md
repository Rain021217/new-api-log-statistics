# Security

## Sensitive files

Do not publish these files with real values:

- `.env`
- `config/sources.yml`
- `runtime/*`

## Recommended deployment posture

1. Use read-only database accounts
2. Prefer private networks or protected reverse proxies
3. Enable optional login authentication for shared environments
4. Rotate `AUTH_PASSWORD` and `AUTH_SESSION_SECRET` before public deployment

## Reporting

If you discover a credential leak, rotate the exposed secrets first, then remove the leaked files from any release bundle or distribution archive.
