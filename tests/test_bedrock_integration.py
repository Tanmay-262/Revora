import pytest
from backend.llm.bedrock_client import BedrockLLMClient
from backend.llm.explainability import LLMExplainer
from backend.llm.bedrock_extraction import BedrockDatabaseExtractor
from backend.db.database import SessionLocal

def test_bedrock_client_initialization():
    client = BedrockLLMClient(region_name="us-east-1", model_id="anthropic.claude-3-haiku-20240307-v1:0")
    assert client.region_name == "us-east-1"
    assert client.model_id == "anthropic.claude-3-haiku-20240307-v1:0"

def test_llm_explainer_bedrock_routing():
    explainer = LLMExplainer()
    provider_name = explainer.get_active_provider_name()
    assert provider_name is not None
    assert "Bedrock" in provider_name or "Gemini" in provider_name or "Fallback" in provider_name

def test_bedrock_extraction_with_db():
    db = SessionLocal()
    try:
        extractor = BedrockDatabaseExtractor(db)
        res = extractor.extract_database_insights("Extract high value failed transactions")
        assert "query" in res
        assert "extracted_data" in res
        assert "narrative" in res
        assert res["extracted_data"]["total_transactions_in_db"] >= 0
    finally:
        db.close()
