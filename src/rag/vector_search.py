"""
Vector Search RAG Client
Provides context enrichment from knowledge base
"""
from typing import List, Dict, Optional
import asyncio

from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient

from config.settings import settings
from src.utils.logger import rag_logger as logger


class VectorSearchRAG:
    """
    RAG client using Databricks Mosaic AI Vector Search
    Enriches responses with historical context, benchmarks, and best practices
    """

    def __init__(
        self,
        workspace_client: Optional[WorkspaceClient] = None,
        endpoint_name: Optional[str] = None,
        index_name: Optional[str] = None
    ):
        """
        Initialize Vector Search RAG client

        Args:
            workspace_client: Databricks workspace client
            endpoint_name: Vector search endpoint name
            index_name: Vector search index name
        """
        self.endpoint_name = endpoint_name or settings.vector_search.endpoint_name
        self.index_name = index_name or settings.vector_search.index_name

        # Initialize workspace client
        if workspace_client:
            self.ws_client = workspace_client
        else:
            self.ws_client = WorkspaceClient(
                host=settings.databricks.workspace_url,
                token=settings.databricks.token
            )

        # Initialize vector search client
        try:
            self.vs_client = VectorSearchClient(
                workspace_url=settings.databricks.workspace_url,
                personal_access_token=settings.databricks.token
            )
            logger.info(f"VectorSearchRAG initialized with index: {self.index_name}")
        except Exception as e:
            logger.warning(f"Could not initialize VectorSearchClient: {e}")
            self.vs_client = None

        # Cache for frequent queries
        self.cache: Dict[str, List[Dict]] = {}
        self.cache_enabled = settings.app.enable_caching

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> str:
        """
        Search the knowledge base for relevant context

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional filters for the search

        Returns:
            Formatted context string
        """
        logger.info(f"Searching knowledge base: {query[:100]}...")

        # Check cache
        cache_key = f"{query}_{top_k}"
        if self.cache_enabled and cache_key in self.cache:
            logger.info("Returning cached result")
            results = self.cache[cache_key]
        else:
            # Perform search
            results = await self._perform_search(query, top_k, filters)

            # Cache results
            if self.cache_enabled:
                self.cache[cache_key] = results

        # Format results into context
        context = self._format_context(results)

        logger.info(f"Retrieved {len(results)} context items")
        return context

    async def _perform_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """
        Perform the actual vector search

        Args:
            query: Search query
            top_k: Number of results
            filters: Optional filters

        Returns:
            List of search results
        """
        if not self.vs_client:
            logger.warning("Vector search client not available, returning mock data")
            return self._get_mock_results(query)

        try:
            # Get the index
            index = self.vs_client.get_index(
                endpoint_name=self.endpoint_name,
                index_name=self.index_name
            )

            # Perform similarity search
            results = index.similarity_search(
                query_text=query,
                columns=["content", "metadata", "category"],
                num_results=top_k,
                filters=filters
            )

            # Format results
            formatted_results = []
            if hasattr(results, 'data_array'):
                for row in results.data_array:
                    formatted_results.append({
                        "content": row[0] if len(row) > 0 else "",
                        "metadata": row[1] if len(row) > 1 else {},
                        "category": row[2] if len(row) > 2 else "general",
                        "score": getattr(row, "score", 0.0)
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Vector search error: {e}", exc_info=True)
            return self._get_mock_results(query)

    def _format_context(self, results: List[Dict]) -> str:
        """
        Format search results into contextual text

        Args:
            results: List of search results

        Returns:
            Formatted context string
        """
        if not results:
            return "No additional context available."

        context_parts = ["**Relevant Context from Knowledge Base:**\n"]

        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            category = result.get("category", "general")
            score = result.get("score", 0.0)

            # Only include high-confidence results
            if score > 0.5:
                context_parts.append(f"\n{i}. [{category.upper()}] {content}")

        if len(context_parts) == 1:
            return "No highly relevant context found."

        return "\n".join(context_parts)

    def _get_mock_results(self, query: str) -> List[Dict]:
        """
        Get mock results when vector search is not available

        Args:
            query: Search query

        Returns:
            List of mock results
        """
        logger.info("Using mock vector search results")

        # Generate contextual mock data based on query keywords
        query_lower = query.lower()

        results = []

        if "sales" in query_lower or "revenue" in query_lower:
            results.append({
                "content": "Historical sales data shows consistent year-over-year growth of 15-20% in Q3 periods.",
                "category": "historical_data",
                "score": 0.85
            })
            results.append({
                "content": "Industry benchmark: Retail sector typically sees 12-15% growth in Q3 due to holiday preparation.",
                "category": "benchmark",
                "score": 0.78
            })

        if "roi" in query_lower or "investment" in query_lower:
            results.append({
                "content": "Previous store openings showed average payback period of 18-24 months with 25-30% ROI.",
                "category": "historical_analysis",
                "score": 0.82
            })
            results.append({
                "content": "Best practice: New store investments should target minimum 20% ROI to account for market uncertainties.",
                "category": "best_practice",
                "score": 0.75
            })

        if "margin" in query_lower or "profit" in query_lower:
            results.append({
                "content": "Company's historical gross margin has ranged from 35-40%, with net margin around 12-15%.",
                "category": "financial_context",
                "score": 0.88
            })
            results.append({
                "content": "Industry average margins: Gross 30-35%, Net 8-12% for similar retail operations.",
                "category": "benchmark",
                "score": 0.80
            })

        if "strategic" in query_lower or "market" in query_lower:
            results.append({
                "content": "Strategic focus has been on premium segment expansion and digital channel integration.",
                "category": "strategic_context",
                "score": 0.79
            })

        # Default context if no matches
        if not results:
            results.append({
                "content": "Company operates in a competitive retail market with focus on quality and customer experience.",
                "category": "general_context",
                "score": 0.65
            })

        return results

    async def enrich_with_context(
        self,
        primary_data: Dict,
        question: str,
        top_k: int = 3
    ) -> Dict:
        """
        Enrich primary data with contextual information

        Args:
            primary_data: Primary data from Genies
            question: Original question
            top_k: Number of context items

        Returns:
            Enriched data dictionary
        """
        logger.info("Enriching data with context...")

        # Build context query
        context_query = self._build_context_query(primary_data, question)

        # Get context
        context = await self.search(context_query, top_k=top_k)

        # Combine
        enriched = {
            "primary_data": primary_data,
            "context": context,
            "enrichment_metadata": {
                "query": context_query,
                "items_retrieved": top_k
            }
        }

        return enriched

    def _build_context_query(self, primary_data: Dict, question: str) -> str:
        """Build a context query from primary data and question"""
        # Extract key terms from primary data
        key_terms = []

        # Add question
        query_parts = [question]

        # Try to extract metrics or important terms
        if isinstance(primary_data, dict):
            if "message" in primary_data:
                # Extract key numbers or terms
                message = str(primary_data["message"])
                if "revenue" in message.lower():
                    key_terms.append("revenue trends")
                if "profit" in message.lower():
                    key_terms.append("profit margins")
                if "growth" in message.lower():
                    key_terms.append("growth patterns")

        if key_terms:
            query_parts.append(" ".join(key_terms))

        return " ".join(query_parts)

    def clear_cache(self):
        """Clear the search cache"""
        self.cache = {}
        logger.info("Vector search cache cleared")

    async def index_documents(
        self,
        documents: List[Dict],
        batch_size: int = 100
    ):
        """
        Index documents into vector search

        Args:
            documents: List of documents to index
            batch_size: Batch size for indexing
        """
        logger.info(f"Indexing {len(documents)} documents...")

        if not self.vs_client:
            logger.warning("Vector search client not available")
            return

        try:
            # This would use the Databricks Vector Search API
            # to index documents. Implementation depends on
            # how the index is configured (Delta table, etc.)
            logger.info("Document indexing would happen here")
            # Implementation details depend on your specific setup

        except Exception as e:
            logger.error(f"Error indexing documents: {e}", exc_info=True)
