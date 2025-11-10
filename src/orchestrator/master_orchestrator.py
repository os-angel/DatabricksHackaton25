"""
Master Orchestrator - Brain of DecisionMakingArena
Coordinates Genies, RAG, Simulations, and Response Synthesis
"""
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from databricks_genai import Completion
from config.settings import settings
from src.utils.logger import orchestrator_logger as logger
from src.orchestrator.intent_classifier import IntentClassifier, QueryType


@dataclass
class ConversationMessage:
    """A message in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class OrchestratorResult:
    """Result from orchestrator processing"""
    response: str
    visualization_data: Optional[Dict] = None
    sources: List[str] = field(default_factory=list)
    execution_plan: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


class MasterOrchestrator:
    """
    Master Orchestrator - Cerebro Principal

    Responsibilities:
    1. Receive CEO questions
    2. Decompose complex queries into sub-tasks
    3. Decide which Genie(s) to consult
    4. Enrich responses with RAG Vector Search
    5. Synthesize final executive response
    """

    PLANNING_PROMPT = """You are the Master Orchestrator for an executive AI system.
Your role is to create an execution plan for answering the CEO's question.

CEO Question: {question}

Intent Classification:
{classification}

Available Resources:
- Sales Genie: Can answer questions about sales data, products, customers, revenue
- Finance Genie: Can answer questions about financial data, margins, costs, ROI
- Strategic Genie: Can answer questions about strategy, market positioning, competition
- Vector Search: Can provide historical context, benchmarks, best practices
- Simulation Engine: Can run what-if scenarios and ROI calculations

Your task:
1. Break down the question into specific sub-queries if needed
2. Determine the optimal order of execution (parallel or sequential)
3. Identify what data each resource should provide
4. Plan how to synthesize the final response

Respond with a JSON execution plan:
{{
    "strategy": "simple|multi_step|simulation",
    "steps": [
        {{
            "step_number": 1,
            "action": "query_genie|query_rag|run_simulation",
            "resource": "sales_genie|finance_genie|vector_search|simulation",
            "query": "specific question to ask",
            "depends_on": [],
            "parallel_with": [2, 3]
        }}
    ],
    "synthesis_approach": "Description of how to combine results",
    "expected_outputs": ["revenue data", "trend analysis", "recommendations"]
}}

Create the execution plan now."""

    SYNTHESIS_PROMPT = """You are synthesizing information for a CEO.

Original Question: {question}

Execution Results:
{results}

RAG Context (Historical/Benchmarks):
{rag_context}

Your task:
Create a concise, executive-level response that:
1. Directly answers the question
2. Provides key insights and context
3. Highlights important trends or anomalies
4. Offers actionable recommendations if applicable
5. Uses business language (avoid technical jargon)

Structure:
- **Summary**: One-sentence answer
- **Details**: 2-3 paragraphs with key insights
- **Context**: Relevant historical or benchmark comparisons
- **Recommendation**: Action items or considerations (if applicable)

Response:"""

    def __init__(
        self,
        genie_client=None,
        rag_client=None,
        simulation_engine=None
    ):
        """
        Initialize the Master Orchestrator

        Args:
            genie_client: Client for Databricks Genies
            rag_client: Client for Vector Search RAG
            simulation_engine: Engine for simulations
        """
        self.intent_classifier = IntentClassifier()
        self.genie_client = genie_client
        self.rag_client = rag_client
        self.simulation_engine = simulation_engine

        self.model = settings.models.orchestrator_model
        self.temperature = settings.models.orchestrator_temperature
        self.max_tokens = settings.models.orchestrator_max_tokens

        self.conversation_history: List[ConversationMessage] = []

    async def process_question(
        self,
        question: str,
        conversation_context: Optional[List[Dict]] = None
    ) -> OrchestratorResult:
        """
        Main entry point - process a CEO question

        Args:
            question: The CEO's question
            conversation_context: Previous conversation messages

        Returns:
            OrchestratorResult with response and metadata
        """
        logger.info(f"Processing question: {question[:100]}...")
        start_time = datetime.now()

        try:
            # Step 1: Classify intent
            classification = self.intent_classifier.classify(
                question,
                conversation_context
            )
            logger.info(f"Intent: {classification['query_type']}")

            # Step 2: Create execution plan
            execution_plan = await self._create_execution_plan(
                question,
                classification
            )
            logger.info(f"Execution plan: {len(execution_plan['steps'])} steps")

            # Step 3: Execute plan
            execution_results = await self._execute_plan(
                execution_plan,
                question,
                classification
            )

            # Step 4: Gather RAG context
            rag_context = await self._gather_rag_context(
                question,
                classification,
                execution_results
            )

            # Step 5: Synthesize final response
            final_response = await self._synthesize_response(
                question,
                execution_results,
                rag_context
            )

            # Step 6: Generate visualizations if needed
            viz_data = None
            if classification.get("requires_visualization"):
                viz_data = self._prepare_visualization_data(
                    execution_results,
                    classification
                )

            # Record conversation
            self._add_to_history("user", question)
            self._add_to_history("assistant", final_response)

            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Question processed in {duration:.2f}s")

            return OrchestratorResult(
                response=final_response,
                visualization_data=viz_data,
                sources=self._extract_sources(execution_results),
                execution_plan=execution_plan,
                metadata={
                    "classification": classification,
                    "duration_seconds": duration,
                    "steps_executed": len(execution_plan["steps"])
                }
            )

        except Exception as e:
            logger.error(f"Error processing question: {e}", exc_info=True)
            return OrchestratorResult(
                response=f"I apologize, but I encountered an error processing your question: {str(e)}",
                metadata={"error": str(e)}
            )

    async def _create_execution_plan(
        self,
        question: str,
        classification: Dict
    ) -> Dict:
        """
        Create an execution plan for the question

        Args:
            question: The CEO's question
            classification: Intent classification result

        Returns:
            Execution plan dictionary
        """
        logger.info("Creating execution plan...")

        # For simple queries, use a simple plan
        if classification["query_type"] == QueryType.SINGLE_DOMAIN:
            return self._create_simple_plan(classification)

        # For complex queries, use LLM to plan
        prompt = self.PLANNING_PROMPT.format(
            question=question,
            classification=self._format_classification(classification)
        )

        try:
            response = Completion.create(
                model=self.model,
                prompt=prompt,
                temperature=0.5,  # Lower for more consistent planning
                max_tokens=1000
            )

            plan_text = response.text.strip()
            # Extract JSON
            import json
            plan = json.loads(self._extract_json_from_text(plan_text))
            return plan

        except Exception as e:
            logger.warning(f"Error creating LLM plan, using fallback: {e}")
            return self._create_fallback_plan(classification)

    def _create_simple_plan(self, classification: Dict) -> Dict:
        """Create a simple execution plan for single-domain queries"""
        genie = classification["genies_to_call"][0]

        return {
            "strategy": "simple",
            "steps": [
                {
                    "step_number": 1,
                    "action": "query_genie",
                    "resource": genie,
                    "query": "original_question",
                    "depends_on": [],
                    "parallel_with": []
                },
                {
                    "step_number": 2,
                    "action": "query_rag",
                    "resource": "vector_search",
                    "query": "context_for_results",
                    "depends_on": [1],
                    "parallel_with": []
                }
            ],
            "synthesis_approach": "Enhance Genie response with RAG context",
            "expected_outputs": ["data", "context"]
        }

    def _create_fallback_plan(self, classification: Dict) -> Dict:
        """Create a fallback plan when LLM planning fails"""
        steps = []
        step_num = 1

        # Add Genie queries
        for genie in classification["genies_to_call"]:
            steps.append({
                "step_number": step_num,
                "action": "query_genie",
                "resource": genie,
                "query": "original_question",
                "depends_on": [],
                "parallel_with": []
            })
            step_num += 1

        # Add RAG query
        steps.append({
            "step_number": step_num,
            "action": "query_rag",
            "resource": "vector_search",
            "query": "context",
            "depends_on": list(range(1, step_num)),
            "parallel_with": []
        })

        return {
            "strategy": "multi_step",
            "steps": steps,
            "synthesis_approach": "Combine all results with context",
            "expected_outputs": ["data", "analysis", "context"]
        }

    async def _execute_plan(
        self,
        plan: Dict,
        question: str,
        classification: Dict
    ) -> Dict[str, Any]:
        """
        Execute the plan steps

        Args:
            plan: Execution plan
            question: Original question
            classification: Intent classification

        Returns:
            Dictionary of execution results
        """
        logger.info(f"Executing plan with {len(plan['steps'])} steps...")

        results = {}
        completed_steps = set()

        for step in plan["steps"]:
            step_num = step["step_number"]

            # Check dependencies
            if not all(dep in completed_steps for dep in step.get("depends_on", [])):
                logger.warning(f"Step {step_num} dependencies not met, skipping")
                continue

            # Execute step
            try:
                if step["action"] == "query_genie":
                    result = await self._query_genie(
                        step["resource"],
                        question,
                        classification
                    )
                    results[f"genie_{step['resource']}"] = result

                elif step["action"] == "query_rag":
                    result = await self._query_rag(
                        question,
                        classification,
                        results
                    )
                    results["rag_context"] = result

                elif step["action"] == "run_simulation":
                    result = await self._run_simulation(
                        question,
                        classification,
                        results
                    )
                    results["simulation"] = result

                completed_steps.add(step_num)
                logger.info(f"Completed step {step_num}: {step['action']}")

            except Exception as e:
                logger.error(f"Error in step {step_num}: {e}", exc_info=True)
                results[f"error_step_{step_num}"] = str(e)

        return results

    async def _query_genie(
        self,
        genie_name: str,
        question: str,
        classification: Dict
    ) -> Dict:
        """Query a Genie space"""
        logger.info(f"Querying {genie_name}...")

        if not self.genie_client:
            return {"error": "Genie client not configured", "message": "Sample data response"}

        try:
            # Call Genie API
            response = await self.genie_client.query(
                genie_name=genie_name,
                question=question
            )
            return response

        except Exception as e:
            logger.error(f"Genie query error: {e}")
            return {"error": str(e), "message": "Unable to fetch data"}

    async def _query_rag(
        self,
        question: str,
        classification: Dict,
        execution_results: Dict
    ) -> str:
        """Query Vector Search for context"""
        logger.info("Querying RAG for context...")

        if not self.rag_client:
            return "Sample context: Historical data shows consistent growth trends."

        try:
            # Build context query
            context_query = self._build_rag_query(question, classification, execution_results)

            # Query vector search
            context = await self.rag_client.search(
                query=context_query,
                top_k=5
            )

            return context

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return "Context unavailable"

    async def _run_simulation(
        self,
        question: str,
        classification: Dict,
        execution_results: Dict
    ) -> Dict:
        """Run a simulation"""
        logger.info("Running simulation...")

        if not self.simulation_engine:
            return {"error": "Simulation engine not configured"}

        try:
            # Extract simulation parameters
            params = classification.get("parameters", {}).get("quantities", {})

            # Run simulation
            result = await self.simulation_engine.run(
                scenario_type="roi_analysis",
                parameters=params,
                context_data=execution_results
            )

            return result

        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return {"error": str(e)}

    async def _gather_rag_context(
        self,
        question: str,
        classification: Dict,
        execution_results: Dict
    ) -> str:
        """Gather RAG context for synthesis"""
        # Already gathered in execution if RAG step was included
        if "rag_context" in execution_results:
            return execution_results["rag_context"]

        # Otherwise, query now
        return await self._query_rag(question, classification, execution_results)

    async def _synthesize_response(
        self,
        question: str,
        execution_results: Dict,
        rag_context: str
    ) -> str:
        """
        Synthesize final executive response

        Args:
            question: Original question
            execution_results: Results from execution steps
            rag_context: Context from RAG

        Returns:
            Final synthesized response
        """
        logger.info("Synthesizing final response...")

        # Format results
        formatted_results = self._format_execution_results(execution_results)

        # Build synthesis prompt
        prompt = self.SYNTHESIS_PROMPT.format(
            question=question,
            results=formatted_results,
            rag_context=rag_context or "No additional context available"
        )

        try:
            response = Completion.create(
                model=self.model,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Synthesis error: {e}", exc_info=True)
            # Return basic synthesis
            return self._basic_synthesis(question, execution_results)

    def _format_execution_results(self, results: Dict) -> str:
        """Format execution results for synthesis"""
        formatted = []

        for key, value in results.items():
            if isinstance(value, dict):
                if "error" in value:
                    formatted.append(f"❌ {key}: {value.get('message', 'Error')}")
                else:
                    formatted.append(f"✓ {key}:\n{self._format_dict(value)}")
            else:
                formatted.append(f"✓ {key}: {value}")

        return "\n\n".join(formatted)

    def _format_dict(self, d: Dict, indent: int = 2) -> str:
        """Format dictionary for display"""
        lines = []
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{' ' * indent}{k}:")
                lines.append(self._format_dict(v, indent + 2))
            else:
                lines.append(f"{' ' * indent}{k}: {v}")
        return "\n".join(lines)

    def _basic_synthesis(self, question: str, results: Dict) -> str:
        """Basic synthesis when LLM fails"""
        response_parts = [f"Regarding your question: '{question}'\n"]

        for key, value in results.items():
            if isinstance(value, dict) and "message" in value:
                response_parts.append(f"• {key}: {value['message']}")
            elif not isinstance(value, dict):
                response_parts.append(f"• {key}: {value}")

        return "\n".join(response_parts)

    def _prepare_visualization_data(
        self,
        execution_results: Dict,
        classification: Dict
    ) -> Optional[Dict]:
        """Prepare data for visualization"""
        # This will be handled by the visualization module
        return {
            "chart_type": "auto",  # Let visualizer decide
            "data": execution_results,
            "classification": classification
        }

    def _extract_sources(self, execution_results: Dict) -> List[str]:
        """Extract data sources from execution results"""
        sources = []
        for key in execution_results.keys():
            if key.startswith("genie_"):
                sources.append(key.replace("genie_", "").replace("_", " ").title())
        if "rag_context" in execution_results:
            sources.append("Knowledge Base")
        if "simulation" in execution_results:
            sources.append("Simulation Engine")
        return sources

    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        msg = ConversationMessage(role=role, content=content)
        self.conversation_history.append(msg)

        # Trim history if too long
        max_history = settings.app.max_conversation_history
        if len(self.conversation_history) > max_history * 2:
            self.conversation_history = self.conversation_history[-(max_history * 2):]

    def _format_classification(self, classification: Dict) -> str:
        """Format classification for prompt"""
        return "\n".join([f"- {k}: {v}" for k, v in classification.items()])

    def _build_rag_query(
        self,
        question: str,
        classification: Dict,
        execution_results: Dict
    ) -> str:
        """Build a query for RAG based on context"""
        # Combine question with key terms from classification
        terms = []
        if "parameters" in classification:
            params = classification["parameters"]
            if "time_period" in params:
                terms.append(params["time_period"])
            if "metrics" in params:
                terms.extend(params["metrics"])

        query_parts = [question]
        if terms:
            query_parts.append("Related to: " + ", ".join(terms))

        return " ".join(query_parts)

    def _extract_json_from_text(self, text: str) -> str:
        """Extract JSON from text that might have markdown or other wrapping"""
        text = text.strip()

        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        return text.strip()

    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.conversation_history
        ]

    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
