"""
Databricks Genie Client
Handles communication with Genie Spaces
"""
import asyncio
import time
from typing import Dict, List, Optional, Any
from enum import Enum

import requests
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieMessage

from config.settings import settings
from src.utils.logger import genie_logger as logger


class GenieSpaceType(str, Enum):
    """Types of Genie spaces"""
    SALES = "sales_genie"
    FINANCE = "finance_genie"
    STRATEGIC = "strategic_genie"


class GenieClient:
    """
    Client for interacting with Databricks Genie Spaces
    Handles conversation management and query execution
    """

    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        """
        Initialize Genie Client

        Args:
            workspace_client: Databricks workspace client (optional)
        """
        if workspace_client:
            self.client = workspace_client
        else:
            # Create client from config
            self.client = WorkspaceClient(
                host=settings.databricks.workspace_url,
                token=settings.databricks.token
            )

        # Map of genie names to space IDs
        self.genie_spaces = {
            GenieSpaceType.SALES: settings.genies.sales_genie_space_id,
            GenieSpaceType.FINANCE: settings.genies.finance_genie_space_id,
            GenieSpaceType.STRATEGIC: settings.genies.strategic_genie_space_id,
        }

        # Active conversations (for context)
        self.conversations: Dict[str, str] = {}  # genie_name -> conversation_id

        logger.info("GenieClient initialized")

    async def query(
        self,
        genie_name: str,
        question: str,
        conversation_id: Optional[str] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Query a Genie space

        Args:
            genie_name: Name of the genie (sales_genie, finance_genie, etc.)
            question: Question to ask
            conversation_id: Optional conversation ID for context
            timeout: Timeout in seconds

        Returns:
            Dictionary with response and metadata
        """
        logger.info(f"Querying {genie_name}: {question[:100]}...")

        try:
            # Get space ID
            space_id = self._get_space_id(genie_name)

            if not space_id:
                logger.error(f"Space ID not configured for {genie_name}")
                return {
                    "success": False,
                    "error": f"Genie space {genie_name} not configured",
                    "message": "Please configure the Genie space ID"
                }

            # Start conversation if needed
            if not conversation_id:
                conversation_id = self._get_or_create_conversation(genie_name, space_id)

            # Send message to Genie
            response = await self._send_message(
                space_id=space_id,
                conversation_id=conversation_id,
                question=question,
                timeout=timeout
            )

            logger.info(f"Genie {genie_name} response received")
            return response

        except Exception as e:
            logger.error(f"Error querying {genie_name}: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "message": "Unable to get response from Genie"
            }

    async def _send_message(
        self,
        space_id: str,
        conversation_id: str,
        question: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        Send a message to Genie and wait for response

        Args:
            space_id: Genie space ID
            conversation_id: Conversation ID
            question: Question to ask
            timeout: Timeout in seconds

        Returns:
            Response dictionary
        """
        try:
            # Create message
            message = self.client.genie.start_conversation(
                space_id=space_id,
                content=question
            )

            # Wait for response (poll for completion)
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Get message status
                message_status = self.client.genie.get_message(
                    space_id=space_id,
                    conversation_id=message.conversation_id,
                    message_id=message.id
                )

                if message_status.status == "COMPLETED":
                    # Extract response
                    response_text = self._extract_response(message_status)

                    # Extract data if available
                    data = self._extract_data(message_status)

                    return {
                        "success": True,
                        "message": response_text,
                        "data": data,
                        "conversation_id": message.conversation_id,
                        "message_id": message.id,
                        "metadata": {
                            "space_id": space_id,
                            "query_time": time.time() - start_time
                        }
                    }

                elif message_status.status == "FAILED":
                    error_msg = getattr(message_status, "error_message", "Unknown error")
                    return {
                        "success": False,
                        "error": error_msg,
                        "message": f"Genie query failed: {error_msg}"
                    }

                # Wait before polling again
                await asyncio.sleep(2)

            # Timeout
            return {
                "success": False,
                "error": "Timeout",
                "message": "Genie query timed out"
            }

        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            raise

    def _get_or_create_conversation(self, genie_name: str, space_id: str) -> str:
        """Get existing conversation or create new one"""
        if genie_name in self.conversations:
            return self.conversations[genie_name]

        # Create new conversation
        # In the actual API, conversations are created automatically with first message
        # We'll store a placeholder
        conversation_id = f"conv_{genie_name}_{int(time.time())}"
        self.conversations[genie_name] = conversation_id

        return conversation_id

    def _get_space_id(self, genie_name: str) -> Optional[str]:
        """Get space ID for a genie"""
        return self.genie_spaces.get(genie_name)

    def _extract_response(self, message_status: GenieMessage) -> str:
        """Extract text response from message status"""
        # The response is in the message content or attachments
        if hasattr(message_status, "content"):
            return message_status.content

        # Try to extract from attachments
        if hasattr(message_status, "attachments"):
            for attachment in message_status.attachments:
                if hasattr(attachment, "text"):
                    return attachment.text

        return "No response content available"

    def _extract_data(self, message_status: GenieMessage) -> Optional[Dict]:
        """Extract structured data from message (if available)"""
        # If Genie returns query results, they might be in attachments
        if hasattr(message_status, "query_result"):
            return self._format_query_result(message_status.query_result)

        return None

    def _format_query_result(self, query_result: Any) -> Dict:
        """Format SQL query results into structured data"""
        # This depends on the structure of query results from Databricks
        try:
            if hasattr(query_result, "data_array"):
                return {
                    "columns": query_result.column_names if hasattr(query_result, "column_names") else [],
                    "rows": query_result.data_array,
                    "row_count": len(query_result.data_array)
                }
        except Exception as e:
            logger.warning(f"Could not format query result: {e}")

        return {"raw": str(query_result)}

    async def query_parallel(
        self,
        queries: List[Dict[str, str]],
        timeout: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Query multiple Genies in parallel

        Args:
            queries: List of query dictionaries with 'genie_name' and 'question'
            timeout: Timeout per query

        Returns:
            List of response dictionaries
        """
        logger.info(f"Executing {len(queries)} parallel queries...")

        tasks = [
            self.query(
                genie_name=q["genie_name"],
                question=q["question"],
                timeout=timeout
            )
            for q in queries
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        formatted_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Query {i} failed: {result}")
                formatted_results.append({
                    "success": False,
                    "error": str(result),
                    "query": queries[i]
                })
            else:
                formatted_results.append(result)

        return formatted_results

    def clear_conversation(self, genie_name: str):
        """Clear conversation history for a genie"""
        if genie_name in self.conversations:
            del self.conversations[genie_name]
            logger.info(f"Cleared conversation for {genie_name}")

    def clear_all_conversations(self):
        """Clear all conversation histories"""
        self.conversations = {}
        logger.info("Cleared all conversations")
