"""Upsonic Shopping Agent - Streamlit UI

A simple Streamlit interface for the shopping assistant.
"""

import streamlit as st
import asyncio
from upsonic import Agent, Task
from upsonic.agent.events import ToolCallEvent, ToolResultEvent
from ucp_client import UCPAgentTools


# =============================================================================
# CONFIG
# =============================================================================

SYSTEM_PROMPT = """You are a helpful shopping assistant.

You have access to UCP shopping tools:
- get_available_products() - See available products
- get_available_discount_codes() - See discount codes
- get_your_user() - Get user info and saved addresses
- discover_merchant() - Get merchant and payment info
- create_cart() - Create a shopping cart
- apply_discount() - Apply discount code to cart
- set_shipping_address() - Set delivery address
- complete_purchase() - Complete the checkout

WORKFLOW:
1. Help user find products
2. Create cart when ready to buy
3. Ask about shipping address
4. Ask about discount codes
5. Confirm before completing purchase

Always be friendly and guide the user step by step."""


# =============================================================================
# AGENT SETUP
# =============================================================================

def create_agent(server_url: str) -> Agent:
    """Create shopping agent with UCP tools."""
    tools = UCPAgentTools(server_url)
    agent = Agent(
        name="Shopping Assistant",
        model="openai/gpt-4o",
        system_prompt=SYSTEM_PROMPT
    )
    agent.add_tools(tools)
    return agent


async def run_agent_with_tools(agent: Agent, prompt: str):
    """Run agent and capture tool calls using streaming."""
    tool_calls = []
    response_text = ""
    
    # Use streaming to capture tool events
    stream_result = await agent.stream_async(Task(description=prompt))
    
    async with stream_result:
        async for event in stream_result.stream_events():
            # Capture tool calls
            if isinstance(event, ToolCallEvent):
                tool_calls.append({
                    "id": event.tool_call_id,
                    "name": event.tool_name,
                    "args": event.tool_args,
                    "result": None
                })
            # Capture tool results
            elif isinstance(event, ToolResultEvent):
                # Find matching tool call and add result
                for tc in tool_calls:
                    if tc["id"] == event.tool_call_id:
                        tc["result"] = event.result_preview or event.result
                        break
    
    # Get final response
    response_text = stream_result.get_accumulated_text()
    
    return response_text, tool_calls


# =============================================================================
# STREAMLIT UI
# =============================================================================

st.set_page_config(
    page_title="Upsonic Agent with UCP",
    page_icon="🛒",
    layout="centered"
)

# Logo and title
st.image("media/logo.png", width=60)
st.title("Upsonic Agent with UCP")
st.caption("Shopping assistant powered by Upsonic & UCP")

# =============================================================================
# SERVER URL INPUT
# =============================================================================

if "server_url" not in st.session_state:
    st.session_state.server_url = None
    st.session_state.agent = None
    st.session_state.messages = []

if st.session_state.server_url is None:
    st.info("👋 Welcome! Please enter the UCP Server URL to get started.")
    
    with st.form("server_form"):
        url_input = st.text_input(
            "UCP Server URL",
            value="http://localhost:8182",
            help="Enter the URL of your UCP server"
        )
        submitted = st.form_submit_button("🚀 Connect", use_container_width=True)
        
        if submitted and url_input:
            st.session_state.server_url = url_input
            st.session_state.agent = create_agent(url_input)
            st.rerun()

else:
    # Connected - show chat interface
    agent = st.session_state.agent
    
    # Sidebar
    with st.sidebar:
        st.success(f"✅ Connected to:\n`{st.session_state.server_url}`")
        
        st.divider()
        
        st.header("ℹ️ Info")
        st.write("This assistant helps you with shopping:")
        st.markdown("""
        - Browse products
        - Create cart
        - Apply discount codes
        - Complete purchase
        """)
        
        st.divider()
        
        if st.button("🔌 Disconnect", use_container_width=True):
            st.session_state.server_url = None
            st.session_state.agent = None
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Quick suggestions (show only when no messages)
    if not st.session_state.messages:
        st.markdown("**Quick actions:**")
        suggestions = [
            "🛍️ Show me available products",
            "🏷️ What discount codes are available?",
            "👤 Show my user info",
            "🏪 Tell me about the merchant"
        ]
        
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    st.session_state.pending_message = suggestion
                    st.rerun()
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # Show tool calls if any
            if msg["role"] == "assistant" and msg.get("tool_calls"):
                with st.expander("🔧 Tool Calls", expanded=False):
                    for tc in msg["tool_calls"]:
                        st.code(f"📤 {tc['name']}({tc.get('args', '')})", language=None)
                        if tc.get("result"):
                            result_str = str(tc["result"])[:500]
                            if len(str(tc["result"])) > 500:
                                result_str += "..."
                            st.success(f"📥 {result_str}")
            st.write(msg["content"])
    
    # Check for pending message from quick suggestions
    prompt = None
    if "pending_message" in st.session_state and st.session_state.pending_message:
        prompt = st.session_state.pending_message
        st.session_state.pending_message = None
    
    # Chat input
    if not prompt:
        prompt = st.chat_input("Type your message...")
    
    if prompt:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get assistant response with tool calls
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, tool_calls = asyncio.run(run_agent_with_tools(agent, prompt))
            
            # Show tool calls if any
            if tool_calls:
                with st.expander("🔧 Tool Calls", expanded=True):
                    for tc in tool_calls:
                        st.code(f"📤 {tc['name']}({tc.get('args', '')})", language=None)
                        if tc.get("result"):
                            result_str = str(tc["result"])[:500]
                            if len(str(tc["result"])) > 500:
                                result_str += "..."
                            st.success(f"📥 {result_str}")
            
            st.write(response)
        
        # Save assistant message with tool calls
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "tool_calls": tool_calls
        })
