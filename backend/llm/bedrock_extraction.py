import os
import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.db import models
from backend.llm.bedrock_client import BedrockLLMClient

class BedrockDatabaseExtractor:
    """
    AWS Bedrock Natural Language Database Extraction Service.
    Queries SQLAlchemy ORM tables and uses Bedrock to extract structured insights.
    """
    def __init__(self, db: Session):
        self.db = db
        self.bedrock_client = BedrockLLMClient()

    def extract_summary_stats(self) -> Dict[str, Any]:
        pass

    def extract_database_insights(self, query: str) -> Dict[str, Any]:
        """
        Executes database queries across Payments, AgentDecisions, and AuditLogs tables
        and invokes AWS Bedrock to format structured JSON/Markdown extraction insights.
        """
        # Query DB metrics
        total_payments = self.db.query(models.Payment).count()
        total_at_risk = float(self.db.query(models.Payment).with_entities(
            models.Payment.amount
        ).all() and sum(p.amount for p in self.db.query(models.Payment).all()) or 0.0)
        
        recovered_payments = self.db.query(models.Payment).filter_by(recovered=True).all()
        total_recovered = float(sum(p.recovered_amount for p in recovered_payments))
        
        pending_approvals = self.db.query(models.HumanApproval).filter_by(status="PENDING").count()
        
        failure_classes_summary = {}
        all_payments = self.db.query(models.Payment).all()
        for p in all_payments:
            fc = p.failure_class or "UNKNOWN"
            failure_classes_summary[fc] = failure_classes_summary.get(fc, 0) + 1
            
        high_value_at_risk = [
            {
                "payment_id": p.payment_id,
                "customer_id": p.customer_id,
                "amount": p.amount,
                "failure_class": p.failure_class,
                "status": p.status
            }
            for p in self.db.query(models.Payment).filter(models.Payment.amount > 10000).limit(5).all()
        ]
        
        # Prepare context payload
        context_data = {
            "total_transactions_in_db": total_payments,
            "total_revenue_at_risk": total_at_risk,
            "total_recovered_revenue": total_recovered,
            "pending_approvals_count": pending_approvals,
            "failure_class_breakdown": failure_classes_summary,
            "high_value_sample": high_value_at_risk
        }
        
        prompt = f"""
        You are an AWS Bedrock Financial Operations Data Extractor.
        Analyze this structured database context and answer the user query concisely:
        
        Database Context:
        {json.dumps(context_data, indent=2)}
        
        User Query: "{query}"
        
        Provide a clean response with key numerical metrics, breakdown, and actionable recommendations.
        """
        
        extracted_narrative = self.bedrock_client.generate_text(prompt, max_tokens=600)
        if not extracted_narrative:
            extracted_narrative = (
                f"Database Extraction Summary: Total transactions={total_payments}, "
                f"Revenue At Risk=INR {total_at_risk:,.2f}, Recovered=INR {total_recovered:,.2f}, "
                f"Pending Approvals={pending_approvals}."
            )
            
        return {
            "query": query,
            "provider": f"AWS Bedrock ({self.bedrock_client.model_id})",
            "extracted_data": context_data,
            "narrative": extracted_narrative
        }
