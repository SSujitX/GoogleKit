## [0.0.2] - 2026-07-12

### Changed

- README authentication setup: all three methods (ADC, service account, OAuth) now include **Step 2: Enable APIs** with links to [APIs & Services → Library](https://console.cloud.google.com/apis/library) and direct enable links for Drive, Sheets, Calendar, Docs, and Slides
- OAuth setup docs updated for Google’s **Google Auth Platform** UI ([Branding](https://console.cloud.google.com/auth/branding), [Audience](https://console.cloud.google.com/auth/audience), [Clients](https://console.cloud.google.com/auth/clients) → Desktop app), with the older Credentials / consent-screen path noted as a fallback
- Publish workflow run title shows `PyPI publish vX.Y.Z` instead of the commit subject
