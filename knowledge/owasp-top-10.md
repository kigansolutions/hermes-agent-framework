# OWASP Top 10 (2021)

## A01:2021 - Broken Access Control
- Users acting outside their intended permissions
- Vertical privilege escalation
- Horizontal privilege escalation
- IDOR (Insecure Direct Object Reference)
- Bypass access control checks

**Testing:**
- Modify URL parameters
- Test horizontal access (access other users' resources)
- Test vertical access (elevate privileges)
- Check for missing access controls on sensitive endpoints

## A02:2021 - Cryptographic Failures
- Sensitive data exposure
- Weak encryption algorithms
- Missing encryption
- Default crypto keys

**Testing:**
- Check for sensitive data in transit
- Verify encryption at rest
- Check algorithm strength
- Look for hardcoded keys

## A03:2021 - Injection
- SQL Injection
- NoSQL Injection
- OS Command Injection
- LDAP Injection
- Expression Language Injection

**Testing:**
- Test all input fields
- Use payloads: `' OR '1'='1`, `; ls -la`, `${7*7}`

## A04:2021 - Insecure Design
- Missing security controls
- Business logic vulnerabilities
- Anti-automation missing

**Testing:**
- Understand business logic
- Test workflow bypasses
- Check for rate limiting

## A05:2021 - Security Misconfiguration
- Unnecessary features enabled
- Default accounts/passwords
- Error handling revealing information
- Upgraded systems missing security features

**Testing:**
- Check headers
- Test default credentials
- Review error messages

## A06:2021 - Vulnerable Components
- Outdated software
- Unsupported components
- Unpatched vulnerabilities

**Testing:**
- Check versions
- Use CVE databases
- Check for known vulnerabilities

## A07:2021 - Authentication Failures
- Weak passwords
- Credential stuffing
- Session fixation
- Improper session handling

**Testing:**
- Test password policies
- Check session tokens
- Test account lockout

## A08:2021 - Software and Data Integrity Failures
- Insecure deserialization
- CI/CD pipeline vulnerabilities
- Update integrity issues

**Testing:**
- Check deserialization
- Review CI/CD config
- Verify update signing

## A09:2021 - Security Logging Failures
- Insufficient logging
- Log injection
- Missing alert thresholds

**Testing:**
- Check what is logged
- Test log injection
- Verify alert mechanisms

## A10:2021 - Server-Side Request Forgery (SSRF)
- Fetch remote resources without validation
- Cloud metadata exposure
- Internal service access

**Testing:**
- Test URL parameters
- Check cloud metadata endpoints
- Probe internal services