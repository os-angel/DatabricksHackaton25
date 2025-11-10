"""
DecisionMakingArena - Main Gradio Application
CEO Command Center Interface
"""
import gradio as gr
import asyncio
from typing import List, Tuple, Optional
import pandas as pd

from config.settings import settings
from src.orchestrator.master_orchestrator import MasterOrchestrator
from src.genies.genie_client import GenieClient
from src.rag.vector_search import VectorSearchRAG
from src.simulations.unity_catalog_functions import UnityCatalogFunctions
from src.visualizations.chart_generator import ChartGenerator
from src.utils.logger import ui_logger as logger


class DecisionMakingArena:
    """
    Main application class for DecisionMakingArena
    """

    def __init__(self):
        """Initialize the application"""
        logger.info("Initializing DecisionMakingArena...")

        # Initialize components
        try:
            self.genie_client = GenieClient()
            self.rag_client = VectorSearchRAG()
            self.simulation_engine = UnityCatalogFunctions()
            self.chart_generator = ChartGenerator()

            # Initialize orchestrator
            self.orchestrator = MasterOrchestrator(
                genie_client=self.genie_client,
                rag_client=self.rag_client,
                simulation_engine=self.simulation_engine
            )

            logger.info("Application initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing application: {e}", exc_info=True)
            raise

    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        logger.info("Creating Gradio interface...")

        with gr.Blocks(
            title="DecisionMakingArena - CEO Command Center",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as app:

            gr.Markdown("""
            # 🎯 DecisionMakingArena
            ### AI-Powered Executive Decision Support System

            Ask complex business questions, run simulations, and get executive-level insights powered by:
            - **Multi-Agent Orchestration** with Databricks Genies
            - **RAG-Enhanced Context** from Vector Search
            - **What-If Simulations** with Unity Catalog Functions
            """)

            with gr.Tabs() as tabs:
                # Tab 1: CEO Chat Interface
                with gr.Tab("💬 CEO Chat", id="chat"):
                    self._create_chat_tab()

                # Tab 2: Simulation Studio
                with gr.Tab("🔬 Simulation Studio", id="simulation"):
                    self._create_simulation_tab()

                # Tab 3: Live Dashboard
                with gr.Tab("📊 Live Dashboard", id="dashboard"):
                    self._create_dashboard_tab()

                # Tab 4: Analysis History
                with gr.Tab("📚 History", id="history"):
                    self._create_history_tab()

            # Footer
            gr.Markdown("""
            ---
            **Powered by:** Databricks Foundation Models | Genie | Vector Search | Unity Catalog

            *Built for Databricks Hackathon 2025*
            """)

        logger.info("Gradio interface created")
        return app

    def _create_chat_tab(self):
        """Create the CEO chat interface tab"""
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                    show_label=True,
                    avatar_images=("👔", "🤖")
                )

                with gr.Row():
                    question_input = gr.Textbox(
                        label="Ask a question",
                        placeholder="e.g., What were our Q3 sales? or If we open 5 new stores with $2M investment, what's the ROI?",
                        lines=2,
                        scale=4
                    )
                    submit_btn = gr.Button("🚀 Ask", variant="primary", scale=1)
                    clear_btn = gr.Button("🔄 Clear", scale=1)

                # Example questions
                gr.Examples(
                    examples=[
                        "What were our total sales in Q3 2024?",
                        "Compare our profit margins to industry benchmarks",
                        "If we open 5 new stores with $2M investment, what would be the ROI in 18 months?",
                        "What products are driving growth this quarter?",
                        "Forecast revenue for the next 6 months based on current trends"
                    ],
                    inputs=question_input,
                    label="Example Questions"
                )

            with gr.Column(scale=1):
                # Status and metadata
                status_box = gr.Textbox(
                    label="Status",
                    value="Ready",
                    interactive=False,
                    lines=2
                )

                thinking_box = gr.Textbox(
                    label="AI Thinking Process",
                    value="Waiting for question...",
                    interactive=False,
                    lines=5
                )

                sources_box = gr.Textbox(
                    label="Data Sources",
                    value="",
                    interactive=False,
                    lines=3
                )

                # Visualization panel
                chart_output = gr.Plot(label="Visualization")

        # Event handlers
        submit_btn.click(
            fn=self.handle_chat_message,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input, status_box, thinking_box, sources_box, chart_output]
        )

        question_input.submit(
            fn=self.handle_chat_message,
            inputs=[question_input, chatbot],
            outputs=[chatbot, question_input, status_box, thinking_box, sources_box, chart_output]
        )

        clear_btn.click(
            fn=lambda: ([], "", "Ready", "Waiting for question...", "", None),
            outputs=[chatbot, question_input, status_box, thinking_box, sources_box, chart_output]
        )

    def _create_simulation_tab(self):
        """Create the simulation studio tab"""
        gr.Markdown("### 🔬 What-If Scenario Analysis")

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("#### Scenario Parameters")

                simulation_type = gr.Dropdown(
                    choices=["ROI - New Store Opening", "Revenue Forecast", "Scenario Comparison"],
                    value="ROI - New Store Opening",
                    label="Simulation Type"
                )

                # ROI Parameters
                with gr.Group(visible=True) as roi_params:
                    num_stores = gr.Slider(
                        minimum=1, maximum=20, value=5, step=1,
                        label="Number of New Stores"
                    )
                    investment_per_store = gr.Number(
                        value=400000,
                        label="Investment per Store ($)"
                    )
                    avg_revenue = gr.Number(
                        value=800000,
                        label="Expected Annual Revenue per Store ($)"
                    )
                    cost_ratio = gr.Slider(
                        minimum=0.5, maximum=0.9, value=0.65, step=0.05,
                        label="Operating Cost Ratio"
                    )
                    forecast_months = gr.Slider(
                        minimum=6, maximum=36, value=18, step=6,
                        label="Forecast Period (months)"
                    )

                run_simulation_btn = gr.Button("🎯 Run Simulation", variant="primary")

            with gr.Column(scale=2):
                gr.Markdown("#### Simulation Results")

                simulation_output = gr.Markdown(value="Run a simulation to see results...")

                simulation_chart = gr.Plot(label="ROI Timeline")

                sensitivity_chart = gr.Plot(label="Sensitivity Analysis")

                export_btn = gr.Button("💾 Export Report")

        # Event handlers
        run_simulation_btn.click(
            fn=self.handle_roi_simulation,
            inputs=[num_stores, investment_per_store, avg_revenue, cost_ratio, forecast_months],
            outputs=[simulation_output, simulation_chart, sensitivity_chart]
        )

    def _create_dashboard_tab(self):
        """Create the live dashboard tab"""
        gr.Markdown("### 📊 Live Business Dashboard")

        with gr.Row():
            kpi1 = gr.HTML(value=self.chart_generator.create_kpi_card(
                value=12500000,
                title="YTD Revenue",
                trend="+15%",
                format_as="currency"
            ))
            kpi2 = gr.HTML(value=self.chart_generator.create_kpi_card(
                value=18.5,
                title="Net Margin",
                trend="+2.3%",
                format_as="percent"
            ))
            kpi3 = gr.HTML(value=self.chart_generator.create_kpi_card(
                value=1250,
                title="Active Customers",
                trend="+8%",
                format_as="number"
            ))

        with gr.Row():
            with gr.Column():
                revenue_trend = gr.Plot(label="Revenue Trend (Last 12 Months)")
            with gr.Column():
                product_mix = gr.Plot(label="Product Mix")

        refresh_btn = gr.Button("🔄 Refresh Dashboard")

        # Event handler
        refresh_btn.click(
            fn=self.refresh_dashboard,
            outputs=[kpi1, kpi2, kpi3, revenue_trend, product_mix]
        )

    def _create_history_tab(self):
        """Create the analysis history tab"""
        gr.Markdown("### 📚 Analysis History")

        history_table = gr.Dataframe(
            headers=["Timestamp", "Question", "Type", "Summary"],
            datatype=["str", "str", "str", "str"],
            label="Past Analyses"
        )

        with gr.Row():
            load_history_btn = gr.Button("📥 Load History")
            clear_history_btn = gr.Button("🗑️ Clear History")

        load_history_btn.click(
            fn=self.load_history,
            outputs=[history_table]
        )

    def handle_chat_message(
        self,
        question: str,
        chat_history: List[Tuple[str, str]]
    ) -> Tuple:
        """
        Handle a chat message

        Args:
            question: User's question
            chat_history: Previous chat messages

        Returns:
            Tuple of (updated_history, cleared_input, status, thinking, sources, chart)
        """
        if not question.strip():
            return chat_history, "", "Ready", "Waiting for question...", "", None

        logger.info(f"Handling question: {question}")

        try:
            # Update status
            status = "Processing..."
            thinking = "🔍 Classifying intent and planning execution..."

            # Add user message to chat
            chat_history = chat_history + [[question, None]]

            # Process question asynchronously
            result = asyncio.run(self.orchestrator.process_question(
                question=question,
                conversation_context=self._format_chat_history(chat_history)
            ))

            # Extract response
            response = result.response

            # Update chat history with response
            chat_history[-1][1] = response

            # Format thinking process
            thinking_text = self._format_thinking_process(result.metadata)

            # Extract sources
            sources_text = "\n".join([f"• {source}" for source in result.sources])

            # Create visualization if available
            chart = None
            if result.visualization_data:
                chart = self.chart_generator.create_chart(
                    data=result.visualization_data.get("data", {}),
                    chart_type=result.visualization_data.get("chart_type", "auto"),
                    title=f"Visualization for: {question[:50]}..."
                )

            return (
                chat_history,
                "",  # Clear input
                "✅ Complete",
                thinking_text,
                sources_text or "No external sources",
                chart
            )

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            error_msg = f"❌ Error: {str(e)}"
            chat_history[-1][1] = error_msg
            return chat_history, "", "Error", error_msg, "", None

    def handle_roi_simulation(
        self,
        num_stores: int,
        investment_per_store: float,
        avg_revenue: float,
        cost_ratio: float,
        forecast_months: int
    ) -> Tuple[str, Optional[gr.Plot], Optional[gr.Plot]]:
        """Handle ROI simulation"""
        logger.info(f"Running ROI simulation: {num_stores} stores, {forecast_months} months")

        try:
            # Run simulation
            result = self.simulation_engine.calculate_roi_new_stores(
                num_stores=num_stores,
                investment_per_store=investment_per_store,
                avg_revenue_per_store=avg_revenue,
                operational_cost_ratio=cost_ratio,
                forecast_months=forecast_months
            )

            # Format results as markdown
            output = f"""
            ## 📊 ROI Simulation Results

            ### Key Metrics
            - **ROI**: {result.roi_percentage}%
            - **Payback Period**: {result.payback_period_months} months
            - **Break-Even Month**: {result.break_even_month}
            - **Cumulative Profit (18mo)**: ${result.cumulative_profit_18mo:,.0f}
            - **NPV**: ${result.npv:,.0f}
            - **IRR**: {result.irr * 100:.2f}%

            ### Analysis
            Opening **{num_stores} new stores** with total investment of **${num_stores * investment_per_store:,.0f}**
            will generate an ROI of **{result.roi_percentage}%** over {forecast_months} months.

            The investment will break even in month **{result.break_even_month}**, with full payback in
            **{result.payback_period_months} months**.

            ### Recommendation
            {'✅ **RECOMMENDED** - Positive NPV and acceptable payback period.' if result.npv > 0 and result.payback_period_months < 24 else '⚠️ **CAUTION** - Review assumptions carefully.'}
            """

            # Create ROI timeline chart
            roi_chart = self.chart_generator.create_roi_timeline(
                data={
                    "monthly_cash_flow": result.monthly_cash_flow,
                    "initial_investment": num_stores * investment_per_store,
                    "break_even_month": result.break_even_month,
                    "roi_percentage": result.roi_percentage
                },
                title=f"ROI Timeline - {num_stores} Stores over {forecast_months} Months"
            )

            # Create sensitivity analysis
            sensitivity_data = self.simulation_engine.sensitivity_analysis(
                base_scenario={
                    "num_stores": num_stores,
                    "investment_per_store": investment_per_store,
                    "avg_revenue": avg_revenue,
                    "cost_ratio": cost_ratio
                },
                variables_to_test=["num_stores", "avg_revenue", "cost_ratio"]
            )

            sensitivity_chart = self.chart_generator.create_sensitivity_chart(
                data=sensitivity_data,
                title="Sensitivity Analysis"
            )

            return output, roi_chart, sensitivity_chart

        except Exception as e:
            logger.error(f"Simulation error: {e}", exc_info=True)
            return f"❌ Error running simulation: {str(e)}", None, None

    def refresh_dashboard(self) -> Tuple:
        """Refresh dashboard data"""
        logger.info("Refreshing dashboard...")

        # Mock data for demo
        kpi1 = self.chart_generator.create_kpi_card(
            value=12500000,
            title="YTD Revenue",
            trend="+15%",
            format_as="currency"
        )

        kpi2 = self.chart_generator.create_kpi_card(
            value=18.5,
            title="Net Margin",
            trend="+2.3%",
            format_as="percent"
        )

        kpi3 = self.chart_generator.create_kpi_card(
            value=1250,
            title="Active Customers",
            trend="+8%",
            format_as="number"
        )

        # Revenue trend
        revenue_data = {
            "Revenue": [800000, 850000, 900000, 920000, 950000, 980000,
                       1000000, 1050000, 1100000, 1150000, 1200000, 1250000]
        }
        revenue_chart = self.chart_generator.create_line_chart(
            data=revenue_data,
            title="Revenue Trend (Last 12 Months)",
            ylabel="Revenue ($)"
        )

        # Product mix
        product_data = {
            "Product A": 3500000,
            "Product B": 2800000,
            "Product C": 2200000,
            "Product D": 2000000,
            "Other": 2000000
        }
        product_chart = self.chart_generator.create_pie_chart(
            data=product_data,
            title="Product Mix"
        )

        return kpi1, kpi2, kpi3, revenue_chart, product_chart

    def load_history(self) -> pd.DataFrame:
        """Load conversation history"""
        history = self.orchestrator.get_conversation_history()

        if not history:
            return pd.DataFrame(columns=["Timestamp", "Question", "Type", "Summary"])

        # Format for display
        df_data = []
        for msg in history:
            if msg["role"] == "user":
                df_data.append({
                    "Timestamp": msg["timestamp"],
                    "Question": msg["content"][:100],
                    "Type": "Query",
                    "Summary": "..."
                })

        return pd.DataFrame(df_data)

    def _format_chat_history(self, chat_history: List[Tuple[str, str]]) -> List[dict]:
        """Format chat history for orchestrator"""
        formatted = []
        for user_msg, assistant_msg in chat_history:
            if user_msg:
                formatted.append({"role": "user", "content": user_msg})
            if assistant_msg:
                formatted.append({"role": "assistant", "content": assistant_msg})
        return formatted

    def _format_thinking_process(self, metadata: dict) -> str:
        """Format thinking process for display"""
        classification = metadata.get("classification", {})
        steps = metadata.get("steps_executed", 0)
        duration = metadata.get("duration_seconds", 0)

        thinking = f"""
        **Classification:**
        - Type: {classification.get('query_type', 'unknown')}
        - Domains: {', '.join(classification.get('domains', []))}
        - Complexity: {classification.get('complexity_score', 0)}/10

        **Execution:**
        - Steps: {steps}
        - Duration: {duration:.2f}s
        """

        return thinking.strip()

    def _get_custom_css(self) -> str:
        """Get custom CSS for the interface"""
        return """
        .gradio-container {
            font-family: 'Inter', sans-serif;
        }
        .gr-button-primary {
            background-color: #1f77b4 !important;
            border-color: #1f77b4 !important;
        }
        """

    def launch(self, **kwargs):
        """Launch the Gradio app"""
        app = self.create_interface()
        logger.info("Launching application...")
        app.launch(**kwargs)


def main():
    """Main entry point"""
    logger.info("Starting DecisionMakingArena...")

    # Validate configuration
    is_valid, errors = settings.validate()
    if not is_valid:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  - {error}")
        logger.warning("Some features may not work without proper configuration")

    # Create and launch app
    app = DecisionMakingArena()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=settings.app.debug_mode
    )


if __name__ == "__main__":
    main()
