# UCP Shopping Agent

## Installation

```bash
uv venv
uv pip install "ucp-client[server]==0.0.5"
uv pip install upsonic==0.69.3
```

## Usage

**Terminal 1** - Start the mock server:
```bash
uv run ucp mockup_server
```

**Terminal 2** - Run the agent:
```bash
uv run upsonic_shopping_agent.py
```
