import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

from openai_service import generate_response

# Load API keys etc.
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GRAPH_DATA_PATH = os.getenv("GRAPH_DATA_PATH", "./Scraped/scraped_content.json")  # generated from entity extractor or filtered scraper


def load_graph_data(path: str) -> List[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"✅ Loaded {len(data)} graph items from JSON")
        return data
    except Exception as e:
        logger.error("❌ Error loading graph JSON", exc_info=e)
        return []


def find_relevant_facts(question: str, graph_data: List[Dict], max_hits=5) -> List[str]:
    question_lower = question.lower()
    relevant = []

    for item in graph_data:
        match_score = 0
        content = item.get("content", "") or item.get("description", "") or ""
        keywords = " ".join(item.get("metadata", {}).get("keywords", []))

        combined = f"{content} {keywords}".lower()

        if any(word in combined for word in question_lower.split()):
            match_score += 1

        if match_score > 0:
            relevant.append((match_score, item))

    relevant.sort(reverse=True, key=lambda x: x[0])
    top_facts = [f"{i['title']}: {i['content'][:300]}..." for _, i in relevant[:max_hits]]

    logger.info(f"📚 Selected {len(top_facts)} context chunks for GraphRAG")
    return top_facts


async def graph_rag_response(user_question: str) -> str:
    graph_data = load_graph_data(GRAPH_DATA_PATH)
    context_facts = find_relevant_facts(user_question, graph_data)

    if not context_facts:
        return "I couldn't find anything in the Nestlé knowledge graph related to your question."

    context_text = "\n\n".join(context_facts)

    prompt = f"""
  "content": "You are Smartie, a digital assistant created to provide information about Nestlé products available in Canada. 
  Your purpose is to: \n\n1. Offer details about product ingredients, features, and availability \n2. 
  Share approved recipes using Nestlé products \n3. Provide general nutritional information \n4. 
  Maintain a friendly yet professional tone \n5. Give concise responses (1-2 paragraphs maximum) \n6. 
  Always clarify when you don't have information \n\nImportant Rules:\n- Never make claims about health benefits\n- Direct 
  users to official packaging for most accurate info\n- Use Canadian product names and measurements\n- When unsure, suggest 
  contacting Nestlé Canada directly",

Facts:
{context_text}

Question: {user_question}

Answer:"""

    return generate_response(prompt)
