import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# LlamaIndex imports
from llama_index.core import Settings
from llama_index.core.tools import FunctionTool
from llama_index.core.agent import ReActAgent
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

# TigerGraph imports
import pyTigerGraph as tg

# Configuration
@dataclass
class Config:
    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY: str = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_VERSION: str = "2024-02-15-preview"
    AZURE_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    AZURE_EMBEDDING_DEPLOYMENT: str = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
    
    # TigerGraph
    TIGERGRAPH_HOST: str = os.getenv("TIGERGRAPH_HOST", "http://localhost")
    TIGERGRAPH_USERNAME: str = os.getenv("TIGERGRAPH_USERNAME", "tigergraph")
    TIGERGRAPH_PASSWORD: str = os.getenv("TIGERGRAPH_PASSWORD", "tigergraph")
    TIGERGRAPH_GRAPH_NAME: str = os.getenv("TIGERGRAPH_GRAPH_NAME", "SocialNetwork")

config = Config()

class TigerGraphChatbot:
    def __init__(self):
        self.setup_logging()
        self.tg_conn = None
        self.agent = None
        self.query_descriptions = {
            "GetPersonInfo": {
                "description": "Get detailed information about a specific person including their job, company, and location",
                "parameters": ["person_id"],
                "example_questions": [
                    "Tell me about person_001",
                    "What information do you have on John Smith?",
                    "Show me details for person_005"
                ]
            },
            "FindConnections": {
                "description": "Find how two people are connected through friendships or work relationships",
                "parameters": ["source_person", "target_person", "max_hops (optional)"],
                "example_questions": [
                    "How is person_001 connected to person_003?",
                    "Find the connection between John and Sarah",
                    "What's the relationship path between person_002 and person_008?"
                ]
            },
            "GetCompanyEmployees": {
                "description": "Get all employees working at a specific company, optionally filtered by department",
                "parameters": ["company_name", "department (optional)"],
                "example_questions": [
                    "Who works at TechCorp?",
                    "Show me all employees at DataSystems",
                    "List engineering department employees at CloudVentures"
                ]
            },
            "FindTopInfluencers": {
                "description": "Find the most influential people in the network based on connections and followers",
                "parameters": ["limit_count (optional, default 10)"],
                "example_questions": [
                    "Who are the top influencers?",
                    "Show me the 5 most connected people",
                    "Find the most influential people in the network"
                ]
            },
            "GetNetworkAnalytics": {
                "description": "Get overall statistics and analytics about the social network",
                "parameters": [],
                "example_questions": [
                    "What are the network statistics?",
                    "Give me an overview of the social network",
                    "Show me network analytics"
                ]
            }
        }
    
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def initialize(self):
        """Initialize TigerGraph connection and LlamaIndex components"""
        try:
            # Initialize TigerGraph connection
            self.tg_conn = tg.TigerGraphConnection(
                host=config.TIGERGRAPH_HOST,
                username=config.TIGERGRAPH_USERNAME,
                password=config.TIGERGRAPH_PASSWORD,
                graphname=config.TIGERGRAPH_GRAPH_NAME
            )
            
            # Test the connection
            self.logger.info("Testing TigerGraph connection...")
            result = self.tg_conn.echo()
            self.logger.info(f"TigerGraph connection successful: {result}")
            
            # Initialize Azure OpenAI
            llm = AzureOpenAI(
                model="gpt-4",
                deployment_name=config.AZURE_DEPLOYMENT_NAME,
                api_key=config.AZURE_OPENAI_KEY,
                azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
                api_version=config.AZURE_OPENAI_VERSION,
                temperature=0.1
            )
            
            # Set global settings
            Settings.llm = llm
            
            # Create tools and agent
            tools = self._create_tools()
            self.agent = ReActAgent.from_tools(
                tools=tools,
                llm=llm,
                verbose=True,
                system_prompt=self._get_system_prompt()
            )
            
            self.logger.info("TigerGraph Chatbot initialized successfully!")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize chatbot: {e}")
            raise
    
    def _create_tools(self) -> List[FunctionTool]:
        """Create LlamaIndex tools for each TigerGraph query"""
        
        def get_person_info(person_id: str) -> str:
            """Get detailed information about a person by their ID"""
            try:
                result = self.tg_conn.runInstalledQuery("GetPersonInfo", {"person_id": person_id})
                if result and len(result[0]["@@result"]) > 0:
                    person_data = result[0]["@@result"][0]
                    return json.dumps({
                        "status": "success",
                        "person": person_data,
                        "message": f"Found information for {person_data['first_name']} {person_data['last_name']}"
                    }, indent=2)
                else:
                    return json.dumps({
                        "status": "not_found",
                        "message": f"No person found with ID: {person_id}"
                    }, indent=2)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Error retrieving person info: {str(e)}"
                }, indent=2)
        
        def find_connections(source_person: str, target_person: str, max_hops: int = 3) -> str:
            """Find connections between two people"""
            try:
                result = self.tg_conn.runInstalledQuery(
                    "FindConnections", 
                    {
                        "source_person": source_person,
                        "target_person": target_person,
                        "max_hops": max_hops
                    }
                )
                connections = result[0]["@@paths"] if result else []
                
                if connections:
                    return json.dumps({
                        "status": "success",
                        "connections": connections,
                        "message": f"Found {len(connections)} connection(s) between {source_person} and {target_person}"
                    }, indent=2)
                else:
                    return json.dumps({
                        "status": "not_found",
                        "message": f"No connections found between {source_person} and {target_person} within {max_hops} hops"
                    }, indent=2)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Error finding connections: {str(e)}"
                }, indent=2)
        
        def get_company_employees(company_name: str, department: str = "") -> str:
            """Get employees working at a specific company"""
            try:
                result = self.tg_conn.runInstalledQuery(
                    "GetCompanyEmployees",
                    {
                        "company_name": company_name,
                        "department": department
                    }
                )
                employees = result[0]["@@employees"] if result else []
                
                if employees:
                    dept_text = f" in {department} department" if department else ""
                    return json.dumps({
                        "status": "success",
                        "employees": employees,
                        "count": len(employees),
                        "message": f"Found {len(employees)} employee(s) at {company_name}{dept_text}"
                    }, indent=2)
                else:
                    return json.dumps({
                        "status": "not_found",
                        "message": f"No employees found at {company_name}" + (f" in {department} department" if department else "")
                    }, indent=2)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Error retrieving company employees: {str(e)}"
                }, indent=2)
        
        def find_top_influencers(limit_count: int = 10) -> str:
            """Find the most influential people in the network"""
            try:
                result = self.tg_conn.runInstalledQuery(
                    "FindTopInfluencers",
                    {"limit_count": limit_count}
                )
                influencers = result[0]["@@influencers"] if result else []
                
                return json.dumps({
                    "status": "success",
                    "influencers": influencers,
                    "count": len(influencers),
                    "message": f"Found top {len(influencers)} influencer(s) in the network"
                }, indent=2)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Error finding top influencers: {str(e)}"
                }, indent=2)
        
        def get_network_analytics() -> str:
            """Get overall network statistics and analytics"""
            try:
                result = self.tg_conn.runInstalledQuery("GetNetworkAnalytics")
                metrics = result[0]["@@metrics"] if result else []
                
                return json.dumps({
                    "status": "success",
                    "metrics": metrics,
                    "message": "Network analytics retrieved successfully"
                }, indent=2)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Error retrieving network analytics: {str(e)}"
                }, indent=2)
        
        def list_available_people() -> str:
            """List all people in the database with their basic info"""
            try:
                # Get all vertices of type Person
                result = self.tg_conn.getVertices("Person")
                people = []
                for person_id, person_data in result.items():
                    people.append({
                        "id": person_id,
                        "name": f"{person_data.get('first_name', '')} {person_data.get('last_name', '')}",
                        "job_title": person_data.get("job_title", ""),
                        "age": person_data.get("age", 0)
                    })
                
                return json.dumps({
                    "status": "success",
                    "people": people,
                    "count": len(people),
                    "message": f"Found {len(people)} people in the database"
                }, indent=2)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Error listing people: {str(e)}"
                }, indent=2)
        
        def list_available_companies() -> str:
            """List all companies in the database"""
            try:
                result = self.tg_conn.getVertices("Company")
                companies = []
                for company_id, company_data in result.items():
                    companies.append({
                        "id": company_id,
                        "name": company_data.get("name", ""),
                        "industry": company_data.get("industry", ""),
                        "size": company_data.get("size", "")
                    })
                
                return json.dumps({
                    "status": "success",
                    "companies": companies,
                    "count": len(companies),
                    "message": f"Found {len(companies)} companies in the database"
                }, indent=2)
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": f"Error listing companies: {str(e)}"
                }, indent=2)
        
        # Create FunctionTool objects
        tools = [
            FunctionTool.from_defaults(
                fn=get_person_info,
                name="get_person_info",
                description="Get detailed information about a person by their ID (e.g., person_001, person_002, etc.)"
            ),
            FunctionTool.from_defaults(
                fn=find_connections,
                name="find_connections",
                description="Find how two people are connected through friendships or work relationships"
            ),
            FunctionTool.from_defaults(
                fn=get_company_employees,
                name="get_company_employees",
                description="Get all employees working at a specific company, optionally filtered by department"
            ),
            FunctionTool.from_defaults(
                fn=find_top_influencers,
                name="find_top_influencers",
                description="Find the most influential people in the network based on connections and followers"
            ),
            FunctionTool.from_defaults(
                fn=get_network_analytics,
                name="get_network_analytics",
                description="Get overall statistics and analytics about the social network"
            ),
            FunctionTool.from_defaults(
                fn=list_available_people,
                name="list_available_people",
                description="List all people in the database with their basic information"
            ),
            FunctionTool.from_defaults(
                fn=list_available_companies,
                name="list_available_companies",
                description="List all companies in the database"
            )
        ]
        
        return tools
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return f"""You are a helpful AI assistant that helps users explore and analyze a social network database using TigerGraph.

The social network contains:
- People with their personal and professional information
- Companies where people work
- Cities where people and companies are located
- Friendship connections between people
- Work relationships between people and companies
- Professional following relationships

Available capabilities:
1. **get_person_info**: Get detailed info about a specific person (requires person ID like person_001)
2. **find_connections**: Find how two people are connected through friendships or work
3. **get_company_employees**: List employees at a company, optionally filtered by department
4. **find_top_influencers**: Find the most influential/connected people in the network
5. **get_network_analytics**: Get overall network statistics and metrics
6. **list_available_people**: See all people in the database
7. **list_available_companies**: See all companies in the database

When users ask questions:
1. If they mention specific people by name (like "John Smith"), first use list_available_people to find their person ID
2. If they mention company names, you can use them directly
3. Be helpful in explaining the results in natural language
4. If you need more information, ask clarifying questions
5. Suggest related queries that might be interesting

People IDs are in format: person_001, person_002, etc.
Company names include: TechCorp, DataSystems, CloudVentures, StartupX, FinanceHub, MobileApps Inc, CyberSecurity Pro

Be conversational and helpful. Explain results clearly and suggest interesting follow-up questions.
"""
    
    async def chat(self, user_message: str) -> Dict[str, Any]:
        """Process user message and return response"""
        try:
            response = await self.agent.achat(user_message)
            return {
                "status": "success",
                "response": str(response),
                "query": user_message
            }
        except Exception as e:
            self.logger.error(f"Error in chat: {e}")
            return {
                "status": "error",
                "response": f"I encountered an error while processing your request: {str(e)}",
                "query": user_message
            }
    
    def get_query_descriptions(self) -> Dict[str, Any]:
        """Get descriptions of available queries"""
        return {
            "queries": self.query_descriptions,
            "sample_data": {
                "people": ["person_001 (John Smith)", "person_002 (Sarah Johnson)", "person_003 (Mike Brown)"],
                "companies": ["TechCorp", "DataSystems", "CloudVentures", "StartupX", "FinanceHub"]
            }
        }

# Flask Application
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Initialize chatbot
chatbot = TigerGraphChatbot()

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "TigerGraph Chatbot"})

@app.route('/api/chat', methods=['POST'])
async def chat():
    """Main chat endpoint"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({"error": "Please provide a message"}), 400
        
        result = await chatbot.chat(user_message)
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "status": "error",
            "response": "I'm sorry, I encountered an internal error. Please try again.",
            "error": str(e)
        }), 500

@app.route('/api/queries', methods=['GET'])
def get_available_queries():
    """Get information about available queries"""
    return jsonify(chatbot.get_query_descriptions())

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test TigerGraph connection"""
    try:
        if chatbot.tg_conn:
            result = chatbot.tg_conn.echo()
            return jsonify({
                "status": "success",
                "message": "TigerGraph connection is working",
                "response": result
            })
        else:
            return jsonify({
                "status": "error",
                "message": "TigerGraph connection not initialized"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"TigerGraph connection failed: {str(e)}"
        }), 500

if __name__ == "__main__":
    # Initialize the chatbot
    try:
        asyncio.run(chatbot.initialize())
        print("🚀 TigerGraph Chatbot is ready!")
        print("🌐 Open http://localhost:5000 in your browser")
        print("📊 TigerGraph queries available:")
        for query_name, info in chatbot.query_descriptions.items():
            print(f"   - {query_name}: {info['description']}")
        
        # Start Flask app
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        print(f"❌ Failed to start chatbot: {e}")
        print("Please check your configuration and TigerGraph connection.")