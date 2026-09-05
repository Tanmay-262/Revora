import os
import json
from typing import Dict, Any, Optional

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

class BedrockLLMClient:
    """
    AWS Bedrock Runtime SDK Client Wrapper.
    Supports Anthropic Claude 3 models (Haiku / Sonnet) and Amazon Titan models.
    """
    def __init__(
        self,
        region_name: Optional[str] = None,
        model_id: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None
    ):
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        
        self.client = None
        self.is_configured = False
        
        if BOTO3_AVAILABLE:
            try:
                # Initialize boto3 bedrock-runtime client
                kwargs = {"region_name": self.region_name}
                if self.aws_access_key_id and self.aws_secret_access_key and not self.aws_access_key_id.startswith("your_"):
                    kwargs["aws_access_key_id"] = self.aws_access_key_id
                    kwargs["aws_secret_access_key"] = self.aws_secret_access_key
                    self.is_configured = True
                    
                self.client = boto3.client("bedrock-runtime", **kwargs)
            except Exception as e:
                print(f"[WARNING] Bedrock client init warning: {e}")
                self.is_configured = False

    def generate_text(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> Optional[str]:
        """
        Invokes AWS Bedrock model and returns generated response string.
        Returns None if Bedrock is unconfigured or call fails.
        """
        if not self.client or not BOTO3_AVAILABLE:
            return None

        try:
            # Format payload based on model family
            if "anthropic" in self.model_id:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            elif "amazon" in self.model_id:
                body = json.dumps({
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature
                    }
                })
            else: # generic fallback
                body = json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature
                })

            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=body
            )
            
            response_body = json.loads(response.get("body").read().decode("utf-8"))
            
            # Parse output based on model family
            if "anthropic" in self.model_id:
                content = response_body.get("content", [])
                if content and isinstance(content, list):
                    return content[0].get("text", "").strip()
            elif "amazon" in self.model_id:
                results = response_body.get("results", [])
                if results and isinstance(results, list):
                    return results[0].get("outputText", "").strip()
                    
            return str(response_body).strip()
            
        except Exception as e:
            print(f"[WARNING] AWS Bedrock invoke_model failed: {e}")
            return None
