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

<img width="1800" height="981" alt="Screenshot 2026-01-12 at 4 32 16 PM" src="https://github.com/user-attachments/assets/596796a5-9fc0-471f-8c12-dd653537deb0" />

