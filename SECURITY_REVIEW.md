## Security Review (2025-12-13)

### What we checked
- Application configuration (SECRET_KEY exposure, DEBUG/ALLOWED_HOSTS, security middleware, cookie flags, HTTPS protections).
- Authentication and access control on user-facing and admin endpoints.
- Input validation, output encoding, CSRF protections, and session handling.
- File upload handling and storage for assessment attachments.
- Dependency and supply-chain posture (requirements file, framework versions).
- Frontend attack surface (DOM updates, template escaping, language/theme scripts, CSP/headers).
- Logging/error handling and operational safeguards (rate limiting, auditability, backups).
- Data protection at rest/in transit (database choice, encryption settings).
- Testing and deployment readiness for security controls.

### Current state (observations)
- **Configuration:** SECRET_KEY is committed to source control, DEBUG is enabled, and ALLOWED_HOSTS is empty, which are unsafe defaults for production. SECURE/HSTS/HTTPS-related settings and secure cookie flags are not configured.
- **Authentication/Authorization:** Core assessment and survey views are publicly accessible without authentication or authorization; only the Django admin is gated. There is no role-based access control around assessment creation/run endpoints.
- **Input handling:** CSRF middleware is enabled and templates auto-escape by default. Assessment AJAX calls include the CSRF token. JSON payloads are minimally validated; option IDs are coerced to ints but lack deeper validation/throttling.
- **File uploads:** AssessmentFile uses a FileField without content-type/size validation or storage segregation; upload path helper indirection is present but no sanitization or AV scanning is applied.
- **Dependency posture:** `requirements.txt` references local build artifacts and cannot be installed here; Django is missing in the environment, preventing tests from running. Dependency provenance/pinning is unclear.
- **Frontend:** Theme/language scripts rely on `innerText` and avoid unsanitized HTML. Server-rendered fragments are injected via `innerHTML`; they rely on backend escaping. No Content Security Policy or other browser hardening headers are configured.
- **Data protection/ops:** SQLite is used by default with no encryption. No settings for secure cookies, session expiry, rate limiting, or audit logging are present.
- **Testing status:** `python manage.py test` fails because Django is not installed (requirements file references local build paths).

### Future improvements (prioritized)
- Move secrets (SECRET_KEY, database creds) and environment-specific settings out of source control; set DEBUG=False and define ALLOWED_HOSTS for deployed environments.
- Enable security headers and HTTPS hardening (SECURE_SSL_REDIRECT, HSTS, SECURE_REFERRER_POLICY, CSP, X-Content-Type-Options, X-Frame-Options), and mark cookies `Secure`/`HttpOnly`/`SameSite`.
- Introduce authentication/authorization for assessment and survey routes; add role-based permissions for authors, reviewers, and respondents. Protect admin with MFA and IP allowlists where possible.
- Validate and sanitize user-controlled data paths: enforce option ID ownership, add rate limiting/throttling on POST endpoints, and add stricter JSON schema validation.
- Harden file uploads with size/type checks, randomized storage paths, virus scanning, and signed download URLs; consider segregated storage buckets with least privilege.
- Fix dependency supply chain: replace local path references in `requirements.txt` with pinned versions from trusted indexes, add dependency scanning, and automate updates.
- Add CSP and other frontend protections; avoid injecting server strings via `innerHTML` when they may contain user-generated HTML, or sanitize before insertion.
- Migrate to a production-grade database with encryption at rest and backups; configure database credentials and rotations via environment variables.
- Add audit logging for admin and critical actions, operational monitoring, and backup/restore runbooks.
- Expand automated tests to cover security controls (authz rules, CSRF on JSON endpoints, file upload validation) and ensure the test suite runs in CI with a reproducible dependency set.
