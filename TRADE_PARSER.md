# Fantasy Football Trade Proposal Parser

A Python script that uses the Claude SDK to automatically extract player names from fantasy football trade proposals.

## Features

- Extracts two lists from trade proposals:
  - Players being proposed to **receive**
  - Players being proposed to **give**
- Uses Claude's language understanding to parse natural language trade offers
- Returns results as both human-readable output and JSON

## Setup

1. **Install dependencies** (already included in project):
   ```bash
   uv sync
   ```

2. **Set up API key**:
   - Get an API key from [Anthropic Console](https://console.anthropic.com/)
   - Add to `.env` file:
     ```
     ANTHROPIC_API_KEY=your_key_here
     ```

## Usage

### Command Line

```bash
# Basic usage
uv run python parse_trade_proposal.py "I'll trade you Tyreek Hill for Justin Jefferson"

# With explicit API key
uv run python parse_trade_proposal.py --api-key sk-ant-... "Trade proposal text"
```

### Python Script

```python
from parse_trade_proposal import parse_trade_proposal
from anthropic import Anthropic

client = Anthropic()  # Uses ANTHROPIC_API_KEY from environment
message = "I'll give you Davante Adams and Travis Etienne for CeeDee Lamb"

players_to_receive, players_to_give = parse_trade_proposal(client, message)
print(f"Receive: {players_to_receive}")
print(f"Give: {players_to_give}")
```

## Examples

Run the example script to see various trade proposals:
```bash
uv run python example_trade_parse.py
```

### Sample Trade Proposals

1. **Simple 1-for-1**: "I'll trade you Tyreek Hill for Justin Jefferson"
   - Receive: ["Justin Jefferson"]
   - Give: ["Tyreek Hill"]

2. **Multiple players**: "Give me CeeDee Lamb and I'll send you Davante Adams and Travis Etienne"
   - Receive: ["CeeDee Lamb"]
   - Give: ["Davante Adams", "Travis Etienne"]

3. **Complex proposal**: "Would you do my Stefon Diggs, Breece Hall, and George Pickens for your CeeDee Lamb and Josh Jacobs?"
   - Receive: ["CeeDee Lamb", "Josh Jacobs"]
   - Give: ["Stefon Diggs", "Breece Hall", "George Pickens"]

## Output Format

The script returns:
- **Console output**: Human-readable lists of players
- **JSON output**: Structured data for programmatic use
  ```json
  {
    "receiving": ["Player Name 1", "Player Name 2"],
    "giving": ["Player Name 3", "Player Name 4"]
  }
  ```