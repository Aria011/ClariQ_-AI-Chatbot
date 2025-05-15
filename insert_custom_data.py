import sqlite3
from datetime import datetime

custom_data = [
    ("What is Python?", "Python is a popular programming language."),
    ("Who created Python?", "Python was created by Guido van Rossum."),
    ("What is AI?", "AI stands for Artificial Intelligence."),
    ("What is ChatGPT?", "ChatGPT is an AI language model developed by OpenAI."),
    ("How does the chatbot work?", "It uses NLP, a knowledge base, and web scraping."),
    ("What is OpenAI?", "OpenAI is an AI research lab."),
    ("Who developed ChatGPT?", "ChatGPT was developed by OpenAI.")
]

def insert_custom_data(data):
    
        conn = sqlite3.connect("chatbot_db.sqlite")
        cursor = conn.cursor()
        
        for question, answer in data:
            cursor.execute("""
                INSERT INTO knowledge (question, answer, created_at)
                VALUES (?, ?, ?)
            """, (question, answer, datetime.now()))
        
        conn.commit()
        conn.close()

        insert_custom_data(custom_data)
        print("Custom dataset inserted successfully.")


