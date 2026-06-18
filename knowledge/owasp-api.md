# OWASP API Security Top 10 (2023)

---

## API1:2023 - Broken Object Level Authorization (BOLA)
APIs tend to expose endpoints that handle object identifiers, creating a wide attack surface of Object Level Access Control issues.

**Description:**
- APIs expose endpoints that handle object identifiers
- No verification that the user has access to the requested object
- Allows attackers to access unauthorized resources

**Testing:**
- Enumerate identifying parameters (id, user_id, object_id)
- Test IDOR vulnerabilities
- Test horizontal privilege escalation
- Test vertical privilege escalation

**Example:** `GET /api/users/123` returns user 123's data. Can you access other users?

---

## API2:2023 - Broken Authentication
Authentication mechanisms are often implemented incorrectly.

**Description:**
- Weak password policies
- Credential stuffing supported
- Token-based auth can be compromised
- Lack of account lockout

**Testing:**
- Test login brute force
- Check token validity
- Test password reset flows
- Check for account enumeration

---

## API3:2023 - Broken Object Property Level Authorization
Lack of or improper authorization validation at the object property level.

**Description:**
- Excessive data exposure (returning all fields)
- Mass assignment (allowing untrusted users to set sensitive fields)
- Lack of proper field-level authorization

**Testing:**
- Analyze API responses for data exposure
- Test PUT/POST/PATCH for mass assignment
- Check authorization on individual fields

---

## API4:2023 - Unrestricted Resource Consumption
APIs don't restrict client interactions.

**Description:**
- No rate limiting
- No timeout limits
- Large payload sizes accepted
- Can lead to DoS

**Testing:**
- Send many requests rapidly
- Send large payloads
- Check timeout handling
- Test resource exhaustion

---

## API5:2023 - Broken Function Level Authorization
Complex access control policies lead to authorization flaws.

**Description:**
- Confusing admin/user endpoints
- No clear separation between functions
- Allows users to access admin functions

**Testing:**
- Map all endpoints
- Test admin endpoints as regular user
- Check for horizontal privilege escalation
- Test force browsing

---

## API6:2023 - Unrestricted Access to Sensitive Business Flows
APIs expose sensitive business flows without compensating controls.

**Description:**
- No rate limiting on sensitive operations
- No bot detection
- Allows automated attacks (scalping, fake accounts)

**Testing:**
- Test for automated account creation
- Test purchase/booking flows
- Check for rate limiting bypass
- Look for business logic abuse

---

## API7:2023 - Server-Side Request Forgery (SSRF)
APIs fetching remote resources without validating user-supplied URIs.

**Description:**
- API fetches from user-provided URL
- No validation of the target
- Can be used to access internal services

**Testing:**
- Test URL parameters with internal IPs
- Test cloud metadata endpoints
- Test for SSRF in file uploads
- Probe internal network

---

## API8:2023 - Security Misconfiguration
APIs and supporting systems have security misconfigurations.

**Description:**
- Unnecessary HTTP methods
- Missing security headers
- CORS misconfiguration
- Verbose error messages

**Testing:**
- Check HTTP headers
- Test CORS configuration
- Check for debug mode
- Analyze error responses

---

## API9:2023 - Improper Inventory Management
Outdated components and poor API documentation.

**Description:**
- Using outdated API versions
- Missing documentation
- Undocumented endpoints exposed
- No deprecation strategy

**Testing:**
- Enumerate API versions
- Look for undocumented endpoints
- Check for .git exposure
- Test for debug endpoints

---

## API10:2023 - Unsafe Consumption of APIs
APIs trusting data from third-party APIs without validation.

**Description:**
- Insufficient validation of third-party data
- Lack of security controls on integrations
- Integration with insecure services

**Testing:**
- Analyze third-party integrations
- Check how external data is processed
- Test for injection via API responses
- Verify data sanitization