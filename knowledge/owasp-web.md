# OWASP Top 10 Web Application Security (2021)

The OWASP Top 10 is a standard awareness document for web application security.

---

## A01:2021 - Broken Access Control
Access control enforces policy such that users cannot act outside of their intended permissions.

**Common Vulnerabilities:**
- Violation of the principle of least privilege
- Bypassing access control checks by modifying the URL
- Permitting viewing or editing someone else's account
- Accessing API with missing access controls for POST, PUT and DELETE
- Elevation of privilege

**Testing:**
- Modify URL parameters
- Test horizontal access (access other users' resources)
- Test vertical access (elevate privileges)
- Check for missing access controls on sensitive endpoints

---

## A02:2021 - Cryptographic Failures
Previously known as Sensitive Data Exposure.

**Common Vulnerabilities:**
- Transmitting data in clear text
- Using old or weak cryptographic algorithms
- Using default crypto keys
- Not enforcing encryption

**Testing:**
- Check for sensitive data in transit (HTTPS)
- Verify encryption at rest
- Check algorithm strength (AES-256, RSA-2048+)
- Look for hardcoded keys

---

## A03:2021 - Injection
Injection flaws, such as SQL, NoSQL, OS command, LDAP.

**Common Vulnerabilities:**
- User supplied data not validated
- Dynamic queries or non-parameterized calls
- Hostile data used within ORM search parameters

**Testing:**
- Test all input fields with payloads
- SQLi: `' OR '1'='1`, `UNION SELECT`
- Command: `; ls -la`, `$(whoami)`
- LDAP: `*)(uid=*))(|(uid=*

---

## A04:2021 - Insecure Design
New category for 2021. Focus on design flaws.

**Common Vulnerabilities:**
- Missing security controls
- Business logic vulnerabilities
- Anti-automation missing

**Testing:**
- Understand business logic
- Test workflow bypasses
- Check for rate limiting
- Look for missing authorization

---

## A05:2021 - Security Misconfiguration
**Common Vulnerabilities:**
- Unnecessary features enabled
- Default accounts/passwords
- Error handling revealing information
- Upgraded systems missing security features
- Insecure server configurations

**Testing:**
- Check HTTP headers
- Test default credentials
- Review error messages
- Check for debug mode

---

## A06:2021 - Vulnerable and Outdated Components
**Common Vulnerabilities:**
- Using unsupported components
- Not knowing all component versions
- Not securing the dependencies

**Testing:**
- Check versions (nmap, wappalyzer)
- Use CVE databases
- Check for known vulnerabilities
- Review dependency tree

---

## A07:2021 - Identification and Authentication Failures
**Common Vulnerabilities:**
- Weak passwords
- Credential stuffing
- Session fixation
- Improper session handling

**Testing:**
- Test password policies
- Check session tokens (length, randomness)
- Test account lockout
- Check for session fixation

---

## A08:2021 - Software and Data Integrity Failures
**Common Vulnerabilities:**
- Insecure deserialization
- CI/CD pipeline vulnerabilities
- Update integrity issues

**Testing:**
- Check deserialization usage
- Review CI/CD config
- Verify update signing
- Check for unsigned updates

---

## A09:2021 - Security Logging and Monitoring Failures
**Common Vulnerabilities:**
- Insufficient logging
- Log injection
- Missing alert thresholds

**Testing:**
- Check what is logged
- Test log injection
- Verify alert mechanisms
- Check for event auditing

---

## A10:2021 - Server-Side Request Forgery (SSRF)
**Common Vulnerabilities:**
- Fetch remote resources without validation
- Cloud metadata exposure (169.254.169.254)
- Internal service access

**Testing:**
- Test URL parameters with:
  - `http://localhost`
  - `http://169.254.169.254`
  - `file:///etc/passwd`
- Check cloud metadata endpoints
- Probe internal services