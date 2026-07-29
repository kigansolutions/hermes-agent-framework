# Hermes public framework safety policy

This repository is a public reference framework and experimental local orchestrator. It is not a production assistant, hosted service, or authorization to connect live Telegram, Caido, browser, shell, credential, or private Hermes runtime data.

## Operating boundary

Hermes command and browser capabilities are restricted to a trusted local operator. Do not expose these surfaces directly to chat, Telegram, webhooks, public APIs, or other untrusted input until a separate execution policy, sandbox design, and owner approval are recorded.

Allowed use in this public repository:

- read and inspect the framework architecture;
- install base Python dependencies;
- run static smoke validation;
- experiment locally with non-sensitive, owner-controlled fixtures.

Not authorized by this repository:

- autonomous shell execution from untrusted prompts;
- scanning, testing, or browsing third-party targets without explicit scope confirmation;
- storing real passwords, tokens, hashes, customer data, payroll data, or private runtime memory;
- publishing Telegram, browser, Caido, or assistant integrations as live services.

## Command execution policy

The current reference implementation includes `shell=True` command execution paths. Treat those paths as local-operator-only until hardening is complete.

Before live use, a follow-up policy must define:

- an allowlist of permitted tools and command shapes;
- argument-vector execution where practical instead of caller-derived shell strings;
- scope confirmation before any network, recon, scan, fuzz, exploit, or credential-testing action;
- destructive-action gates for writes, deletes, exploit attempts, brute force, account testing, and data exfiltration-like behavior;
- audit logging of requested command, normalized command, operator, timestamp, target, and result;
- timeout, rate-limit, and cancellation behavior;
- safe fixture tests that prove blocked commands do not execute.

Until those controls exist, assume commands can affect the local machine and network. Run only in a disposable, owner-controlled environment.

## Browser stealth restrictions

`integration/browser.py` contains browser stealth and weakened-isolation flags such as anti-automation behavior, `--no-sandbox`, disabled web security, insecure-content allowances, and certificate-error ignores. These are sensitive security-testing capabilities.

Use browser stealth only for authorized security testing in a controlled local environment. It must not be described or exposed as a general assistant automation feature. Do not use it against third-party services, login flows, or protected platforms without explicit written authorization and scope confirmation.

Before browser automation is connected to AIOS or a public assistant surface, record:

- allowed domains and test accounts;
- whether stealth mode is permitted or disabled by default;
- screenshot and artifact retention rules;
- credential-entry rules;
- human approval before login, form submission, purchase, message sending, or destructive actions.

## Credential-like memory handling

`knowledge/knowledge.py` includes a credential-like table shape for reference data. Runtime SQLite files are ignored by git, but local storage of usernames, passwords, hashes, tokens, or recovered secrets is still sensitive.

For public and client-safe use, credential-like memory is disabled by policy until a separate data-handling decision is recorded. That decision must cover:

- explicit operator consent before capture;
- encryption at rest;
- retention period;
- purge workflow;
- export restrictions;
- whether hashes and passwords are stored at all;
- test evidence proving secrets are not committed.

Do not commit runtime databases, local memory exports, token files, `.env` files, screenshots containing secrets, or copied credential material.

## Runtime validation gate

A later runtime-validation PR may import and exercise Hermes only with harmless fixtures. That PR must state exactly which commands, targets, credentials, browser profiles, and integrations are in scope. It must not connect private deployments or live accounts without Cameron's explicit approval.
