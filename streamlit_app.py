"""Upsonic Shopping Agent - Streamlit UI

A simple Streamlit interface for the shopping assistant.
"""

import streamlit as st
import asyncio
import json
import httpx
from functools import wraps
from upsonic import Agent, Task, Chat
from upsonic.agent.events import ToolCallEvent, ToolResultEvent
from ucp_client import UCPAgentTools


# =============================================================================
# DEBUG HTTP LOGGING
# =============================================================================

# Store original httpx request method
_original_request = httpx.AsyncClient.request

async def _debug_request(self, method, url, **kwargs):
    """Wrapper to log HTTP requests and responses."""
    print("\n" + "🔵"*35)
    print(f"📤 HTTP {method} → {url}")
    if kwargs.get("json"):
        print(f"📦 REQUEST BODY:")
        print(json.dumps(kwargs["json"], indent=2, default=str))
    print("🔵"*35)
    
    try:
        response = await _original_request(self, method, url, **kwargs)
        print("\n" + "🟢"*35)
        print(f"📥 HTTP {response.status_code} ← {url}")
        try:
            resp_json = response.json()
            print(f"📦 RESPONSE BODY:")
            print(json.dumps(resp_json, indent=2, default=str))
        except:
            print(f"📦 RESPONSE TEXT: {response.text[:500]}")
        print("🟢"*35 + "\n")
        return response
    except Exception as e:
        print("\n" + "🔴"*35)
        print(f"❌ HTTP ERROR: {e}")
        print("🔴"*35 + "\n")
        raise

# Monkey-patch httpx to add debug logging
httpx.AsyncClient.request = _debug_request


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
    tools = UCPAgentTools(server_url, debug=True)
    agent = Agent(
        name="Shopping Assistant",
        model="openai/gpt-4o",
        system_prompt=SYSTEM_PROMPT
    )
    agent.add_tools(tools)
    return agent


def create_chat(agent: Agent) -> Chat:
    """Create a chat session with conversation memory."""
    return Chat(
        session_id="streamlit_shopping_session",
        user_id="streamlit_user",
        agent=agent
    )


def extract_tool_calls_from_messages(messages, start_index: int):
    """Extract tool calls from chat messages after a given index."""
    tool_calls = []
    
    for msg in messages[start_index:]:
        # Check if message has tool_calls attribute (assistant messages with tool use)
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                # Upsonic uses dict format: {'tool_name': ..., 'tool_call_id': ..., 'args': ...}
                if isinstance(tc, dict):
                    tool_call_info = {
                        "id": tc.get('tool_call_id', str(len(tool_calls))),
                        "name": tc.get('tool_name', 'unknown'),
                        "args": tc.get('args', {}),
                        "result": None
                    }
                else:
                    # Fallback for object-style tool calls
                    tc_id = getattr(tc, 'tool_call_id', getattr(tc, 'id', str(len(tool_calls))))
                    tc_name = getattr(tc, 'tool_name', getattr(tc, 'name', 'unknown'))
                    tc_args = getattr(tc, 'args', getattr(tc, 'arguments', {}))
                    tool_call_info = {
                        "id": tc_id,
                        "name": tc_name,
                        "args": tc_args,
                        "result": None
                    }
                tool_calls.append(tool_call_info)
        
        # Check if this is a tool result message
        if hasattr(msg, 'role') and msg.role == 'tool':
            tool_call_id = getattr(msg, 'tool_call_id', None)
            result = getattr(msg, 'content', None)
            # Find matching tool call and add result
            for tc in tool_calls:
                if tc["id"] == tool_call_id:
                    tc["result"] = result
                    break
            # If no match found but we have tool calls without results, add to last one
            if result and tool_calls and tool_calls[-1]["result"] is None:
                tool_calls[-1]["result"] = result
    
    return tool_calls


async def run_agent_with_tools(chat: Chat, prompt: str):
    """Run agent via chat and capture tool calls."""
    tool_calls = []
    response_text = ""
    
    # Get message count before invoke to know where new messages start
    messages_before = len(chat.all_messages) if hasattr(chat, 'all_messages') else 0
    
    # Try streaming first, fall back to invoke if not supported
    if hasattr(chat, 'stream_async'):
        # Use streaming to capture tool events
        stream_result = await chat.stream_async(prompt)
        
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
    else:
        # Fallback to invoke without streaming tool events
        response_text = await chat.invoke(prompt)
        
        # Extract tool calls from message history
        if hasattr(chat, 'all_messages'):
            tool_calls = extract_tool_calls_from_messages(chat.all_messages, messages_before)
    
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
    st.session_state.chat = None
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
            st.session_state.chat = create_chat(st.session_state.agent)
            st.rerun()

else:
    # Connected - show chat interface
    agent = st.session_state.agent
    chat = st.session_state.chat
    
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
            st.session_state.chat = None
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            # Reset chat session for new conversation
            st.session_state.chat = create_chat(st.session_state.agent)
            st.session_state.messages = []
            st.rerun()
    
    # Display chat history from session state
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # Show tool calls if any (for assistant messages)
            if msg["role"] == "assistant" and msg.get("tool_calls"):
                with st.expander("🔧 Tool Calls", expanded=False):
                    for tc in msg["tool_calls"]:
                        st.code(f"📤 {tc['name']}({tc.get('args', '')})", language=None)
                        if tc.get("result"):
                            result_str = str(tc["result"])[:500]
                            if len(str(tc["result"])) > 500:
                                result_str += "..."
                            st.success(f"📥 {result_str}")
            st.markdown(msg["content"])
    
    # Chat input with default placeholder
    prompt = st.chat_input("Show me available products")
    
    # Process new message
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Show spinner while processing
        with st.spinner("🤔 Thinking..."):
            response, tool_calls = asyncio.run(run_agent_with_tools(chat, prompt))
        
        # Add assistant message to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "tool_calls": tool_calls
        })
        
        # Rerun to display all messages from the history loop only
        st.rerun()
