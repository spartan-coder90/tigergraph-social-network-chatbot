import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_setup():
    print("🔍 Testing TigerGraph Chatbot Setup...")
    print("=" * 50)
    
    # Test 1: Check environment variables
    print("1. 📋 Checking environment variables...")
    required_vars = [
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY", 
        "AZURE_OPENAI_DEPLOYMENT",
        "TIGERGRAPH_HOST",
        "TIGERGRAPH_USERNAME",
        "TIGERGRAPH_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"   ✅ {var}: Set")
    
    if missing_vars:
        print(f"   ❌ Missing variables: {', '.join(missing_vars)}")
        return False
    
    # Test 2: Test TigerGraph connection
    print("\n2. 🐅 Testing TigerGraph connection...")
    try:
        import pyTigerGraph as tg
        
        conn = tg.TigerGraphConnection(
            host=os.getenv("TIGERGRAPH_HOST"),
            username=os.getenv("TIGERGRAPH_USERNAME"),
            password=os.getenv("TIGERGRAPH_PASSWORD"),
            graphname=os.getenv("TIGERGRAPH_GRAPH_NAME", "SocialNetwork")
        )
        
        result = conn.echo()
        print(f"   ✅ TigerGraph connection successful: {result}")
        
        # Test graph schema
        vertices = conn.getVertexTypes()
        print(f"   ✅ Found vertex types: {vertices}")
        
    except Exception as e:
        print(f"   ❌ TigerGraph connection failed: {e}")
        return False
    
    # Test 3: Test Azure OpenAI connection
    print("\n3. ☁️  Testing Azure OpenAI connection...")
    try:
        from llama_index.llms.azure_openai import AzureOpenAI
        
        llm = AzureOpenAI(
            model="gpt-4",
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-02-15-preview",
            temperature=0.1
        )
        
        response = await llm.acomplete("Hello, this is a test.")
        print(f"   ✅ Azure OpenAI connection successful")
        
    except Exception as e:
        print(f"   ❌ Azure OpenAI connection failed: {e}")
        return False
    
    # Test 4: Test installed queries
    print("\n4. 🔧 Testing installed TigerGraph queries...")
    try:
        queries = conn.getInstalledQueries()
        expected_queries = ["GetPersonInfo", "FindConnections", "GetCompanyEmployees", 
                          "FindTopInfluencers", "GetNetworkAnalytics"]
        
        for query in expected_queries:
            if query in queries:
                print(f"   ✅ Query {query}: Installed")
            else:
                print(f"   ❌ Query {query}: Not found")
                
    except Exception as e:
        print(f"   ⚠️  Could not check installed queries: {e}")
    
    print("\n🎉 Setup test completed successfully!")
    print("\nYou can now run the chatbot with: python app.py")
    return True

if __name__ == "__main__":
    asyncio.run(test_setup())
