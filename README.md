# MemAgent
Hybrid Context-Aware Multi-Agent Memory System

This project implements an advanced, production-grade agentic memory pipeline that bridges the gap between semantic similarity matching and relational structured knowledge.

By layering Vector Space Search alongside a Graph Database architecture, the agent acts less like a standard stateless chatbot and more like a human assistant—maintaining long-term episodic context, extracting dynamic global entity attributes, and tracking cross-user behavioral relationships on the fly.

Core System Architecture
The ecosystem relies on an integrated, modern AI engineering stack designed for cloud-free token parsing efficiency and ultra-low latency response cycles:

<img width="657" height="472" alt="image" src="https://github.com/user-attachments/assets/8b2da694-2817-4179-8edb-625e34f51015" />


 Orchestration Layer (mem0): Manages conversational session tracking, controls state management, handles user profile parsing rules, and aggregates context windows.

Inference Pipeline (Groq Cloud): Powered by llama-3.3-70b-versatile for blazing-fast inference, processing core user responses and handling entity parsing schemas using JSON object configurations.

Embedding Model (HuggingFace Transformers): Runs BAAI/bge-small-en-v1.5 locally, compiling unstructured natural text inputs into accurate 384-dimensional dense vectors without relying on external paywalled APIs.

Vector Store Backend (Qdrant Local Host): Manages persistent multi-tenant text vectors, matches semantic profiles via cosine distance metrics, and updates context payloads in real-time.

Knowledge Graph Execution Core (Neo4j Aura DB): A cloud-hosted graph layer that stores nodes and explicit semantic edges (Relationships). This allows developers to query, analyze, and map complex behavioral data through a web interface.

Dual-Layer Storage Mechanics
The system stores information in two distinct ways to overcome the limitations of using just one database type:

1. The Vector Storage Layer (Qdrant)
When an interaction happens, mem0 calculates mathematical embeddings and pushes text records directly into the local Qdrant collection.

The Goal: To quickly surface loose, similar contextual chunks (e.g., "User mentioned a milk allergy 3 days ago").

The Problem: It handles raw blocks of text natively. It does not understand specific entities or explicit parameters without reading through full JSON structures.

2. The Structured Graph Extraction Layer (Neo4j)
To fix this, an extraction worker passes the chat history back through Groq to run Open Information Extraction (OpenIE). The model turns the conversation into structured entity triplets: [Subject -> Predicate -> Object].

The Goal: It strips out filler conversational words and runs a Cypher merge statement to dynamically build clean, interactive objects.

The Result: The database maps out direct networks like (:Person {name: "Jayesh"})-[:HAS_ALLERGY]->(:Entity {name: "milk product"}).

