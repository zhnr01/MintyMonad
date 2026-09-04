# Security Policy

## Scope

MintyMonad is a Monad Testnet portfolio project. It is not intended for mainnet funds or production financial use.

## Reporting

Do not publicly disclose a suspected vulnerability before maintainers have had a reasonable opportunity to investigate. Open a private security report through the repository hosting provider and include reproduction steps, affected files, impact, and suggested remediation.

Never include private keys, API keys, seed phrases, or other credentials in a report.

## Known limitations

The smart contract has not received an independent audit. The application depends on external RPC and metadata providers. Production deployment requires additional rate limiting, CSRF controls, monitoring, migrations, and a hardened WSGI deployment.
