# indexer_service.py
# Converts scraped content into vectorized documents and uploads to Azure Cognitive Search

import logging
from scraper import get_scraped_content
from search_service import AzureSearchService
from openai_service import generate_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_search_documents(products: list) -> list:
    documents = []

    for product in products:
        try:
            # Extract ID from URL
            product_url = product.get("url", "")
            product_id = product_url.replace("https://www.madewithnestle.ca/", "")

            # Determine category
            metadata = product.get("metadata", {})
            category = metadata.get("categories", ["unknown"])[0]
            keywords = metadata.get("keywords", [])
            description = metadata.get("description", "")

            # Text to embed
            content = product.get("content", "")
            title = product.get("title", "")
            content_to_embed = f"{title} {content} {description} {' '.join(keywords)}"

            # Generate vector embedding
            vector_field = generate_embeddings(content_to_embed)

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


def index_scraped_content(self):
    try:
        logger.info("🚀 Starting to index content...")

        # Ensure index exists
        AzureSearchService.create_search_index()

        # Load scraped data
        products = get_scraped_content()
        if not products:
            logger.warning("No products found. Please run the scraper first.")
            return

        logger.info(f"Found {len(products)} products to index")

        # Vectorize and structure
        documents = prepare_search_documents(products)
        if not documents:
            logger.warning("No documents prepared for indexing")
            return

        logger.info(f"Uploading {len(documents)} documents to Azure Search")
        AzureSearchService.upload_documents(documents)

        logger.info("✅ Indexing completed successfully")

    except Exception as e:
        logger.error("❌ Error indexing scraped content:", exc_info=e)
        raise
