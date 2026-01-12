"""Upsonic Shopping Agent with UCP Tools.

A shopping assistant that uses UCP (Universal Commerce Protocol) 
to browse products, manage carts, and complete purchases.
"""

from upsonic import Agent, Chat
from ucp_client import UCPAgentTools


# =============================================================================
# 1. SYSTEM PROMPT
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
# 2. CREATE AGENT
# =============================================================================

def create_agent(server_url: str) -> Agent:
    """Create shopping agent with UCP tools."""
    
    # Initialize UCP tools
    tools = UCPAgentTools(server_url)
    
    # Create agent
    agent = Agent(
        name="Shopping Assistant",
        model="openai/gpt-4o",
        system_prompt=SYSTEM_PROMPT
    )
    
    # Add UCP tools to agent
    agent.add_tools(tools)
    
    return agent


# =============================================================================
# 3. INTERACTIVE CHAT
# =============================================================================

async def chat_with_agent(agent: Agent):
    """Run interactive chat session."""
    
    chat = Chat(
        session_id="shopping_session",
        user_id="user_1",
        agent=agent
    )
    
    print("🛒 Shopping Assistant Ready!")
    print("Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print("Goodbye! 👋")
            break
        
        response = await chat.invoke(user_input)
        print(f"Assistant: {response}\n")


# =============================================================================
# 4. MAIN
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    # Server URL
    SERVER_URL = "http://localhost:8182"
    
    # Create agent
    agent = create_agent(SERVER_URL)
    
    # Run interactive chat
    asyncio.run(chat_with_agent(agent))
