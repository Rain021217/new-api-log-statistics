# Contributing

## Scope

This project focuses on analytics and reporting for `new-api` usage logs.

## Local development

1. Copy `.env.example` to `.env`
2. Copy `config/sources.example.yml` to `config/sources.yml`
3. Fill in a test database
4. Start the stack with `make up` or `make up-cache`

## Pull request expectations

1. Keep changes scoped and reversible
2. Do not commit real database credentials, `.env`, runtime logs, or `config/sources.yml`
3. Update `README.md` when deployment, configuration, or user-facing behavior changes
4. Update `CHANGELOG.md` for notable release-facing changes

## Release hygiene

Before sharing a release bundle, run:

```bash
make release-bundle
make verify-release
```
