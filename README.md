# 🐅 TigerGraph Social Network Chatbot

A complete natural language interface for TigerGraph using LlamaIndex and Azure OpenAI.

## ✨ Features

- 🗣️ **Natural Language Queries**: Ask questions in plain English
- 🧠 **LlamaIndex Integration**: Intelligent query routing and response formatting
- 🐅 **TigerGraph Backend**: Powerful graph database with pre-built social network schema
- ☁️ **Azure OpenAI**: GPT-4 powered conversations
- 🌐 **Modern Web UI**: Real-time chat interface with rich formatting
- 🚀 **Production Ready**: Docker, monitoring, and deployment scripts included

## 🎯 Try It Out

Ask questions like:
- "Tell me about person_001"
- "Who works at TechCorp?"
- "How is John connected to Sarah?"
- "Who are the top 5 influencers?"
- "Show me network analytics"

## 🚀 Quick Start

1. **Clone and setup**:
```bash
git clone https://github.com/YOUR_USERNAME/tigergraph-social-chatbot.git
cd tigergraph-social-chatbot
chmod +x setup.sh
./setup.sh

Configure environment:

bashcp .env.template .env
# Edit .env with your Azure OpenAI and TigerGraph credentials

Setup TigerGraph database:

bash# Run the GSQL script in TigerGraph Studio or command line
gsql setup_tigergraph.gsql

Test and run:

bashsource venv/bin/activate
python test_connection.py
python app.py

Open browser: http://localhost:5000

📊 Sample Data
The system includes:

15 people with realistic profiles
7 companies across different industries
5 cities with location data
Friendship and work relationships
5 pre-built analytical queries

🏗️ Architecture
User Question → Web UI → Flask API → LlamaIndex Agent → pyTigerGraph → TigerGraph
                    ↓
              Azure OpenAI (GPT-4)
🛠️ Tech Stack

Backend: Python, Flask, LlamaIndex, pyTigerGraph
AI: Azure OpenAI (GPT-4, Embeddings)
Database: TigerGraph
Frontend: HTML5, CSS3, JavaScript