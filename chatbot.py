
import re
import sqlite3
from flask import Flask, g, request, jsonify
from bs4 import BeautifulSoup
import requests
from langchain.memory import ConversationBufferMemory
from langchain.agents import Tool
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import random

# ========== Database Manager ==========
class DatabaseManager:
    def __init__(self, db_path='chatbot_db.sqlite'):
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.setup_db()
        
    def setup_db(self):
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    id INTEGER PRIMARY KEY,
                    question TEXT,
                    answer TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS conversation_logs (
                    id INTEGER PRIMARY KEY,
                    user_input TEXT,
                    bot_response TEXT,
                    intent TEXT,
                    tools_used TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    
    def query_knowledge(self, question):
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT answer FROM knowledge WHERE question LIKE :query"),
                    {"query": f"%{question}%"}
                ).fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Database error: {str(e)}")
            return None
    
    def log_conversation(self, user_input, bot_response, intent, tools_used=None):
        try:
            with self.engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO conversation_logs 
                        (user_input, bot_response, intent, tools_used) 
                        VALUES (:input, :response, :intent, :tools)
                    """),
                    {
                        "input": user_input, 
                        "response": bot_response, 
                        "intent": intent,
                        "tools": str(tools_used) if tools_used else None
                    }
                )
                conn.commit()
        except Exception as e:
            print(f"Failed to log conversation: {str(e)}")


# ========== Web Scraper ==========
class WebScraper:
    def get_content(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
                
            return ' '.join([p.get_text().strip() for p in soup.find_all('p') if p.get_text().strip()])
        except Exception as e:
            return f"Error accessing URL: {str(e)}"
        

# ========== Enhanced Chatbot ==========
class AIChatbot:
    def __init__(self):
        self.scraper = WebScraper()
        self.db = DatabaseManager()
        
        self.memory = ConversationBufferMemory(memory_key="chat_history")
        
        self.tools = [
            Tool(
                name="KnowledgeBase",
                func=self.handle_knowledge_query,
                description="Useful for answering factual questions from the database"
            ),
            Tool(
                name="WebScraper",
                func=self.handle_web_query,
                description="Useful when you need to get content from a website URL"
            ),
            Tool(
                name="GeneralConversation",
                func=self.handle_general_chat,
                description="Useful for general conversations, greetings, and small talk"
            )
        ]
        
        
    def extract_url(self, text):
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        return urls[0] if urls else None
    
    def handle_knowledge_query(self, query):
        """Tool function for knowledge base queries"""
        result = self.db.query_knowledge(query)
        return result if result else "No information found in knowledge base"
    
    def handle_web_query(self, query):
        """Tool function for web scraping"""
        url = self.extract_url(query)
        if url:
            content = self.scraper.get_content(url)
            return f"From {url}: {content[:500]}..."  # Truncate long content
        return "No valid URL found in query"
    
    def handle_general_chat(self, query):
        """Tool function for general conversation"""
        responses = {
            "greeting": ["Hello!", "Hi there!", "Hey! How can I help you?"],
            "farewell": ["Goodbye!", "See you later!", "Have a nice day!"],
            "thanks": ["You're welcome!", "My pleasure!", "Happy to help!"],
            "identity": ["I'm an AI chatbot designed to assist you with information, web searches, and conversation.",
                         "I'm your friendly AI assistant, ready to help with your questions!",
                         "I'm a conversational AI built to provide information and assistance."],
            "name": ["You can call me ChatBot!", "I'm ChatBot, your AI assistant.", "My name is ChatBot, how can I help you today?"],
            "capabilities": ["I can answer questions, search for information in my knowledge base, and extract content from websites.",
                            "I'm capable of answering questions, having conversations, and helping you find information online.",
                            "My capabilities include answering questions, web searching, and friendly conversation."],
            "joke": [
        "Why don't scientists trust atoms? Because they make up everything!",
        "Why did the math book look sad? Because it had too many problems!",
        "What do you get if you cross a cat with a dark horse? Kitty Perry!"
    ],
            "repeat": ["Sure! Here's another one:", "Let me tell you another."],
            "clear_history": ["Chat history cleared.", "Starting fresh!", "Conversation reset."],
            "default": ["I'm not sure how to respond to that.", "Could you rephrase your question?", "I don't have information on that yet."]
        }
        
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["hello", "hi", "hey", "howdy"]):
            return random.choice(responses["greeting"])
        elif any(word in query_lower for word in ["bye", "goodbye", "later", "see you"]):
            return random.choice(responses["farewell"])
        elif any(word in query_lower for word in ["thank", "thanks", "appreciate"]):
            return random.choice(responses["thanks"])
        elif any(phrase in query_lower for phrase in ["who are you", "what are you", "tell me about yourself", "your purpose"]):
            return random.choice(responses["identity"])
        elif any(phrase in query_lower for phrase in ["your name", "what's your name", "what are you called", "what should i call you"]):
            return random.choice(responses["name"])
        elif any(phrase in query_lower for phrase in ["what can you do", "your abilities", "your capabilities", "help me with", "how can you help"]):
            return random.choice(responses["capabilities"])
        elif any(phrase in query_lower for phrase in ["tell me a joke", "say something funny", "make me laugh", "know any joke", "tell joke"]):
            return random.choice(responses["joke"])
        elif any(phrase in query_lower for phrase in ["another", "another one", "tell me more", "can you repeat", "another joke", "one more"]):
            return random.choice(responses["repeat"])
        elif any(phrase in query_lower for phrase in ["clear", "reset conversation", "start over"]):
            return random.choice(responses["clear_history"])
        
        return random.choice(responses["default"])
    
    def respond(self, user_input):
        try:
            user_input_lower = user_input.lower()
            
            url = self.extract_url(user_input)
            if url:
                response = self.handle_web_query(user_input)
                intent = "web_query"
            elif any(phrase in user_input_lower for phrase in ["who are you", "what are you", "your name", "what can you do"]):
                response = self.handle_general_chat(user_input)
                intent = "identity_query"
            else:
                kb_response = self.handle_knowledge_query(user_input)
                if kb_response and kb_response != "No information found in knowledge base":
                    response = kb_response
                    intent = "knowledge_query"
                else:
                    response = self.handle_general_chat(user_input)
                    intent = "general_chat"
            
            self.db.log_conversation(
                user_input=user_input,
                bot_response=response,
                intent=intent,
                tools_used=intent
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing your request: {str(e)}"
            self.db.log_conversation(
                user_input=user_input,
                bot_response=error_msg,
                intent="error"
            )
            return error_msg
        

# ========== Flask App ==========
app = Flask(__name__)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400
    
    if 'chatbot' not in g:
        g.chatbot = AIChatbot()
    
    response = g.chatbot.respond(data['message'])
    
    return jsonify({
        'response': response,
        'status': 'success'
    })

@app.route('/')
def home():
    return """
    <h1>AI Chatbot API</h1>
    <p>Send POST requests to /chat with JSON containing 'message' field.</p>
    """

if __name__ == '__main__':
    app.run(debug=True)


    