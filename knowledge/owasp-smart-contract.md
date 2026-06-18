# OWASP Smart Contract Top 10 (2026)

---

## SC01:2026 - Access Control Vulnerabilities
Access control flaws allow unauthorized users to invoke privileged functions.

**Description:**
- Missing access modifiers
- Incorrectly configured access
- Privilege escalation
- Admin function exposure

**Testing:**
- Check all functions for access modifiers
- Test admin functions as non-admin
- Look for callable by anyone
- Check upgradeability implications

**Example Vulnerabilities:**
```solidity
function adminOnly() public { ... }  // Missing access modifier
function withdraw() public { ... }   // Anyone can withdraw
```

---

## SC02:2026 - Business Logic Vulnerabilities
Flaws in business logic that bypass low-level checks.

**Description:**
- Logic errors in calculations
- Race condition exploitation
- Front-running vulnerability
- Workflow bypasses

**Testing:**
- Analyze business logic thoroughly
- Test edge cases
- Check for reentrancy
- Test flash loan interactions

---

## SC03:2026 - Price Oracle Manipulation
Manipulation of price oracle data.

**Description:**
- Using centralized oracles
- Price feed manipulation
- Flash loan attacks on oracles
- Stale price data

**Testing:**
- Analyze oracle usage
- Check for TWAP
- Test price manipulation
- Check oracle update frequency

---

## SC04:2026 - Flash Loan-Facilitated Attacks
Attacks using flash loans to manipulate markets.

**Description:**
- Large price swings in single transaction
- Oracle manipulation
- Liquidation attacks
- Governance manipulation

**Testing:**
- Simulate flash loan attacks
- Check for proper oracle usage
- Test liquidation logic
- Verify governance checks

---

## SC05:2026 - Lack of Input Validation
Missing validation of user input.

**Description:**
- No bounds checking
- Missing zero-address checks
- Integer overflow
- Unvalidated external calls

**Testing:**
- Test all input parameters
- Check zero-address validation
- Test boundary conditions
- Fuzz input parameters

---

## SC06:2026 - Unchecked External Calls
Failure to check return values of external calls.

**Description:**
- send() without check
- Low-level calls ignored
- Missing error handling
- Revert DoS

**Testing:**
- Check all external calls
- Verify return value handling
- Test reentrancy protection
- Check for .call{value:...}()

---

## SC07:2026 - Arithmetic Errors
Mathematical errors in contract logic.

**Description:**
- Integer overflow/underflow
- Rounding errors
- Precision loss
- Incorrect calculations

**Testing:**
- Use SafeMath or Solidity 0.8+
- Test boundary values
- Check arithmetic operations
- Verify calculation logic

---

## SC08:2026 - Reentrancy Attacks
Calling external contracts before state updates.

**Description:**
- Cross-function reentrancy
- Cross-contract reentrancy
- DAO-style attacks
- State modification after external call

**Testing:**
- Check all external calls
- Use checks-effects-interactions
- Implement reentrancy guards
- Test with malicious contracts

---

## SC09:2026 - Integer Overflow and Underflow
Integer operations exceeding bounds.

**Description:**
- Using older Solidity (<0.8)
- Unsigned integers going negative
- Overflow in calculations
- Underflow in loops

**Testing:**
- Check Solidity version
- Use SafeMath in older versions
- Test with extreme values
- Fuzz arithmetic operations

---

## SC10:2026 - Proxy & Upgradeability Vulnerabilities
Flaws in upgradeable proxy patterns.

**Description:**
- Storage collisions
- Uninitialized proxy
- Upgradeable contract vulnerabilities
- Delegatecall vulnerabilities

**Testing:**
- Analyze proxy implementation
- Check storage layout
- Verify initialization
- Test upgrade mechanism