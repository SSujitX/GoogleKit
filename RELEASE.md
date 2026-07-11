## [0.0.4] - 2026-07-12

### Fixed

- **Calendar RSVP:** participant responses use `Attendee.self` only for local
  selection, omit read-only attendee fields, and put `attendeesOmitted` in the
  event request body.
- **OAuth scopes:** cached installed-app tokens are loaded with their actual
  granted scopes and trigger fresh consent when required scopes are missing.
- **Transport:** configured timeouts and user agents are applied to the
  authorized HTTP transport; transient network failures and Google 403/429
  rate-limit responses are retried.
- **Drive folders:** recursive uploads reuse existing folders according to the
  overwrite policy, and exported PDF collision checks use the actual `.pdf`
  destination.
- **Drive exports:** Google Vids are no longer sent to the incompatible
  `files.export` endpoint. The error now explains that Google requires the
  long-running `files.download` operation.
- **Drive shortcuts:** default filenames for exported Google-native files gain
  the correct extension for both short formats and full MIME types.
- **Docs tabs:** `documents.get` requests tab content by default, parses nested
  tabs, and preserves/aggregates named ranges from each `documentTab`.
- **Token storage:** token writes are atomic and use restrictive permissions
  where supported.
- **Documentation:** scope-error behavior and current Drive/Docs limitations now
  match the implementation.

### Validation

- 239 non-integration tests pass.
- MkDocs strict build passes.
- Wheel and source distribution build as version 0.0.4.