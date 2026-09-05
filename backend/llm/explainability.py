import os
import json
from typing import Dict, Any, List
import google.generativeai as genai

from backend.llm.bedrock_client import BedrockLLMClient

class LLMExplainer:
    """
    Multi-provider LLM reasoning service supporting AWS Bedrock, Google Gemini, and deterministic fallbacks.
    Dynamically routes queries based on LLM_PROVIDER setting and active credentials.
    """
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
        
        # Initialize AWS Bedrock Client
        self.bedrock_client = BedrockLLMClient()
        
        # Initialize Google Gemini Client
        self.gemini_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.gemini_model = None
        self.has_gemini = bool(self.gemini_key and not self.gemini_key.startswith("your_"))
        
        if self.has_gemini:
            try:
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception:
                self.has_gemini = False

    def get_active_provider_name(self) -> str:
        """Returns the currently active provider name ('AWS Bedrock', 'Google Gemini', or 'Deterministic Fallback')."""
        if self.provider == "bedrock" and self.bedrock_client.is_configured:
            return f"AWS Bedrock ({self.bedrock_client.model_id})"
        elif self.has_gemini:
            return "Google Gemini (gemini-1.5-flash)"
        elif self.bedrock_client.client is not None:
            return f"AWS Bedrock Sandbox ({self.bedrock_client.model_id})"
        return "Deterministic Safety Fallback"

    def _generate_with_active_llm(self, prompt: str) -> str:
        """Attempts generation with Bedrock first if provider==bedrock, then Gemini, then None."""
        if self.provider == "bedrock":
            bedrock_output = self.bedrock_client.generate_text(prompt)
            if bedrock_output:
                return bedrock_output
                
        if self.has_gemini and self.gemini_model:
            try:
                res = self.gemini_model.generate_content(prompt)
                if res and res.text:
                    return res.text.strip()
            except Exception:
                pass
                
        # Try Bedrock as fallback if not primary
        if self.provider != "bedrock":
            bedrock_output = self.bedrock_client.generate_text(prompt)
            if bedrock_output:
                return bedrock_output
                
        return None

    def explain_root_cause_and_risk(
        self,
        payment_data: Dict[str, Any],
        root_cause: Dict[str, Any],
        selected_intervention: Dict[str, Any],
        policy_result: Dict[str, Any]
    ) -> str:
        """Generates natural language summary explaining payment failure and chosen intervention."""
        amount = payment_data.get("amount", 0.0)
        cause_name = root_cause.get("cause", "UNKNOWN")
        evidence = root_cause.get("evidence", [])
        action_name = selected_intervention.get("intervention", "NONE")
        expected_val = selected_intervention.get("expected_recovery_value", 0.0)
        policy_decision = policy_result.get("decision", "ALLOW")
        
        prompt = f"""
        You are an expert AI payment operations analyst at Razorpay.
        Provide a concise, 2-3 sentence executive summary explaining this payment failure and recovery decision to a merchant:
        - Transaction Amount: INR {amount:,.2f}
        - Root Cause: {cause_name} (Evidence: {', '.join(evidence)})
        - Recommended Action: {action_name}
        - Expected Recovery Value: INR {expected_val:,.2f}
        - Policy Decision: {policy_decision} ({policy_result.get('rationale')})
        """
        
        llm_text = self._generate_with_active_llm(prompt)
        if llm_text:
            return llm_text
                
        # Deterministic fallback summary
        return (
            f"Payment of INR {amount:,.2f} failed due to {cause_name.replace('_', ' ').title()} "
            f"(Evidence: {'; '.join(evidence)}). "
            f"The AI Recovery Engine recommends '{action_name.replace('_', ' ').title()}' "
            f"with an estimated net recovery value of INR {expected_val:,.2f}. "
            f"Policy status: {policy_decision}."
        )

    def answer_merchant_query(self, query: str, context_metrics: Dict[str, Any]) -> str:
        """Answers natural language merchant queries based strictly on backend facts."""
        at_risk = context_metrics.get("total_revenue_at_risk", 0.0)
        recovered = context_metrics.get("total_recovered_revenue", 0.0)
        rate = context_metrics.get("recovery_rate", 0.0)
        uplift = context_metrics.get("recovery_uplift", 0.0)
        pending = context_metrics.get("human_escalations", 0)
        
        prompt = f"""
        You are Razorpay's AI Revenue Recovery Assistant. Answer the merchant's query concisely based ONLY on these true system facts:
        - Active LLM Provider: {self.get_active_provider_name()}
        - Revenue at Risk: INR {at_risk:,.2f}
        - Recovered Revenue: INR {recovered:,.2f}
        - Overall Recovery Rate: {rate*100:.2f}%
        - Recovery Uplift over Baseline: {uplift*100:.2f}%
        - Pending Human Reviews: {pending}
        
        Merchant Query: "{query}"
        """
        
        llm_text = self._generate_with_active_llm(prompt)
        if llm_text:
            return llm_text
                
        # Deterministic Q&A Fallback
        q_lower = query.lower()
        if "risk" in q_lower or "how much" in q_lower:
            return f"Currently, there is INR {at_risk:,.2f} at risk across failed payment attempts."
        elif "recovered" in q_lower or "rate" in q_lower:
            return f"The agent has recovered INR {recovered:,.2f}, achieving an overall recovery rate of {rate*100:.2f}% ({uplift*100:.1f}% uplift over baseline)."
        elif "pending" in q_lower or "review" in q_lower or "approve" in q_lower:
            return f"There are currently {pending} transactions awaiting manual merchant review."
        else:
            return f"System Summary ({self.get_active_provider_name()}): Revenue at risk is INR {at_risk:,.2f}, with INR {recovered:,.2f} successfully recovered ({rate*100:.1f}% recovery rate)."
