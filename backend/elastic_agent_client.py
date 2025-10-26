"""
Elastic AI Assistant / Agent Builder Integration for ScholarForge.
Integrates with paper_chaser_gamma and ScholarBot agents.
"""

import requests
from typing import Dict, Any, List, Optional
import logging
from backend import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElasticAgentClient:
    """Client for interacting with Elastic AI Assistant agents."""

    def __init__(self):
        """Initialize Elastic Agent client with MCP endpoint."""
        # Use the MCP agent builder endpoint
        self.mcp_url = "https://my-elasticsearch-project-cf6e91.kb.us-central1.gcp.elastic.cloud/api/agent_builder/mcp"
        self.base_url = config.ELASTIC_URL.replace(":443", "")
        self.api_key = config.ELASTIC_API_KEY
        self.headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",  # Required for MCP endpoint
            "kbn-xsrf": "true"  # Required for Kibana API
        }

        # Agent identifiers
        self.paper_chaser_id = "paper_chaser_gamma"
        self.scholarbot_name = "ScholarBot"

        logger.info("Initialized Elastic AI Assistant client with MCP endpoint")

    def chat_with_agent(
        self,
        message: str,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a message to an Elastic AI Assistant agent via MCP.

        Args:
            message: User message/query
            agent_id: Agent ID (e.g., "paper_chaser_gamma")
            agent_name: Agent name (e.g., "ScholarBot")
            conversation_id: Optional conversation ID for context

        Returns:
            Dictionary containing agent response
        """
        try:
            # Use paper_chaser_gamma by default
            if not agent_id and not agent_name:
                agent_id = self.paper_chaser_id

            logger.info(f"Sending message to MCP agent: {message[:50]}...")

            # Try MCP endpoint first
            payload = {
                "message": message,
                "agent_id": agent_id or agent_name
            }

            if conversation_id:
                payload["conversation_id"] = conversation_id

            response = requests.post(
                self.mcp_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logger.info("Successfully received MCP agent response")

                # Extract response text (format may vary)
                response_text = ""
                if isinstance(result, dict):
                    response_text = result.get("response") or result.get("message") or result.get("text") or str(result)
                else:
                    response_text = str(result)

                return {
                    "success": True,
                    "response": response_text,
                    "conversation_id": result.get("conversation_id") if isinstance(result, dict) else None,
                    "agent_id": agent_id or agent_name,
                    "raw_response": result
                }
            else:
                logger.warning(f"MCP request failed: {response.status_code} - {response.text[:200]}")

                # Fallback to original agent endpoint
                logger.info("Trying fallback agent endpoint...")
                return self._fallback_agent_request(message, agent_id, agent_name, conversation_id)

        except Exception as e:
            logger.error(f"Error communicating with MCP agent: {e}")
            # Try fallback
            return self._fallback_agent_request(message, agent_id, agent_name, conversation_id)

    def _fallback_agent_request(
        self,
        message: str,
        agent_id: Optional[str],
        agent_name: Optional[str],
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback to original agent endpoint if MCP fails."""
        try:
            url = f"{self.base_url}/_plugins/_ml/agents/_execute"

            payload = {
                "parameters": {
                    "question": message
                }
            }

            if agent_id:
                payload["agent_id"] = agent_id
            elif agent_name:
                payload["agent_name"] = agent_name

            if conversation_id:
                payload["conversation_id"] = conversation_id

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                logger.info("Successfully received fallback agent response")
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "conversation_id": result.get("conversation_id"),
                    "agent_id": agent_id or agent_name,
                    "raw_response": result
                }
            else:
                logger.error(f"Fallback agent request failed: {response.status_code}")
                return {
                    "success": False,
                    "error": f"Both MCP and fallback endpoints failed",
                    "response": "I apologize, but I'm having trouble connecting to the research agent. Please check the agent configuration."
                }

        except Exception as e:
            logger.error(f"Fallback agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Agent connection error: {str(e)}"
            }

    def chat_with_paper_chaser(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat with paper_chaser_gamma agent.

        Args:
            message: User query about papers
            conversation_id: Optional conversation context

        Returns:
            Agent response
        """
        return self.chat_with_agent(
            message=message,
            agent_id=self.paper_chaser_id,
            conversation_id=conversation_id
        )

    def chat_with_scholarbot(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat with ScholarBot agent.

        Args:
            message: User query about research
            conversation_id: Optional conversation context

        Returns:
            Agent response
        """
        return self.chat_with_agent(
            message=message,
            agent_name=self.scholarbot_name,
            conversation_id=conversation_id
        )

    def search_papers_with_agent(
        self,
        query: str,
        agent: str = "paper_chaser"
    ) -> List[Dict[str, Any]]:
        """
        Use agent to search for papers.

        Args:
            query: Research topic query
            agent: Which agent to use ("paper_chaser" or "scholarbot")

        Returns:
            List of papers found by agent
        """
        try:
            # Craft a query that asks the agent to find papers
            message = f"Find recent research papers about: {query}. Return at least 5 papers with their titles, authors, years, and sources."

            if agent == "scholarbot":
                response = self.chat_with_scholarbot(message)
            else:
                response = self.chat_with_paper_chaser(message)

            if response.get("success"):
                # Parse response to extract papers
                # Note: This depends on how the agent structures its response
                papers = self._parse_agent_papers(response.get("response", ""))
                return papers
            else:
                logger.warning(f"Agent search failed: {response.get('error')}")
                return []

        except Exception as e:
            logger.error(f"Error searching with agent: {e}")
            return []

    def _parse_agent_papers(self, agent_response: str) -> List[Dict[str, Any]]:
        """
        Parse papers from agent response.

        Args:
            agent_response: Text response from agent

        Returns:
            List of parsed paper dictionaries
        """
        # This is a basic parser - adjust based on actual agent response format
        papers = []

        # Try to extract structured data if available in raw_response
        # Otherwise, return the text response as-is for display

        # For now, return empty list - the chat interface will display the text
        # In production, you'd parse the agent's structured output

        return papers


# Singleton instance
_elastic_agent_client = None


def get_elastic_agent_client() -> ElasticAgentClient:
    """Get or create ElasticAgentClient singleton."""
    global _elastic_agent_client
    if _elastic_agent_client is None:
        _elastic_agent_client = ElasticAgentClient()
    return _elastic_agent_client
