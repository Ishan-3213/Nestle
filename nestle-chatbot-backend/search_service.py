import os
import requests
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class AzureSearchService:
    def __init__(self):
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
        self.search_api_key = os.getenv("AZURE_SEARCH_API_KEY", "")
        self.search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "nestle-chat-bot")
        self.api_version = self._detect_api_version()  # Auto-detect best API version
        self.headers = {
            "api-key": self.search_api_key,
            "Content-Type": "application/json"
        }

    def _detect_api_version(self) -> str:
        """Detect the best supported API version"""
        versions_to_try = [
            "2023-11-01",
            "2023-10-01-Preview",
            "2021-04-30-Preview",
            "2020-06-30"
        ]
        
        for version in versions_to_try:
            try:
                url = f"{self.search_endpoint}/indexes?api-version={version}&$top=1"
                response = requests.get(url, headers={"api-key": self.search_api_key})
                if response.status_code == 200:
                    print(f"✅ Using API version: {version}")
                    return version
            except Exception:
                continue
        
        raise Exception("No supported API version found")

    def create_search_index(self) -> None:
        """Create the search index if it doesn't exist"""
        url = f"{self.search_endpoint}/indexes/{self.search_index_name}?api-version={self.api_version}"
        
        # Check if index exists
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                print(f"Search index '{self.search_index_name}' already exists")
                return
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response.status_code == 404:
                pass  # Index doesn't exist, proceed to create
            else:
                raise

        # Create index
        print(f"Creating search index '{self.search_index_name}'...")
        index_definition = {
            "name": self.search_index_name,
            "fields": [
                {
                    "name": "id",
                    "type": "Edm.String",
                    "key": True,
                    "searchable": False,
                    "filterable": False,
                    "facetable": False,
                    "sortable": False
                },
                {
                    "name": "url",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": True,
                    "facetable": False,
                    "sortable": False
                },
                {
                    "name": "title",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": True,
                    "facetable": False,
                    "sortable": True
                },
                {
                    "name": "content",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": False,
                    "facetable": False,
                    "sortable": False
                },
                {
                    "name": "category",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": True,
                    "facetable": True,
                    "sortable": True
                },
                {
                    "name": "keywords",
                    "type": "Collection(Edm.String)",
                    "searchable": True,
                    "filterable": True,
                    "facetable": True,
                    "sortable": False
                },
                {
                    "name": "description",
                    "type": "Edm.String",
                    "searchable": True,
                    "filterable": False,
                    "facetable": False,
                    "sortable": False
                }
            ]
        }

        # Only add vector fields if supported
        if self.api_version >= "2023-10-01-Preview":
            index_definition["fields"].append({
                "name": "vectorField",
                "type": "Collection(Edm.Single)",
                "dimensions": 1536,
                "vectorSearchProfile": "vector-profile"
            })
            index_definition["vectorSearch"] = {
                "profiles": [{
                    "name": "vector-profile",
                    "algorithm": "hnsw",
                    "algorithmConfiguration": "default"
                }],
                "algorithmConfigurations": [{
                    "name": "default",
                    "kind": "hnsw",
                    "parameters": {
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500,
                        "metric": "cosine"
                    }
                }]
            }

        # Only add semantic search if supported
        if self.api_version >= "2021-04-30-Preview":
            index_definition["semantic"] = {
                "configurations": [{
                    "name": "my-semantic-config",
                    "prioritizedFields": {
                        "titleField": {"fieldName": "title"},
                        "contentFields": [
                            {"fieldName": "content"},
                            {"fieldName": "description"}
                        ],
                        "keywordsFields": [{"fieldName": "keywords"}]
                    }
                }]
            }

        response = requests.put(url, json=index_definition, headers=self.headers)
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create index: {response.text}")
        
        print(f"Search index '{self.search_index_name}' created successfully")

    def upload_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Upload documents to the search index"""
        url = f"{self.search_endpoint}/indexes/{self.search_index_name}/docs/index?api-version={self.api_version}"
        
        # Prepare documents for upload
        actions = [{"@search.action": "upload", **doc} for doc in documents]
        
        # Upload in batches of 100
        batch_size = 100
        for i in range(0, len(actions), batch_size):
            batch = actions[i:i + batch_size]
            response = requests.post(url, json={"value": batch}, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to upload batch: {response.text}")
            
            print(f"Uploaded batch {i//batch_size + 1} of {len(actions)//batch_size + 1}")
        
        print("All documents uploaded successfully")

    def search_documents(self, query: str, filter_expr: Optional[str] = None) -> Dict[str, Any]:
        """Search for documents in the index"""
        url = f"{self.search_endpoint}/indexes/{self.search_index_name}/docs/search?api-version={self.api_version}"
        
        body = {
            "search": query,
            "queryType": "simple",
            "searchFields": "title,content,description,keywords",
            "select": "id,url,title,content,category,keywords,description",
            "count": True,
            "top": 10
        }
        
        if filter_expr:
            body["filter"] = filter_expr
        
        response = requests.post(url, json=body, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def vector_search(self, vector: List[float], filter_expr: Optional[str] = None) -> Dict[str, Any]:
        """Search using vector similarity"""
        url = f"{self.search_endpoint}/indexes/{self.search_index_name}/docs/search?api-version={self.api_version}"
        
        body = {
            "vectors": [{
                "value": vector,
                "fields": "vectorField",
                "k": 10
            }],
            "select": "id,url,title,content,category,keywords,description",
            "count": True
        }
        
        if filter_expr:
            body["filter"] = filter_expr
        
        response = requests.post(url, json=body, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def hybrid_search(self, query: str, vector: List[float], filter_expr: Optional[str] = None) -> Dict[str, Any]:
        """Combine keyword and vector search"""
        url = f"{self.search_endpoint}/indexes/{self.search_index_name}/docs/search?api-version={self.api_version}"
        
        body = {
            "search": query,
            "queryType": "simple",
            "searchFields": "title,content,description,keywords",
            "vectors": [{
                "value": vector,
                "fields": "vectorField",
                "k": 10
            }],
            "select": "id,url,title,content,category,keywords,description",
            "count": True,
            "top": 10
        }
        
        if filter_expr:
            body["filter"] = filter_expr
        
        response = requests.post(url, json=body, headers=self.headers)
        response.raise_for_status()
        return response.json()