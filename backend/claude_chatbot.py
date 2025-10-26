"""
Claude-powered chatbot with access to Elastic research papers.
Uses Claude API with function calling to search papers.
"""

import anthropic
from typing import Dict, Any, List, Optional
import logging
import json
from backend import config
from backend.elastic_client import get_elastic_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeChatbot:
    """Claude-powered chatbot with Elastic search capabilities."""

    def __init__(self):
        """Initialize Claude chatbot with Elastic access."""
        self.client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
        self.model = config.CLAUDE_MODEL
        self.elastic = get_elastic_client()
        logger.info(f"Initialized Claude chatbot with model: {self.model}")

    def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Chat with Claude, giving it access to search research papers.

        Args:
            message: User message
            conversation_history: Previous messages in conversation

        Returns:
            Dictionary with response and updated history
        """
        try:
            # Build conversation history
            messages = conversation_history or []
            messages.append({
                "role": "user",
                "content": message
            })

            # Define tools Claude can use
            tools = [
                {
                    "name": "search_papers",
                    "description": "Search for research papers in the database by topic, keywords, or query. Returns relevant papers with titles, authors, abstracts, and years.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query (e.g., 'quantum computing', 'transformer architectures', 'CRISPR')"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of papers to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_paper_details",
                    "description": "Get detailed information about a specific paper by its title or ID.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "The paper title to look up"
                            }
                        },
                        "required": ["title"]
                    }
                }
            ]

            # System prompt
            system_prompt = """You are a research assistant with access to a database of academic papers.
You can search for papers, provide summaries, explain research concepts, and help users discover relevant research.

When users ask about papers or research topics:
1. Use the search_papers tool to find relevant papers
2. Provide clear, concise summaries
3. Cite specific papers when possible (include authors and years)
4. Explain complex concepts in accessible language

Be helpful, accurate, and cite your sources."""

            # Call Claude with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=messages,
                tools=tools
            )

            # Handle tool use
            if response.stop_reason == "tool_use":
                # Claude wants to use a tool
                tool_results = []

                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_name = content_block.name
                        tool_input = content_block.input
                        tool_use_id = content_block.id

                        logger.info(f"Claude calling tool: {tool_name} with input: {tool_input}")

                        # Execute the tool
                        if tool_name == "search_papers":
                            result = self._search_papers(
                                tool_input.get("query"),
                                tool_input.get("max_results", 5)
                            )
                        elif tool_name == "get_paper_details":
                            result = self._get_paper_details(tool_input.get("title"))
                        else:
                            result = {"error": f"Unknown tool: {tool_name}"}

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result)
                        })

                # Add assistant's tool use to history
                messages.append({
                    "role": "assistant",
                    "content": response.content
                })

                # Add tool results
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

                # Get final response from Claude
                final_response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system_prompt,
                    messages=messages,
                    tools=tools
                )

                # Extract text response
                response_text = ""
                for block in final_response.content:
                    if hasattr(block, "text"):
                        response_text += block.text

                # Add final response to history
                messages.append({
                    "role": "assistant",
                    "content": response_text
                })

                return {
                    "success": True,
                    "response": response_text,
                    "conversation_history": messages
                }

            else:
                # Direct response without tools
                response_text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        response_text += block.text

                messages.append({
                    "role": "assistant",
                    "content": response_text
                })

                return {
                    "success": True,
                    "response": response_text,
                    "conversation_history": messages
                }

        except Exception as e:
            logger.error(f"Error in Claude chat: {e}")
            return {
                "success": False,
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "conversation_history": messages if messages else []
            }

    def _search_papers(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search for papers using Elastic."""
        try:
            papers = self.elastic.search_papers(query, size=max_results)

            results = []
            for paper in papers:
                results.append({
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", ""),
                    "year": paper.get("year", ""),
                    "abstract": paper.get("abstract", "")[:300] + "...",
                    "venue": paper.get("venue", ""),
                    "field": paper.get("field", "")
                })

            return {
                "found": len(results),
                "papers": results
            }

        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return {
                "error": str(e),
                "found": 0,
                "papers": []
            }

    def _get_paper_details(self, title: str) -> Dict[str, Any]:
        """Get details about a specific paper."""
        try:
            # Search for the specific paper
            papers = self.elastic.search_papers(title, size=1)

            if papers:
                paper = papers[0]
                return {
                    "found": True,
                    "title": paper.get("title", ""),
                    "authors": paper.get("authors", ""),
                    "year": paper.get("year", ""),
                    "abstract": paper.get("abstract", ""),
                    "venue": paper.get("venue", ""),
                    "field": paper.get("field", ""),
                    "url": paper.get("url", "")
                }
            else:
                return {
                    "found": False,
                    "error": f"Paper not found: {title}"
                }

        except Exception as e:
            logger.error(f"Error getting paper details: {e}")
            return {
                "found": False,
                "error": str(e)
            }


# Singleton instance
_claude_chatbot = None


def get_claude_chatbot() -> ClaudeChatbot:
    """Get or create ClaudeChatbot singleton."""
    global _claude_chatbot
    if _claude_chatbot is None:
        _claude_chatbot = ClaudeChatbot()
    return _claude_chatbot
