import os
import json
from dotenv import load_dotenv
from groq import Groq
from mem0 import Memory
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Clean Mem0 configuration (Standard Qdrant Setup)
config = {
    "version": "v1.1",
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "BAAI/bge-small-en-v1.5"
        }
    },
    "llm": {
        "provider": "groq",
        "config": {
            "api_key": os.getenv("GROQ_API_KEY"),
            "model": "llama-3.3-70b-versatile"
        }
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "groq_memories",
            "embedding_model_dims": 384
        }
    }
}

# Initialize memory
memory = Memory.from_config(config)

# --- NEO4J CONNECTION ---
NEO4J_URL = "neo4j+s://2c358abd.databases.neo4j.io"
NEO4J_USER = "2c358abd"
NEO4J_PASS = "mLC6pSbtNn5qh_fzHfZR_X2zmqAXEI15c-YLoXtWX64"

neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASS))

def sync_dynamic_triplets(tx, triplets):
    """
    Dynamically creates nodes and connections based on whatever the LLM extracts.
    Example: (Person {name: 'Sarah'})-[:FAVORITE_FOOD]->(Entity {name: 'Pizza'})
    """
    for triplet in triplets:
        source = triplet.get("source").strip()
        relationship = triplet.get("relationship").strip().replace(" ", "_").upper()
        target = triplet.get("target").strip()
        
        if not source or not relationship or not target:
            continue
            
        # Cypher query that handles dynamic labels and connections safely
        cypher_query = f"""
        MERGE (s:Person {{name: $source}})
        MERGE (t:Entity {{name: $target}})
        MERGE (s)-[:{relationship}]->(t)
        """
        tx.run(cypher_query, source=source, target=target)


def extract_dynamic_triplets(user_text, ai_text):
    """
    Instructs Llama 3.3 to extract knowledge graph triplets from the chat text dynamically.
    """
    extraction_prompt = f"""
    Analyze the dialogue below. Extract facts as Knowledge Graph triplets [Source, Relationship, Target].
    - The 'source' should be the specific person talking or being discussed (e.g., 'Jayesh', 'Sarah', 'My Friend').
    - The 'relationship' must be a concise action/state verb (e.g., 'LIVES_IN', 'FAVORITE_FOOD', 'HAS_ALLERGY', 'VISITED').
    - The 'target' is the object, place, or thing.
    
    Return strictly a JSON object with this exact structure:
    {{
        "triplets": [
            {{"source": "John", "relationship": "FAVORITE_FOOD", "target": "Sushi"}},
            {{"source": "Alex", "relationship": "VISITED", "target": "Paris"}}
        ]
    }}
    
    Dialogue:
    User: {user_text}
    AI: {ai_text}
    """
    try:
        extract_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": extraction_prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(extract_response.choices[0].message.content)
        return data.get("triplets", [])
    except Exception as e:
        print(f"[Extraction Warning]: {e}")
        return []


USER_ID = "global_user_session"
print("Type 'exit' to quit.\n")

while True:
    user_query = input("> ")

    if user_query.lower() == "exit":
        break

    # Retrieve vector memories for conversational context
    search_results = memory.search(query=user_query, filters={"user_id": USER_ID})
    context = ""
    memories = search_results.get("results", []) if isinstance(search_results, dict) else search_results

    if memories:
        context = "\n".join(m["memory"] for m in memories if isinstance(m, dict) and "memory" in m)

    # Build prompt messages
    messages = [
        {"role": "system", "content": f"You are a helpful assistant.\n\nRelevant memories:\n{context}"},
        {"role": "user", "content": user_query}
    ]

    # Generate primary response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    ai_response = response.choices[0].message.content
    print("\nAI:", ai_response)

    # 1. Save standard semantic logs to Mem0 vector engine
    conversation_turn = [
        {"role": "user", "content": user_query},
        {"role": "assistant", "content": ai_response}
    ]
    memory.add(conversation_turn, user_id=USER_ID)

    # 2. Extract facts dynamically and push them to your Neo4j Instance
    try:
        triplets = extract_dynamic_triplets(user_query, ai_response)
        if triplets:
            with neo4j_driver.session() as session:
                session.execute_write(sync_dynamic_triplets, triplets)
            print(f"[Graph Sync Complete: Created {len(triplets)} dynamic links inside Neo4j]")
    except Exception as e:
        print(f"[Neo4j Dynamic Sync Warning]: {e}")
        
    print()

neo4j_driver.close()