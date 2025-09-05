# Implementation Plan: Move League ID to Environment Variable
**Issue #12**: https://github.com/GregBaugues/sleeper-mcp/issues/12

## Problem Statement
The league ID `1266471057523490816` is currently hardcoded in the codebase. We need to move it to an environment variable named `SLEEPER_LEAGUE_ID` for better configurability.

## Files Affected
Based on the codebase search, the following files need to be updated:

### Core Implementation
1. **sleeper_mcp.py**: 
   - Line 28: `LEAGUE_ID = "1266471057523490816"`
   - Line 41: Comment mentioning hardcoded league ID

### Documentation
2. **README.md**: 
   - Line 26: Mentions league ID in requirements
   - Line 295: Note about hardcoded league ID

3. **CLAUDE.md**: 
   - Line 7: Mentions hardcoded league ID
   - Line 100: Mentions hardcoded LEAGUE_ID constant

### Testing
4. **tests/test_integration.py**: 
   - Line 29: Assertion checking for hardcoded league ID

5. **tests/test_sleeper_mcp.py**: 
   - Line 14: Mock data with league ID
   - Line 85: Test assertion with hardcoded ID
   - Line 244: Mock draft data with league ID
   - Line 262: Test assertion with league ID

6. **tests/conftest.py**: 
   - Line 48: Returns hardcoded league ID

### Deployment
7. **render.yaml**: 
   - Need to add SLEEPER_LEAGUE_ID environment variable

## Implementation Steps

### Step 1: Update sleeper_mcp.py
- Import os module
- Replace hardcoded LEAGUE_ID with environment variable
- Add fallback to current league ID for backward compatibility
- Update docstrings

### Step 2: Update tests
- Modify tests to use environment variable
- Keep test league ID as a constant in conftest.py
- Update test assertions to be environment-aware

### Step 3: Update documentation
- README.md: Add SLEEPER_LEAGUE_ID to environment variables section
- CLAUDE.md: Update references to reflect environment variable usage

### Step 4: Update deployment configuration
- render.yaml: Add SLEEPER_LEAGUE_ID to environment variables

### Step 5: Testing
- Test locally with environment variable set
- Test without environment variable (fallback behavior)
- Run full test suite

## Environment Variable Design
```python
# sleeper_mcp.py
import os

# Get league ID from environment variable with fallback to Token Bowl
LEAGUE_ID = os.environ.get("SLEEPER_LEAGUE_ID", "1266471057523490816")
```

## Backward Compatibility
- Default to Token Bowl league ID if environment variable is not set
- This ensures existing deployments continue to work without configuration changes

## Testing Strategy
1. Set SLEEPER_LEAGUE_ID environment variable in test environment
2. Verify all existing tests pass
3. Test with different league IDs
4. Test fallback behavior when env var is not set