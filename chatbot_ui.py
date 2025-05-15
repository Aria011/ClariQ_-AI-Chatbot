import streamlit as st
from chatbot import AIChatbot  
import os

st.set_page_config(page_title="ClariQ", page_icon="🤖", layout="wide")    

st.markdown("""
<style>
    html, body {
        overflow-y :hidden;
    }
    * Ensure content fits without scrolling */
    .main .block-container {
        max-height: calc(100vh - 200px);  /* Adjust based on your header/footer height */
        overflow-y: auto;  /* Allows scrolling within container if needed */
    }
            
    h1 {
        text-align: center;
        margin-top: 0;
    }
    .stMarkdown p {
        text-align: center;
        margin-bottom: 1rem;
    }
    /* Adjust chat container height */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
        height: calc(100vh - 250px);  /* Adjust based on your layout */
        overflow-y: auto;
    }
    
    .main .block-container {
        max-width: 800px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
   
    .stChatInput {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        max-width: 800px;
    }
    
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
        margin: 0 auto;
        width: 50%;
        max-width: 600px;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 12px;
        border-radius: 15px 15px 0 15px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .bot-message {
        background-color: #f5f5f5;
        padding: 12px;
        border-radius: 15px 15px 15px 0;
        margin: 8px 0;
        max-width: 80%;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    .chat-container {
        height: 70vh;
        overflow-y: auto;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #fafafa;
    }
    .custom-container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #fafafa;
    border-radius: 10px;
    border: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

st.title(" ClariQ ")
st.caption("Your intelligent assistant for clear, fast, and reliable conversations.")

@st.cache_resource
def load_chatbot():
    return AIChatbot()

chatbot = load_chatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

col1, col2, col3 = st.columns([1,5,1])

with col2:
    with st.container(height=380):
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-message"><strong> You:</strong>{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-message"><strong> Bot:</strong> {msg["content"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        response = chatbot.respond(prompt)
    except Exception as e:
        response = f"Error: {str(e)}"
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()




