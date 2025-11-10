"""
Configuration settings for DecisionMakingArena
"""
import os
from typing import Optional
from pydantic import BaseModel, Field


class DatabricksConfig(BaseModel):
    """Databricks workspace configuration"""
    workspace_url: str = Field(default_factory=lambda: os.getenv("DATABRICKS_WORKSPACE_URL", ""))
    token: str = Field(default_factory=lambda: os.getenv("DATABRICKS_TOKEN", ""))
    warehouse_id: Optional[str] = Field(default_factory=lambda: os.getenv("DATABRICKS_WAREHOUSE_ID"))

    class Config:
        env_prefix = "DATABRICKS_"


class GenieConfig(BaseModel):
    """Genie Spaces configuration"""
    sales_genie_space_id: str = Field(default_factory=lambda: os.getenv("SALES_GENIE_SPACE_ID", ""))
    finance_genie_space_id: str = Field(default_factory=lambda: os.getenv("FINANCE_GENIE_SPACE_ID", ""))
    strategic_genie_space_id: str = Field(default_factory=lambda: os.getenv("STRATEGIC_GENIE_SPACE_ID", ""))

    class Config:
        env_prefix = "GENIE_"


class VectorSearchConfig(BaseModel):
    """Vector Search configuration"""
    endpoint_name: str = Field(default="decision_making_vs_endpoint")
    index_name: str = Field(default="decision_making_knowledge_base")
    embedding_model: str = Field(default="databricks-bge-large-en")

    class Config:
        env_prefix = "VECTOR_SEARCH_"


class ModelConfig(BaseModel):
    """LLM Model configuration"""
    # Master Orchestrator - Complex reasoning
    orchestrator_model: str = Field(default="databricks-meta-llama-3-1-405b-instruct")
    orchestrator_temperature: float = Field(default=0.7)
    orchestrator_max_tokens: int = Field(default=2000)

    # Intent Classifier - Fast classification
    classifier_model: str = Field(default="databricks-meta-llama-3-1-70b-instruct")
    classifier_temperature: float = Field(default=0.3)
    classifier_max_tokens: int = Field(default=500)

    # Optional: Data Analyzer
    analyzer_model: str = Field(default="databricks-meta-llama-3-1-70b-instruct")
    analyzer_temperature: float = Field(default=0.5)
    analyzer_max_tokens: int = Field(default=1500)

    class Config:
        env_prefix = "MODEL_"


class AppConfig(BaseModel):
    """Application configuration"""
    app_name: str = Field(default="DecisionMakingArena")
    app_version: str = Field(default="1.0.0")
    debug_mode: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    max_conversation_history: int = Field(default=10)
    enable_caching: bool = Field(default=True)
    cache_ttl_seconds: int = Field(default=300)


class Settings:
    """Main settings container"""
    def __init__(self):
        self.databricks = DatabricksConfig()
        self.genies = GenieConfig()
        self.vector_search = VectorSearchConfig()
        self.models = ModelConfig()
        self.app = AppConfig()

    def validate(self) -> tuple[bool, list[str]]:
        """Validate that required configurations are set"""
        errors = []

        if not self.databricks.workspace_url:
            errors.append("DATABRICKS_WORKSPACE_URL is required")
        if not self.databricks.token:
            errors.append("DATABRICKS_TOKEN is required")
        if not self.genies.sales_genie_space_id:
            errors.append("SALES_GENIE_SPACE_ID is required")
        if not self.genies.finance_genie_space_id:
            errors.append("FINANCE_GENIE_SPACE_ID is required")

        return len(errors) == 0, errors


# Global settings instance
settings = Settings()
