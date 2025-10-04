Discord RAG-Based Question Answering System
Author: Jibin Kunjumon
Project: Intelligent Discord Bot with Retrieval-Augmented Generation

📋 Table of Contents

Overview
Problem & Objective
Architecture
Technologies Used
Project Structure
Setup & Installation
Configuration
Usage
Evaluation Results
Key Features
Documentation


🎯 Overview
An intelligent Discord bot that answers user questions using Retrieval-Augmented Generation (RAG) with real-time context understanding. The system combines document retrieval with AI language models to provide instant, accurate responses through a familiar chat interface.
Why It Matters

✅ Provides instant, accurate responses
✅ Combines document retrieval with Azure GPT-3.5 Turbo
✅ Enables seamless knowledge access through Discord
✅ Context-aware answer generation


🔍 Problem & Objective
What It Does:
An intelligent Discord bot that answers user questions using Retrieval-Augmented Generation (RAG) with real-time context understanding.
Why It Matters:
Provides instant, accurate responses by combining document retrieval with AI language models, enabling seamless knowledge access through a familiar chat interface.

🏗️ Architecture
System Architecture
The system follows a three-tier architecture:

Data Layer: MongoDB Atlas Vector Database for semantic search
Processing Layer: RAG pipeline with embeddings and retrieval
Interface Layer: Discord bot for user interaction

Show Image
Workflow

📁 Data Preparation

Raw documents are chunked into manageable pieces
Embeddings generated using sentence transformers
Stored in MongoDB Atlas Vector Database


🔄 RAG Pipeline

User query is encoded into vector format
System performs vector similarity search
Top-3 relevant documents retrieved as context
Context + query sent to Azure GPT-3.5 Turbo
AI generates accurate, context-aware answer


💬 Deployment

Integrated with Discord bot interface
Real-time query processing
Seamless user experience



Show Image

🛠️ Technologies Used
TechnologyPurposePythonBackend developmentVS CodeDevelopment environmentGoogle ColabExperimentation and notebook developmentSentence TransformersDocument and query embeddings (all-MiniLM-L6-v2, 384 dimensions)MongoDB AtlasVector database for semantic search and efficient similarity retrievalAzure OpenAI GPT-3.5 TurboLanguage model for context-aware answer generationDiscord.pyBot framework with real-time user interactionFAISSVector similarity searchLangChainLLM orchestration and text processing

📁 Project Structure
discord-rag-data-scientist/
│
├── backend/                    # Core Python modules
│   ├── chatbot.py             # Entry point for RAG chatbot logic
│   ├── discord_bot.py         # Connects model to Discord
│   ├── embeddings.py          # Sentence embeddings (MiniLM / OpenAI)
│   ├── llm.py                 # LLM configuration and responses
│   ├── RAG_pipeline.py        # Retrieval-Augmented Generation pipeline
│   └── retrieval.py           # Context retrieval logic
│
├── diagrams/                   # System design visuals
│   ├── architectural_diagram.png
│   └── workflow_diagram.png
│
├── docs/                       # Research & documentation
│   ├── EMBEDDING_MODELS_RESEARCH.md
│   ├── IN_SCOPE.md
│   ├── learning_guide.md
│   └── VECTOR_BASES_RESEARCH.md
│
├── notebooks/                  # Model training & evaluation
│   └── Discord_Chatbot_Lab.ipynb
│
├── reports/                    # Evaluation outputs
│   ├── evaluation_report.md
│   └── results.json
│
├── config.py                   # Configuration variables
├── evaluation.py               # Model evaluation script
├── .env                        # Environment variables (API keys)
├── .gitignore                  # Git ignore rules
├── BLOCKERS.md                 # Issues tracked during development
├── requirements.txt            # Python dependencies
└── README.md                   # This file

⚙️ Setup & Installation
Prerequisites

Python 3.8 or higher
MongoDB Atlas account with a cluster
Azure OpenAI API access
Discord Bot Token

Installation Steps

Clone the repository

bash   git clone <repository-url>
   cd discord-rag-data-scientist

Create a Conda environment (recommended)

bash   conda create -n discord-rag python=3.10
   conda activate discord-rag

Install dependencies

bash   pip install -r requirements.txt
Dependencies
txtsentence-transformers==5.1.0
numpy==1.26.4
scikit-learn==1.7.2
langchain==0.3.27
langchain-text-splitters==0.3.11
pymongo==4.15.1
dnspython==2.8.0
openai==1.109.1
discord.py==2.6.3
faiss==1.7.4
tiktoken==0.11.0
python-dotenv==1.1.1

🔧 Configuration
1. MongoDB Atlas Setup

Create a MongoDB Atlas cluster
Create a database named: rag_db
Create a collection named: chunks
Obtain your MongoDB connection URI

2. Azure OpenAI Setup

Set up Azure OpenAI service
Deploy GPT-3.5 Turbo model
Obtain API key and endpoint

3. Discord Bot Setup

Go to Discord Developer Portal
Create a new application
Create a bot and obtain the bot token
Enable necessary intents (Message Content Intent)
Invite bot to your server

4. Environment Variables
Create a .env file in the root directory:
envDISCORD_BOT_TOKEN=your_discord_bot_token_here
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here
MONGODB_URI=your_mongodb_connection_uri_here

🚀 Usage
Running the Discord Bot
bashpython -m backend.discord_bot
The bot will start and connect to your Discord server. Once running, users can interact with it using the following prefixes:
Chat Commands:

!ask <your question>
$ask <your question>
/ask <your question>

Example:
!ask What is machine learning?
Running Evaluation
To evaluate the system's performance:
bashpython -m evaluation
This will run the evaluation suite and generate:

reports/evaluation_report.md - Detailed evaluation metrics
reports/results.json - Raw evaluation results

Using the Colab Notebook
Open notebooks/Discord_Chatbot_Lab.ipynb in Google Colab for:

Experimentation with embeddings
Model training and testing
Pipeline prototyping


📈 Evaluation Results
System Performance

✅ 4/4 test queries passed
✅ 69.2% average token overlap
✅ 100% expected keyword match rate

Retrieval Accuracy

Top-3 document retrieval working effectively
Relevant context successfully extracted
Source attribution included in responses

Response Quality

High accuracy: 90-96% token overlap
Context-aware answer generation
Graceful handling of out-of-scope queries

Example:
Query: "Who is Elon Musk?"
Response: "My knowledge base contains information about Python, Machine Learning, Web Development, and Discord."
Key Achievement
✨ Fully functional RAG system with robust evaluation framework

✨ Key Features
Discord Bot (discord_bot.py)
The Discord bot implements a clean, prefix-based RAG chatbot built using discord.py. Features include:

Multiple prefix support (!ask, $ask, /ask)
Per-user cooldowns to prevent spam
Caching with lru_cache for repeated queries
Answer cleaning to remove unnecessary source or noise text
Fallback responses for out-of-scope questions
Real-time query processing

Evaluation System (evaluation.py)
Comprehensive evaluation framework that:

Tests query accuracy
Measures token overlap
Validates keyword matching
Generates detailed reports


📚 Documentation
Additional documentation is available in the docs/ directory:

EMBEDDING_MODELS_RESEARCH.md - Research on embedding model selection
VECTOR_BASES_RESEARCH.md - Vector database comparison and selection
IN_SCOPE.md - Project scope and requirements
learning_guide.md - Learning resources and guides
BLOCKERS.md - Development challenges and solutions


🎯 Key Takeaways
✅ Built end-to-end RAG system with 100% test accuracy
✅ Integrated Azure GPT-3.5 Turbo with MongoDB Atlas
✅ Deployed functional Discord bot interface
✅ Achieved 69.2% average token overlap with expected responses
✅ Implemented robust evaluation framework

📝 License
This project is created for educational purposes.

🙏 Acknowledgments
Special thanks to the open-source communities behind:

LangChain
Sentence Transformers
Discord.py
MongoDB


Built with ❤️ by Jibin Kunjumon