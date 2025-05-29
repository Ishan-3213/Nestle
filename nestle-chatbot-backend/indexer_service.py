# indexer_service.py

import logging
from scraper import get_scraped_content
from search_service import AzureSearchService
from openai_service import generate_embeddings

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_search_documents(products: list) -> list:
    """
    Converts scraped product data into documents suitable for Azure Cognitive Search.
    
    Args:
        products (list): List of scraped product dictionaries.
    
    Returns:
        list: List of structured and vectorized documents ready for indexing.
    """
    documents = []

    for product in products:
        try:
            # Extract unique ID from the product URL
            product_url = product.get("url", "")
            product_id = product_url.replace("https://www.madewithnestle.ca/", "")

            # Extract metadata for enrichment
            metadata = product.get("metadata", {})
            category = metadata.get("categories", ["unknown"])[0]
            keywords = metadata.get("keywords", [])
            description = metadata.get("description", "")

            # Combine text fields to generate semantic embeddings
            content = product.get("content", "")
            title = product.get("title", "")
            content_to_embed = f"{title} {content} {description} {' '.join(keywords)}"

            # Generate OpenAI embedding vector for semantic search
            vector_field = generate_embeddings(content_to_embed)

            # Append the formatted document
            documents.append({
                "id": product_id,
                "url": product_url,
                "title": title,
                "content": content,
                "category": category,
                "keywords": keywords,
                "description": description,
                "vectorField": vector_field
            })

            logger.info(f"Prepared document for: {title}")

        except Exception as e:
            logger.error(f"Error preparing document for {product.get('title', 'Unknown')}:", exc_info=e)

    return documents


def index_scraped_content():
    """
    Main function to index all scraped content into Azure Cognitive Search.
    
    This function will:
    - Load the scraped data from local storage
    - Prepare documents (including OpenAI embeddings)
    - Create the Azure search index (if needed)
    - Upload documents to Azure Cognitive Search
    """
    try:
        logger.info("🚀 Starting to index content...")

        # Ensure the search index exists in Azure
        AzureSearchService.create_search_index()

        # Load the previously scraped content
        products = get_scraped_content()
        if not products:
            logger.warning("No products found. Please run the scraper first.")
            return

        logger.info(f"Found {len(products)} products to index")

        # Prepare documents with vector embeddings
        documents = prepare_search_documents(products)
        if not documents:
            logger.warning("No documents prepared for indexing")
            return

        # Upload documents to Azure Cognitive Search
        logger.info(f"Uploading {len(documents)} documents to Azure Search")
        AzureSearchService.upload_documents(documents)

        logger.info("✅ Indexing completed successfully")

    except Exception as e:
        logger.error("❌ Error indexing scraped content:", exc_info=e)
        raise
