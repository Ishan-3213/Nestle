import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

from openai_service import generate_response

# Load environment variables from .env file (e.g., API keys, paths)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the graph-based knowledge file (typically extracted/filtered product info)
GRAPH_DATA_PATH = os.getenv("GRAPH_DATA_PATH", "./Scraped/scraped_content.json")


def load_graph_data(path: str) -> List[Dict]:
    """
    Loads JSON data representing the product knowledge graph.

    Args:
        path (str): Path to the JSON file.

    Returns:
        List[Dict]: List of dictionary items containing product data.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"✅ Loaded {len(data)} graph items from JSON")
        return data
    except Exception as e:
        logger.error("❌ Error loading graph JSON", exc_info=e)
        return []


def find_relevant_facts(question: str, graph_data: List[Dict], max_hits=5) -> List[str]:
    """
    Retrieves the most relevant content chunks from the graph based on keyword matching.

    Args:
        question (str): User's natural language query.
        graph_data (List[Dict]): Loaded product data.
        max_hits (int): Maximum number of matching chunks to return.

    Returns:
        List[str]: Top N content snippets that are relevant to the question.
    """
    question_lower = question.lower()
    relevant = []

    for item in graph_data:
        match_score = 0

        # Try matching based on available content and keywords
        content = item.get("content", "") or item.get("description", "") or ""
        keywords = " ".join(item.get("metadata", {}).get("keywords", []))
        combined = f"{content} {keywords}".lower()

        # Naive keyword match (could be replaced with semantic match later)
        if any(word in combined for word in question_lower.split()):
            match_score += 1

        if match_score > 0:
            relevant.append((match_score, item))

    # Sort by match score in descending order
    relevant.sort(reverse=True, key=lambda x: x[0])

    # Format top hits as "title: content..."
    top_facts = [f"{i['title']}: {i['content'][:300]}..." for _, i in relevant[:max_hits]]

    logger.info(f"📚 Selected {len(top_facts)} context chunks for GraphRAG")
    return top_facts


async def graph_rag_response(user_question: str) -> str:
    """
    Main Graph-RAG pipeline: fetches relevant graph-based facts and generates a conversational response.

    Args:
        user_question (str): The user's input question.

    Returns:
        str: AI-generated answer based on available graph facts and prompt rules.
    """
    # Load knowledge graph data
    graph_data = load_graph_data(GRAPH_DATA_PATH)

    # Select most relevant fact snippets
    context_facts = find_relevant_facts(user_question, graph_data)

    # Fallback if nothing matched
    if not context_facts:
        return "I couldn't find anything in the Nestlé knowledge graph related to your question."

    # Merge all selected facts as prompt context
    context_text = "\n\n".join(context_facts)

    # Construct a system + user prompt with instructions and selected facts
    prompt = f"""
"content": "You are NestleBOT, a digital assistant created to provide information about Nestlé products available in Canada. 
Your purpose is to: 

1. Offer details about product ingredients, features, and availability  
2. Share approved recipes using Nestlé products  
3. Provide general nutritional information  
4. Maintain a friendly yet professional tone  
5. Give concise responses (1-2 paragraphs maximum)  
6. Always clarify when you don't have information  

Important Rules:
- Never make claims about health benefits
- Direct users to official packaging for most accurate info
- Use Canadian product names and measurements
- When unsure, suggest contacting Nestlé Canada directly",

Facts:
{context_text}

Question: {user_question}

Answer:"""

    # Generate AI response from OpenAI or Azure OpenAI service
    return generate_response(prompt)
