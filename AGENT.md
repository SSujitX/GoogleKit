You are a principal Python library architect and senior Google Workspace API engineer.

Build a complete, production-quality, publishable Python package named GoogleKit.

GoogleKit is an unofficial Python SDK that provides a clean, consistent, strongly typed interface for:

1. Google Drive
2. Google Sheets
3. Google Calendar
4. Google Docs
5. Google Slides

The project must be safe, modular, easy to understand, easy to test, easy to extend, and ready for publication to PyPI.

Do not produce a prototype, a single-file script, placeholder code, pseudocode, incomplete skeletons, or large unorganized files.

────────────────────────────────────────────────────────────────
1. RESEARCH BEFORE WRITING CODE
────────────────────────────────────────────────────────────────

Before generating code:

1. Research the latest official documentation from:
   - Google Workspace developer documentation
   - Google authentication documentation
   - uv documentation
   - Python Packaging User Guide
   - PyPI package metadata for all dependencies

2. Verify:
   - Current Google API versions
   - Current recommended Python Google API client libraries
   - Current OAuth desktop flow
   - Current service-account flow
   - Current Application Default Credentials flow
   - Supported Python versions
   - Current uv packaging and publishing commands
   - Current OAuth scopes for all five services
   - Whether the PyPI project name `googlekit` is available

3. Use official documentation as the source of truth.

4. Do not copy outdated quickstart architecture blindly.

5. Do not use:
   - oauth2client
   - deprecated out-of-band OAuth flows
   - obsolete setup.py-based packaging
   - requirements.txt as the project dependency source
   - hardcoded dependency versions without checking current compatibility
   - undocumented Google API behavior

6. If `googlekit` is already occupied on PyPI:
   - Report that clearly before publishing.
   - Keep the internal import package named `googlekit`.
   - Do not silently rename the project without approval.

────────────────────────────────────────────────────────────────
2. DEVELOPMENT TOOLING
────────────────────────────────────────────────────────────────

Use uv exclusively for development.

Do not use pip, Poetry, Pipenv, Conda, or manually managed virtual environments in project instructions.

Required workflow:

    uv init --lib
    uv add ...
    uv add --dev ...
    uv sync
    uv lock
    uv run pytest
    uv run ruff check .
    uv run ruff format .
    uv run mypy src
    uv build

Use:

- `pyproject.toml` as the single project configuration source
- `uv.lock` for the reproducible development environment
- `src` package layout
- the current recommended uv-compatible build backend
- Python 3.14 for local development if all dependencies support it
- package compatibility with Python 3.11 through Python 3.14 when feasible

Research compatibility first. Do not falsely claim support for an untested Python version.

Commit:

- pyproject.toml
- uv.lock
- .python-version

Do not create requirements.txt unless there is a documented external compatibility requirement.

────────────────────────────────────────────────────────────────
3. INSTALLATION CONTRACT
────────────────────────────────────────────────────────────────

Use one distribution with standardized optional dependencies.

Required installation commands:

    uv add googlekit
    uv add "googlekit[gdrive]"
    uv add "googlekit[gsheets]"
    uv add "googlekit[gcalendar]"
    uv add "googlekit[gdocs]"
    uv add "googlekit[gslides]"
    uv add "googlekit[all]"

Meaning:

- `googlekit`
  - Core types
  - Authentication abstractions
  - Exceptions
  - Configuration
  - No eager import of optional Google service dependencies

- `googlekit[gdrive]`
  - Google Drive functionality

- `googlekit[gsheets]`
  - Google Sheets functionality

- `googlekit[gcalendar]`
  - Google Calendar functionality

- `googlekit[gdocs]`
  - Google Docs functionality

- `googlekit[gslides]`
  - Google Slides functionality

- `googlekit[all]`
  - All five services

Use `[project.optional-dependencies]`.

Do not create circular self-dependencies such as placing
`googlekit[gdrive]` inside GoogleKit’s own optional-dependency definitions.

List the actual dependency union directly in each applicable extra.

Extras add dependencies; they do not selectively remove package source files. All service source modules may ship in the wheel, but unavailable services must fail cleanly when their required extra is not installed.

Required error example:

    Google Drive support is not installed.
    Install it with:
        uv add "googlekit[gdrive]"

The base package must import successfully when no service extra is installed.

────────────────────────────────────────────────────────────────
4. PACKAGE PURPOSE AND PUBLIC API
────────────────────────────────────────────────────────────────

Provide two supported usage styles.

Unified client:

    from googlekit import GoogleKit

    kit = GoogleKit.from_oauth(
        client_secrets="client_secret.json",
        token_path="token.json",
    )

    kit.drive.files.upload("report.pdf")
    kit.sheets.values.read("spreadsheet_id", "Sheet1!A1:D20")
    kit.calendar.events.create(...)
    kit.docs.documents.create("Proposal")
    kit.slides.presentations.create("Pitch Deck")

Individual clients:

    from googlekit.gdrive import DriveClient

    drive = DriveClient.from_oauth(
        client_secrets="client_secret.json",
        token_path="token.json",
    )

    drive.files.upload("report.pdf")

Requirements:

- Services are lazily initialized.
- Importing `googlekit` must not initialize every Google service.
- Credentials can be shared across service clients.
- Public APIs must be stable, predictable, and consistently named.
- Every public class, method, exception, and model must have a concise, useful docstring.
- Return useful typed models while retaining access to the original Google API response when appropriate.
- Do not return unexplained nested dictionaries everywhere.
- Do not hide important Google behavior or permission requirements.

────────────────────────────────────────────────────────────────
5. AUTHENTICATION
────────────────────────────────────────────────────────────────

Implement these credential methods:

A. OAuth 2.0 Desktop Client

    GoogleKit.from_oauth(
        client_secrets="client_secret.json",
        token_path=None,
        scopes=None,
    )

Requirements:

- Browser-based local-server authorization
- Automatic token refresh
- Configurable token storage
- Reauthorization when additional scopes are required
- Clear cancellation and browser-flow errors
- No deprecated OOB flow
- Token files stored in an OS-appropriate user configuration directory by default
- Never place tokens in the installed package directory

B. Service Account

    GoogleKit.from_service_account(
        credentials_file="service-account.json",
        subject=None,
        scopes=None,
    )

Requirements:

- Normal service-account support
- Optional Workspace domain-wide delegation using `subject`
- Clearly document that domain-wide delegation requires Workspace administrator configuration
- Clearly document that ordinary service accounts do not automatically own or access a personal user’s files

C. Application Default Credentials

    GoogleKit.from_adc(
        quota_project_id=None,
        scopes=None,
    )

Requirements:

- Use the current official Google authentication mechanism
- Clear error when ADC is unavailable

Create a credential-provider abstraction so additional authentication methods can be added without modifying every service.

Suggested public abstractions:

- CredentialProvider protocol
- OAuthCredentialProvider
- ServiceAccountCredentialProvider
- ADCCredentialProvider
- TokenStore protocol
- FileTokenStore
- InMemoryTokenStore

Security requirements:

- Never log access tokens, refresh tokens, client secrets, private keys, authorization codes, or credential JSON contents
- Redact secrets from exceptions and logs
- Use pathlib
- Use safe file permissions where supported
- Never commit credential or token files
- Include proper .gitignore rules
- Include `.env.example` only for non-secret variable names
- Do not require environment variables when explicit configuration is cleaner

────────────────────────────────────────────────────────────────
6. OAUTH SCOPES
────────────────────────────────────────────────────────────────

Create a centralized scope system.

Do not request all scopes by default.

Use least privilege.

Support explicit scope profiles such as:

- metadata/read-only
- read-only
- read-write
- full access where genuinely required

Drive scope behavior must clearly distinguish between:

- files created or selected through the app
- metadata access
- all-file read access
- full Drive access

Never silently escalate OAuth privileges.

If a method requires a scope not currently granted:

- Detect it where practical
- Raise a clear InsufficientScopesError
- Identify the required scope
- Explain how to reauthorize

Create:

- Scope enum or constants
- ScopeSet value object
- Per-service scope presets
- Scope aggregation for the unified client
- Scope validation tests

OAuth tokens are scope-bound. Handle adding a new service after initial authorization cleanly.

────────────────────────────────────────────────────────────────
7. GOOGLE DRIVE FUNCTIONALITY
────────────────────────────────────────────────────────────────

Implement under `googlekit.gdrive`.

Required managers:

    drive.files
    drive.folders
    drive.permissions
    drive.changes

Required functionality:

Files:
- list
- iterate all with pagination
- search using Drive query syntax
- get metadata
- create
- upload from path
- upload from bytes
- upload from file-like object
- simple upload
- multipart upload
- resumable upload
- configurable chunk size
- upload progress callback
- download to path
- download to bytes
- download to file-like object
- download progress callback
- export Google-native files
- copy
- move
- rename
- update metadata
- trash
- restore from trash
- permanently delete
- checksum/size metadata where available

Folders:
- create folder
- create nested folder path
- list children
- upload directory recursively
- download directory recursively
- configurable overwrite behavior
- preserve meaningful directory structure
- avoid recursion loops and duplicate traversal

Permissions:
- list permissions
- share with user
- share with group
- create public/domain link only when explicitly requested
- change role
- remove permission
- create shareable link
- support reader/commenter/writer where valid
- validate permission type and role

Drive-specific requirements:
- Shared Drive support
- `supportsAllDrives` behavior where required
- corpora/drive ID options where relevant
- pagination
- shortcuts where practical
- Google-native files must use export rather than binary download
- helpful error listing valid export formats
- safe overwrite policies
- no full-file memory loading for large downloads unless explicitly requested

────────────────────────────────────────────────────────────────
8. GOOGLE SHEETS FUNCTIONALITY
────────────────────────────────────────────────────────────────

Implement under `googlekit.gsheets`.

Required managers:

    sheets.spreadsheets
    sheets.values
    sheets.worksheets
    sheets.formatting

Spreadsheets:
- create spreadsheet
- get spreadsheet metadata
- set title
- batch update
- export through Drive when requested
- share through Drive when requested

Values:
- read one range
- read multiple ranges
- write one range
- write multiple ranges
- append rows
- update rows/ranges
- clear range
- clear multiple ranges
- configurable value input option
- configurable render option
- major dimension support
- preserve empty cells correctly

Worksheets:
- list worksheets
- create worksheet
- rename worksheet
- delete worksheet
- duplicate worksheet
- reorder worksheet
- resize rows and columns
- freeze rows and columns
- hide/unhide worksheet

Formatting:
- text formatting
- number formats
- background formatting
- alignment
- borders
- merge/unmerge
- conditional formatting where practical
- column widths
- row heights

Do not add pandas as a mandatory dependency.

If DataFrame support is added, place it behind a separate optional extra such as:

    googlekit[dataframe]

Core Sheets operations must work with ordinary Python sequences and mappings.

────────────────────────────────────────────────────────────────
9. GOOGLE CALENDAR FUNCTIONALITY
────────────────────────────────────────────────────────────────

Implement under `googlekit.gcalendar`.

Required managers:

    calendar.calendars
    calendar.events
    calendar.freebusy

Calendars:
- list calendars
- get calendar
- create secondary calendar where supported
- update calendar metadata
- delete secondary calendar where supported

Events:
- list
- iterate all with pagination
- get
- create
- update
- patch
- delete
- recurring events
- all-day events
- timed events
- attendees
- reminders
- locations
- descriptions
- attachments where supported
- conference/Google Meet creation
- invitation response
- event status
- transparency
- visibility
- extended properties
- time-zone-aware datetimes
- sync tokens where practical

Free/busy:
- query one calendar
- query multiple calendars
- typed busy interval results

Calendar requirements:
- Never accept ambiguous naive datetimes silently
- Require a timezone or apply an explicitly configured default
- Use timezone-aware datetime objects
- Serialize RFC3339 correctly
- Handle all-day dates separately from timed datetimes
- Expose `send_updates` explicitly for operations that may email attendees
- Do not unexpectedly send invitation emails

────────────────────────────────────────────────────────────────
10. GOOGLE DOCS FUNCTIONALITY
────────────────────────────────────────────────────────────────

Implement under `googlekit.gdocs`.

Required managers:

    docs.documents
    docs.content
    docs.tables
    docs.images

Documents:
- create document
- get document
- inspect structural elements
- batch update
- export using Drive
- share using Drive

Content:
- insert text
- append text
- delete content range
- replace all text
- text styling
- paragraph styling
- headings
- page breaks
- lists
- links
- named ranges where supported

Tables:
- insert table
- insert/delete table rows
- insert/delete table columns
- write cell content
- basic table formatting where supported

Images:
- insert image from publicly accessible URL
- resize image
- replace image where supported

Requirements:
- Correctly handle UTF-16 index semantics used by the Docs API
- Document index behavior clearly
- Do not assume Python string indexes always equal Google Docs indexes
- Support template replacement workflows
- Export and sharing rely on Drive; surface the required Drive API/scopes explicitly

────────────────────────────────────────────────────────────────
11. GOOGLE SLIDES FUNCTIONALITY
────────────────────────────────────────────────────────────────

Implement under `googlekit.gslides`.

Required managers:

    slides.presentations
    slides.pages
    slides.elements
    slides.text
    slides.images
    slides.tables

Presentations:
- create
- get
- batch update
- export through Drive
- share through Drive

Pages/slides:
- add slide
- delete slide
- duplicate slide
- reorder slide
- choose layout
- get slide IDs

Elements:
- create shape
- delete element
- move element
- resize element
- group/ungroup where supported

Text:
- insert text
- replace all text
- delete text
- style text
- paragraph styling
- template placeholder replacement

Images:
- insert image by URL
- replace image
- position and size image

Tables:
- create table
- write cells
- add/remove rows or columns where supported
- basic formatting where supported

Requirements:
- Use stable object IDs where appropriate
- Validate dimensions and units
- Provide helpers for common deck-template workflows
- Export and sharing dependencies on Drive must be explicit

────────────────────────────────────────────────────────────────
12. CROSS-SERVICE OPERATIONS
────────────────────────────────────────────────────────────────

Google Docs, Sheets, and Slides sharing/export functionality commonly relies on Google Drive behavior.

Design this cleanly:

- Reuse shared credentials
- Reuse a shared Drive transport/helper
- Do not duplicate Drive export or permission logic
- Do not create circular imports
- Do not silently request broader Drive scopes
- Raise a clear missing-scope or missing-extra error
- Document required API enablement and scopes

The unified GoogleKit client should allow cross-service reuse without requiring the user to authenticate repeatedly.

────────────────────────────────────────────────────────────────
13. ERROR MODEL
────────────────────────────────────────────────────────────────

Create a clear exception hierarchy:

    GoogleKitError
    ConfigurationError
    AuthenticationError
    AuthorizationError
    InsufficientScopesError
    MissingExtraError
    APIError
    NotFoundError
    ConflictError
    ValidationError
    RateLimitError
    QuotaExceededError
    RetryExhaustedError
    TransportError
    PartialFailureError

Requirements:

- Map Google HTTP/API errors into useful exceptions
- Preserve original status code, reason, request ID, and original exception where safe
- Do not leak credentials or request authorization headers
- Produce human-readable messages
- Include actionable installation instructions for MissingExtraError
- Do not catch Exception broadly unless re-raising with preserved context
- Use exception chaining

────────────────────────────────────────────────────────────────
14. RETRIES, PAGINATION, AND TRANSPORT
────────────────────────────────────────────────────────────────

Create shared transport infrastructure.

Retries:
- Retry transient failures only
- Handle rate limits and server failures
- Respect Retry-After where available
- Exponential backoff with jitter
- Configurable maximum attempts
- Do not blindly retry unsafe non-idempotent operations
- Permit callers to disable retries
- Make retry behavior testable without real sleeping

Pagination:
- Support raw pages
- Support lazy iteration
- Support `page_size`
- Support `page_token`
- Do not eagerly load every result by default
- Provide typed Page models where useful

Transport:
- Centralized discovery/service construction
- Lazy service creation
- Configurable user agent
- Optional request timeout where supported
- Standard-library logging
- No print statements in library code
- Document thread-safety accurately after researching the chosen client
- Do not claim thread safety without evidence

Do not invent a fake asynchronous API.

Version 1 should be synchronous and dependable. Async support may be a later feature.

────────────────────────────────────────────────────────────────
15. DATA MODELS AND TYPING
────────────────────────────────────────────────────────────────

Use modern Python typing.

Requirements:

- `from __future__ import annotations`
- pathlib.Path
- dataclasses where appropriate
- Enum or StrEnum where appropriate
- Protocol for pluggable interfaces
- Generic pagination types where useful
- Typed aliases for IDs, ranges, and scopes where they improve clarity
- `py.typed` marker
- strict or near-strict mypy configuration
- minimal use of Any
- no unnecessary Pydantic dependency
- no mutable default arguments
- no raw booleans where an enum gives materially clearer behavior

Models should be small and useful.

Do not create a model class for every trivial dictionary if it adds no value.

Permit advanced users to access raw Google response data.

────────────────────────────────────────────────────────────────
16. REQUIRED PROJECT STRUCTURE
────────────────────────────────────────────────────────────────

Use this as the baseline structure. Adjust only when there is a concrete architectural reason.

googlekit/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── publish.yml
├── docs/
│   ├── index.md
│   ├── installation.md
│   ├── authentication.md
│   ├── scopes.md
│   ├── errors.md
│   ├── drive.md
│   ├── sheets.md
│   ├── calendar.md
│   ├── docs.md
│   ├── slides.md
│   └── publishing.md
├── examples/
│   ├── auth/
│   │   ├── oauth_desktop.py
│   │   ├── service_account.py
│   │   └── adc.py
│   ├── drive/
│   │   ├── upload_download.py
│   │   ├── search_files.py
│   │   └── share_file.py
│   ├── sheets/
│   │   ├── read_write.py
│   │   ├── append_rows.py
│   │   └── format_sheet.py
│   ├── calendar/
│   │   ├── create_event.py
│   │   ├── recurring_event.py
│   │   └── freebusy.py
│   ├── docs/
│   │   ├── create_document.py
│   │   └── replace_template.py
│   └── slides/
│       ├── create_presentation.py
│       └── replace_template.py
├── src/
│   └── googlekit/
│       ├── __init__.py
│       ├── __main__.py
│       ├── client.py
│       ├── py.typed
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── adc.py
│       │   ├── credentials.py
│       │   ├── oauth.py
│       │   ├── service_account.py
│       │   ├── scopes.py
│       │   └── token_store.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── configuration.py
│       │   ├── constants.py
│       │   ├── exceptions.py
│       │   ├── optional.py
│       │   ├── pagination.py
│       │   ├── protocols.py
│       │   ├── retries.py
│       │   ├── transport.py
│       │   ├── types.py
│       │   └── validation.py
│       ├── gdrive/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── changes.py
│       │   ├── files.py
│       │   ├── folders.py
│       │   ├── models.py
│       │   ├── permissions.py
│       │   └── transfers.py
│       ├── gsheets/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── formatting.py
│       │   ├── models.py
│       │   ├── spreadsheets.py
│       │   ├── values.py
│       │   └── worksheets.py
│       ├── gcalendar/
│       │   ├── __init__.py
│       │   ├── calendars.py
│       │   ├── client.py
│       │   ├── events.py
│       │   ├── freebusy.py
│       │   └── models.py
│       ├── gdocs/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── content.py
│       │   ├── documents.py
│       │   ├── images.py
│       │   ├── models.py
│       │   └── tables.py
│       └── gslides/
│           ├── __init__.py
│           ├── client.py
│           ├── elements.py
│           ├── images.py
│           ├── models.py
│           ├── pages.py
│           ├── presentations.py
│           ├── tables.py
│           └── text.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── gdrive/
│   │   ├── gsheets/
│   │   ├── gcalendar/
│   │   ├── gdocs/
│   │   └── gslides/
│   ├── integration/
│   │   ├── gdrive/
│   │   ├── gsheets/
│   │   ├── gcalendar/
│   │   ├── gdocs/
│   │   └── gslides/
│   └── packaging/
│       ├── test_base_install.py
│       ├── test_service_extras.py
│       └── test_wheel.py
├── .gitignore
├── .python-version
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── SECURITY.md
├── mkdocs.yml
├── pyproject.toml
└── uv.lock

File-organization rules:

- Each file must have one clear responsibility.
- Avoid vague modules such as `helpers.py`, `common.py`, or `misc.py`.
- Prefer meaningful names.
- Keep files generally below approximately 250–300 lines.
- Split a file when it has multiple responsibilities, not merely because of line count.
- Do not create dozens of tiny one-function files.
- No god classes.
- No circular imports.
- Keep public APIs in service clients/managers and implementation details private.
- Prefix genuinely private modules or members with `_`.
- Avoid duplicate logic across services.

────────────────────────────────────────────────────────────────
17. CODE QUALITY
────────────────────────────────────────────────────────────────

Code must be:

- Complete
- Concise
- Meaningful
- Readable
- Typed
- Tested
- Documented
- Secure
- Idiomatic
- Production-oriented

Requirements:

- Small focused functions
- Clear names
- Guard clauses instead of deeply nested branches
- No unnecessary inheritance
- Prefer composition
- No premature abstract framework
- No copy-pasted API request logic
- No magic strings scattered through code
- No unexplained numerical constants
- No silent failures
- No `pass`, placeholder TODOs, or NotImplementedError in required functionality
- No generated-looking filler comments
- Comments explain why, not what obvious code does
- Docstrings describe arguments, return values, errors, and important Google-specific behavior
- Use logging rather than print
- Use pathlib rather than string path manipulation
- Validate inputs before sending avoidable bad requests
- Preserve original exceptions through chaining
- Public method naming must be consistent across services

Run:

    uv run ruff format .
    uv run ruff check .
    uv run mypy src
    uv run pytest

All must pass.

────────────────────────────────────────────────────────────────
18. TESTING
────────────────────────────────────────────────────────────────

Use pytest.

Development dependencies should include current compatible versions of:

- pytest
- pytest-cov
- pytest-mock or standard unittest.mock
- ruff
- mypy
- documentation tooling
- build-validation tooling as appropriate

Unit tests:

- Must not make network requests
- Mock the Google service boundary
- Test request payload construction
- Test response conversion
- Test pagination
- Test retry decisions
- Test exception mapping
- Test scope calculations
- Test token storage
- Test missing extras
- Test credential-provider behavior
- Test path handling
- Test timezone handling
- Test Docs UTF-16 indexing helpers
- Test large file streaming behavior without loading entire files

Integration tests:

- Mark with `@pytest.mark.integration`
- Disabled by default
- Require explicit environment configuration
- Never use committed credentials
- Create test resources with unique names
- Clean up created resources in `finally` blocks or fixtures
- Never delete pre-existing user resources
- Clearly document possible quota/API costs

Packaging tests:

1. Build wheel and source distribution with:

       uv build

2. Create a clean environment with base package only.

3. Confirm:

       import googlekit

   succeeds without service dependencies.

4. Confirm accessing an unavailable service raises MissingExtraError with the correct uv command.

5. Install and test each extra independently.

6. Install `[all]` and test all public imports.

7. Verify wheel contents include:
   - all required modules
   - py.typed
   - license metadata
   - no secrets
   - no test credentials
   - no local cache files

8. Verify source and wheel metadata.

Target meaningful coverage of at least 90%, but prioritize behavior over gaming the coverage number.

────────────────────────────────────────────────────────────────
19. DOCUMENTATION
────────────────────────────────────────────────────────────────

README must include:

- What GoogleKit is
- Unofficial/non-Google affiliation disclaimer
- Supported services
- Installation with uv
- Extras table
- OAuth quickstart
- Service-account quickstart
- ADC quickstart
- One working example for each service
- OAuth scope explanation
- API enablement requirements
- Common errors
- Links to full documentation
- Development commands
- Build instructions
- Security warning about credentials
- Supported Python versions
- License

Required installation examples:

    uv add googlekit
    uv add "googlekit[gdrive]"
    uv add "googlekit[gsheets]"
    uv add "googlekit[gcalendar]"
    uv add "googlekit[gdocs]"
    uv add "googlekit[gslides]"
    uv add "googlekit[all]"

Document cross-service requirements:

- Docs/Sheets/Slides export may require Drive API access
- Sharing Docs/Sheets/Slides uses Drive permissions
- Service accounts need files/calendars shared with them unless Workspace delegation is configured
- OAuth consent and app verification may be required for public apps using sensitive or restricted scopes

Examples must:

- Be short
- Be runnable
- Use fake placeholder IDs/emails
- Never contain credentials
- Include cleanup where they create remote resources

────────────────────────────────────────────────────────────────
20. CLI
────────────────────────────────────────────────────────────────

Provide a minimal standard-library-based CLI without adding a heavy CLI framework.

Commands:

    googlekit --version
    googlekit doctor
    googlekit auth status

`doctor` should check:

- Python version
- Installed extras
- Credential configuration
- Token path accessibility
- Available authentication method
- Obvious missing files
- Optional API connectivity only when explicitly requested

It must not print secret values.

The package remains primarily a Python library, not a CLI application.

────────────────────────────────────────────────────────────────
21. CI AND PUBLISHING
────────────────────────────────────────────────────────────────

Create GitHub Actions workflows using the current official uv setup action.

CI must run on:

- Windows
- Linux
- macOS

Test supported Python versions after confirming dependency compatibility.

CI jobs:

- formatting check
- lint
- type check
- unit tests
- package build
- wheel installation smoke test
- extras installation matrix

Integration tests must not run for untrusted pull requests or without explicitly configured secrets.

Publishing:

- Build using `uv build`
- Publish using `uv publish`
- Prefer PyPI Trusted Publishing where currently recommended
- Provide TestPyPI instructions
- Never publish automatically from arbitrary branches
- Publish only from protected tagged releases
- Do not place PyPI API tokens in repository files

Use semantic versioning.

Obtain version at runtime using package metadata rather than manually duplicating version strings throughout the source.

────────────────────────────────────────────────────────────────
22. REQUIRED ACCEPTANCE TESTS
────────────────────────────────────────────────────────────────

The implementation is complete only when all of these are true:

1. `uv sync --all-extras` succeeds.
2. `uv run ruff format --check .` succeeds.
3. `uv run ruff check .` succeeds.
4. `uv run mypy src` succeeds.
5. `uv run pytest` succeeds.
6. `uv build` creates valid wheel and sdist.
7. Plain `googlekit` imports without service extras.
8. Every individual service extra installs independently.
9. `[all]` installs every service.
10. Missing services produce friendly MissingExtraError messages.
11. OAuth token refresh is tested.
12. Service-account construction is tested.
13. ADC construction is tested.
14. Scope aggregation is tested.
15. Pagination is lazy and tested.
16. Retry behavior is tested without real sleeping.
17. Errors are mapped into GoogleKit exceptions.
18. Large transfers stream rather than loading everything into memory.
19. Drive shared-drive operations are supported where applicable.
20. Calendar timezone handling is correct.
21. Docs UTF-16 index handling is tested.
22. Cross-service Drive export/share requirements are documented.
23. No secret values appear in logs.
24. Every example passes static validation.
25. Wheel installation works in a clean environment.
26. Documentation accurately matches the implemented API.
27. There are no placeholders in required features.

────────────────────────────────────────────────────────────────
23. IMPLEMENTATION PROCESS
────────────────────────────────────────────────────────────────

Work in controlled phases.

Phase 1:
- Research official sources
- Report findings
- Verify package-name status
- Finalize dependency choices
- Finalize scope matrix
- Show the complete project tree
- Explain any justified changes to the requested tree

Phase 2:
- Create pyproject.toml
- Create package core
- Create exceptions
- Create optional-extra loading
- Create authentication system
- Create tests for core/auth

Phase 3:
- Implement Google Drive completely
- Add unit tests
- Add examples
- Run checks

Phase 4:
- Implement Google Sheets completely
- Add unit tests
- Add examples
- Run checks

Phase 5:
- Implement Google Calendar completely
- Add unit tests
- Add examples
- Run checks

Phase 6:
- Implement Google Docs completely
- Add unit tests
- Add examples
- Run checks

Phase 7:
- Implement Google Slides completely
- Add unit tests
- Add examples
- Run checks

Phase 8:
- Add cross-service operations
- Add documentation
- Add CLI
- Add CI
- Add packaging tests

Phase 9:
- Run all validation
- Build wheel and sdist
- Install each extra in clean environments
- Produce final report

Do not dump the entire repository into one enormous response.

Create and edit actual project files.

After each phase:

1. List files created or changed.
2. Show commands executed.
3. Report test/lint/type-check results honestly.
4. Identify remaining work.
5. Continue automatically unless a genuine product decision requires approval.

Do not repeatedly ask for permission for routine technical choices.

Make sensible, researched decisions.

Never state that something works unless it was actually tested.

Begin now with Phase 1.