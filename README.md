# UCP Shopping Agent

## Installation

```bash
uv venv
uv pip install "ucp-client[server]==0.0.5"
uv pip install upsonic==0.69.3
uv pip install streamlit
```

## Usage

**Terminal 1** - Start the mock server:
```bash
uv run ucp mockup_server
```

**Terminal 2** - Run the agent (CLI):
```bash
uv run upsonic_shopping_agent.py
```

## Streamlit UI

You can also use the Streamlit web interface:

```bash
uv run streamlit run streamlit_app.py
```

Then open http://localhost:8501 in your browser.
