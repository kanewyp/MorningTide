"""
LLM Integration Module for Ollama

Handles communication with local Ollama instance for generating
therapy suggestions and discussion prompts.
"""

import logging
import requests
import json
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama connection."""
    base_url: str = "http://localhost:11434"
    model: str = "mistral"
    temperature: float = 0.7
    top_p: float = 0.9
    num_predict: int = 512


class OllamaGenerator:
    """Wraps Ollama API for RAG-based LLM generation."""

    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize Ollama generator with configuration."""
        self.config = config or OllamaConfig()
        self.base_url = self.config.base_url. rstrip("/")
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify Ollama is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            logger.info("✓ Ollama connection verified")
        except requests.exceptions.RequestException as e:
            logger. error(
                f"✗ Cannot connect to Ollama at {self.base_url}: {e}"
            )
            raise RuntimeError(
                f"Ollama not accessible at {self.base_url}. "
                "Please ensure Ollama is running and accessible."
            )

    def build_system_prompt(self) -> str:
        """Build the system prompt for therapy discussion generation."""
        return """You are a supportive therapy assistant helping users prepare for 
their next session with their therapist. Your role is to:

1. Analyze the user's recent journal entries to understand their current challenges
2. Identify key themes and patterns in their emotional state
3. Suggest meaningful discussion topics for their therapy session
4. Generate actionable reflection prompts to deepen self-awareness
5. Provide context and suggestions grounded in evidence-based therapeutic approaches

Guidelines: 
- Be empathetic, non-judgmental, and supportive
- Focus on patterns and themes rather than surface-level issues
- Suggest concrete discussion topics the user can bring to therapy
- Provide evidence-based perspectives when appropriate
- Encourage self-reflection and deeper exploration
- Maintain appropriate professional boundaries (not replacing therapy)
- Keep suggestions practical and actionable

Format your response as a structured set of discussion topics and prompts."""

    def build_user_prompt(
        self,
        diary_context: str,
        retrieved_topics: List[Dict[str, str]]
    ) -> str:
        """Build the user prompt combining diary context and retrieved therapy topics."""
        prompt = f"""Based on the user's recent journal entries and relevant therapy topics, 
generate discussion prompts and suggestions for their upcoming therapy session. 

--- USER'S RECENT JOURNAL ENTRIES ---
{diary_context}

--- RELEVANT THERAPY TOPICS FOR CONTEXT ---
"""
        for i, topic in enumerate(retrieved_topics, 1):
            prompt += f"\n{i}. {topic. get('title', 'Untitled')}\n"
            prompt += f"   Category: {topic.get('category', 'General')}\n"
            prompt += f"   Context: {topic.get('content', '')[:200]}...\n"

        prompt += """
--- YOUR TASK ---
Generate 3-5 structured discussion topics that: 
1. Directly relate to the user's journal entries
2. Connect to evidence-based therapy concepts
3. Are actionable and meaningful for their next therapy session
4. Include specific reflection prompts the user can explore

Format the response as: 
DISCUSSION TOPIC [number]:  [Title]
- Context: [Why this topic matters based on their entries]
- Therapy Connection: [Related therapeutic approach]
- Discussion Prompt: [Specific question or reflection they can explore]
- Suggested Focus: [Area to focus on in session]

"""
        return prompt

    def generate_suggestions(
        self,
        diary_context: str,
        retrieved_topics: List[Dict[str, str]],
        stream: bool = False
    ) -> str:
        """
        Generate therapy suggestions using Ollama. 

        Args:
            diary_context: Combined user diary entries as context
            retrieved_topics: List of relevant therapy topics from vector store
            stream: Whether to stream response (True) or wait for completion

        Returns:
            Generated suggestions as string
        """
        system_prompt = self.build_system_prompt()
        user_prompt = self.build_user_prompt(diary_context, retrieved_topics)

        payload = {
            "model": self.config.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": stream,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "num_predict": self. config.num_predict,
        }

        try:
            response = requests.post(
                self.generate_endpoint,
                json=payload,
                timeout=120  # Generous timeout for model loading
            )
            response. raise_for_status()

            if stream:
                # Handle streaming response
                result = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            result += chunk.get("response", "")
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue
                return result
            else:
                # Handle complete response
                data = response.json()
                return data.get("response", "")

        except requests.exceptions. Timeout:
            logger.error("Ollama request timed out")
            raise RuntimeError(
                "LLM generation timed out. Model may be loading or busy."
            )
        except requests.exceptions.RequestException as e:
            logger. error(f"Ollama API error: {e}")
            raise RuntimeError(f"LLM generation failed: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            raise RuntimeError("Failed to parse LLM response")

    def health_check(self) -> Dict[str, Any]:
        """Check Ollama health and model availability."""
        try:
            # Check API availability
            api_response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            api_response.raise_for_status()

            # List available models
            models_data = api_response.json()
            models = [m["name"] for m in models_data. get("models", [])]

            model_available = any(
                self.config.model in model for model in models
            )

            return {
                "status": "healthy",
                "ollama_url": self.base_url,
                "configured_model": self.config.model,
                "model_available": model_available,
                "available_models": models,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "ollama_url": self.base_url,
                "timestamp": datetime.now().isoformat()
            }