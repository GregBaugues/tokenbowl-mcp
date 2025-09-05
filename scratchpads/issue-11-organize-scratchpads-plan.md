# Issue #11: Move Scratchpads into Scratchpad Directory

## GitHub Issue
https://github.com/GregBaugues/sleeper-mcp/issues/11

## Problem Statement
- Scratchpad files are currently stored directly in the project root directory
- Need to organize them in a dedicated `scratchpads/` directory for better project organization
- Update .claude/agents and .claude/commands configurations to ensure future scratchpads are stored in the new location

## Current State Analysis

### Existing Scratchpads
1. `scratchpad-issue-5-improve-docstrings.md` - Implementation plan for improving MCP tool docstrings
2. `scratchpad-issue-8-waiver-wire.md` - Implementation plan for waiver wire functionality

### Configuration Files
1. `.claude/agents/github-issue-planner.md` - Agent that creates scratchpads (line 40: specifies filename format)
2. `.claude/commands/issue.md` - Command that uses the github-issue-planner agent

## Implementation Plan

### Task 1: Create Scratchpads Directory
- **Description**: Create a new `scratchpads/` directory in the project root
- **Implementation**: Simple directory creation
- **Files**: None to modify
- **Testing**: Verify directory exists

### Task 2: Move Existing Scratchpads
- **Description**: Move all existing scratchpad files to the new directory
- **Implementation**: 
  - Move `scratchpad-issue-5-improve-docstrings.md` → `scratchpads/scratchpad-issue-5-improve-docstrings.md`
  - Move `scratchpad-issue-8-waiver-wire.md` → `scratchpads/scratchpad-issue-8-waiver-wire.md`
  - Move this planning document `issue-11-organize-scratchpads-plan.md` → `scratchpads/issue-11-organize-scratchpads-plan.md`
- **Files**: 3 files to move
- **Testing**: Verify files exist in new location and not in old location

### Task 3: Update GitHub Issue Planner Agent
- **Description**: Update the agent to save scratchpads in the new directory
- **Implementation**: 
  - Modify line 40 to prepend `scratchpads/` to the filename format
  - Update any references in the documentation to mention the scratchpads directory
- **Files**: `.claude/agents/github-issue-planner.md`
- **Testing**: Run the agent to create a test scratchpad and verify it's created in the right location

### Task 4: Update Issue Command (if needed)
- **Description**: Check if the issue command needs updates for the new scratchpad location
- **Implementation**: Review the command file for any hardcoded references
- **Files**: `.claude/commands/issue.md`
- **Testing**: Run the issue command workflow

### Task 5: Add .gitkeep (optional)
- **Description**: Add a .gitkeep file to ensure the scratchpads directory is tracked in git
- **Implementation**: Create empty `.gitkeep` file in scratchpads/ directory
- **Files**: `scratchpads/.gitkeep`
- **Testing**: Verify git tracks the directory

## Risk Assessment
- **Low Risk**: This is a simple organizational change with minimal impact
- **Mitigation**: Keep old file references in git history for reference

## Testing Strategy
1. Create the directory structure
2. Move existing files
3. Test the github-issue-planner agent creates new scratchpads in the correct location
4. Verify the issue command continues to work correctly

## Success Criteria
- All existing scratchpad files are moved to `scratchpads/` directory
- Future scratchpads created by the github-issue-planner agent are automatically saved in the new directory
- The issue command workflow continues to function correctly
- Project structure is cleaner and more organized

## Estimated Complexity
- **Overall**: Low
- **Task 1**: Trivial
- **Task 2**: Trivial
- **Task 3**: Low (simple path update)
- **Task 4**: Low (verification mostly)
- **Task 5**: Trivial