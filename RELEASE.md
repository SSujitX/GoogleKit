# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Google API client libraries are now default dependencies (`uv add googlekit`); service extras removed
- Unified `GoogleKit` constructors require explicit `services=` or `scopes=` (no all-service default)
- OAuth cached tokens are accepted only when their granted scopes cover the request (no fake scope expansion)
- HTTP timeout / authorized httplib2 transport; retry TransportError and 403 rate-limit reasons
- Drive folder upload/download overwrite safety; Docs `includeTabsContent` + tab parsing
- Calendar `response_status` applies only to `self=True` attendees with `attendeesOmitted`

### Added

- Core package: exceptions, retries, pagination, transport, client-library checks
- Authentication: OAuth desktop, service account, ADC, scope presets, token stores
- Unified `GoogleKit` client with lazy service accessors
- Minimal CLI (`googlekit --version`, `doctor`, `auth status`)
- Documentation, examples, CI, and packaging tests

## [0.1.0] - 2026-07-11

### Added

- Initial public release scaffolding for GoogleKit
