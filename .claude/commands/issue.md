Follow these steps to analyze and fix the GitHub issue: $ARGUMENTS. 

# PLAN
- Use a subagent to plan the issue's impelmentation. 


# CREATE
- Create a new branch for the issue
- Solve the issue in small, manageable steps, according to your plan. 
- Commit your changes after each step. 
- When finished, write tests to cover the work you did. Follow the testing guideines in CLAUDE.md


# STAGE
- Open a PR. 

# REVIEW
- Request a PR from Sandy Metz
- If the review passes, move on. 
- If the review does not pass, fix the code, stage, and review until it does

# LEARN 
- pass the context of the conversation to the claude.md updater 
- once it has modified claude.md, add it changes to the PR. 

# DEPLOY
- make any final commits and pushes necessary to deploy
- wait until the CI checks have finished running. 
- if all the CI on the PR pass, merge it. 
- if not, fix it. 



Remember to use the GitHub CLI (`gh`) for all Github-related tasks. 