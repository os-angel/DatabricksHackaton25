"""
Intent Classifier - Fast classification using 70b model
Determines query type and required resources
"""
import json
from typing import Dict, List, Optional
from enum import Enum

from databricks_genai import Completion
from config.settings import settings
from src.utils.logger import orchestrator_logger as logger


class QueryType(str, Enum):
    """Types of queries the system can handle"""
    SINGLE_DOMAIN = "single_domain"
    MULTI_DOMAIN = "multi_domain"
    SIMULATION = "simulation"
    CONVERSATIONAL = "conversational"
    CLARIFICATION_NEEDED = "clarification_needed"


class Domain(str, Enum):
    """Business domains"""
    SALES = "sales"
    FINANCE = "finance"
    STRATEGIC = "strategic"
    OPERATIONS = "operations"


class IntentClassifier:
    """
    Fast intent classification using lighter LLM model
    Determines what resources and Genies are needed
    """

    CLASSIFICATION_PROMPT = """You are an expert query classifier for an executive decision-making system.
Analyze the CEO's question and classify it into structured output.

Your task:
1. Identify the query type (single_domain, multi_domain, simulation, conversational, clarification_needed)
2. Identify relevant business domains (sales, finance, strategic, operations)
3. Determine if visualization is needed
4. Extract key parameters mentioned (time periods, metrics, quantities)
5. Identify which Genie spaces should be consulted

CEO Question: {question}

Conversation Context: {context}

Respond ONLY with valid JSON in this exact format:
{{
    "query_type": "single_domain|multi_domain|simulation|conversational|clarification_needed",
    "domains": ["sales", "finance", "strategic", "operations"],
    "primary_domain": "sales|finance|strategic|operations",
    "requires_visualization": true|false,
    "requires_simulation": true|false,
    "genies_to_call": ["sales_genie", "finance_genie", "strategic_genie"],
    "parameters": {{
        "time_period": "Q3 2024",
        "metrics": ["revenue", "profit"],
        "quantities": {{}},
        "entities": ["products", "regions"]
    }},
    "complexity_score": 1-10,
    "estimated_steps": 1-5,
    "clarification_needed": false,
    "clarification_questions": []
}}

Examples:

Question: "What were our sales in Q3?"
{{
    "query_type": "single_domain",
    "domains": ["sales"],
    "primary_domain": "sales",
    "requires_visualization": true,
    "requires_simulation": false,
    "genies_to_call": ["sales_genie"],
    "parameters": {{"time_period": "Q3", "metrics": ["sales"]}},
    "complexity_score": 2,
    "estimated_steps": 1,
    "clarification_needed": false,
    "clarification_questions": []
}}

Question: "If we open 5 new stores with $2M investment, what's the ROI?"
{{
    "query_type": "simulation",
    "domains": ["finance", "sales", "strategic"],
    "primary_domain": "finance",
    "requires_visualization": true,
    "requires_simulation": true,
    "genies_to_call": ["sales_genie", "finance_genie"],
    "parameters": {{"quantities": {{"num_stores": 5, "investment": 2000000}}, "metrics": ["roi"]}},
    "complexity_score": 8,
    "estimated_steps": 5,
    "clarification_needed": false,
    "clarification_questions": []
}}

Now classify the CEO's question."""

    def __init__(self):
        self.model = settings.models.classifier_model
        self.temperature = settings.models.classifier_temperature
        self.max_tokens = settings.models.classifier_max_tokens

    def classify(
        self,
        question: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Classify the user's question

        Args:
            question: The CEO's question
            conversation_context: Previous conversation messages

        Returns:
            Classification result as dictionary
        """
        logger.info(f"Classifying question: {question[:100]}...")

        # Format context
        context_str = self._format_context(conversation_context or [])

        # Build prompt
        prompt = self.CLASSIFICATION_PROMPT.format(
            question=question,
            context=context_str or "No previous context"
        )

        try:
            # Call Databricks Foundation Model
            response = Completion.create(
                model=self.model,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Parse response
            result_text = response.text.strip()

            # Extract JSON from response
            result = self._extract_json(result_text)

            # Validate and enhance
            result = self._validate_classification(result)

            logger.info(f"Classification: {result['query_type']} - Domains: {result['domains']}")
            return result

        except Exception as e:
            logger.error(f"Classification error: {e}", exc_info=True)
            # Return safe default
            return self._get_default_classification(question)

    def _format_context(self, context: List[Dict]) -> str:
        """Format conversation context for the prompt"""
        if not context:
            return ""

        formatted = []
        for msg in context[-3:]:  # Last 3 messages
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{role.upper()}: {content[:100]}")

        return "\n".join(formatted)

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        # Try to find JSON in the text
        text = text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        # Parse JSON
        return json.loads(text)

    def _validate_classification(self, result: Dict) -> Dict:
        """Validate and enhance classification result"""
        # Ensure required fields
        if "query_type" not in result:
            result["query_type"] = QueryType.SINGLE_DOMAIN

        if "domains" not in result or not result["domains"]:
            result["domains"] = [Domain.SALES]

        if "primary_domain" not in result:
            result["primary_domain"] = result["domains"][0]

        if "requires_visualization" not in result:
            result["requires_visualization"] = True

        if "requires_simulation" not in result:
            result["requires_simulation"] = result["query_type"] == QueryType.SIMULATION

        if "genies_to_call" not in result:
            result["genies_to_call"] = self._map_domains_to_genies(result["domains"])

        if "complexity_score" not in result:
            result["complexity_score"] = len(result["domains"]) * 2

        if "estimated_steps" not in result:
            result["estimated_steps"] = len(result["genies_to_call"])

        return result

    def _map_domains_to_genies(self, domains: List[str]) -> List[str]:
        """Map business domains to Genie space names"""
        mapping = {
            Domain.SALES: "sales_genie",
            Domain.FINANCE: "finance_genie",
            Domain.STRATEGIC: "strategic_genie",
            Domain.OPERATIONS: "sales_genie",  # Fallback
        }

        genies = []
        for domain in domains:
            if domain in mapping:
                genie = mapping[domain]
                if genie not in genies:
                    genies.append(genie)

        return genies or ["sales_genie"]

    def _get_default_classification(self, question: str) -> Dict:
        """Return safe default classification on error"""
        logger.warning("Using default classification")
        return {
            "query_type": QueryType.SINGLE_DOMAIN,
            "domains": [Domain.SALES],
            "primary_domain": Domain.SALES,
            "requires_visualization": True,
            "requires_simulation": False,
            "genies_to_call": ["sales_genie"],
            "parameters": {},
            "complexity_score": 3,
            "estimated_steps": 1,
            "clarification_needed": False,
            "clarification_questions": []
        }
