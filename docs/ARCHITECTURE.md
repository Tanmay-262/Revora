# System Architecture - Revora (AI Revenue Recovery Agent)

## Track 03: AI Revenue Recovery (Razorpay AI Builder Buildathon)

### Overview
Revora is a production-inspired, autonomous AI revenue recovery platform designed to detect at-risk payments, diagnose failure root causes, rank recovery interventions by expected value, enforce deterministic guardrails, and safely execute recovery workflows.

```text
                    MERCHANT / USER
                          |
                          v
                 NEXT.JS UI DASHBOARD
                          |
                          v
                    FASTAPI REST API
                          |
              +-----------+-----------+
              |                       |
              v                       v
        AGENT ORCHESTRATOR       REST ENDPOINTS
              |                       |
       +------+------+                v
       |             |         AWS BEDROCK / GEMINI
       v             v        DATABASE EXTRACTION
  ML SERVICES     BUSINESS DATA
       |             |
       +------+------+
              |
              v
       DECISION ENGINE
              |
              v
       POLICY / GUARDRAIL
              |
      +-------+-------+
      |               |
      v               v
   ALLOWED         HUMAN REVIEW
      |
      v
RAZORPAY TEST API / MOCK
      |
      v
ACTION RESULT & AUDIT TRAIL
      |
      v
EVALUATION / BATCH METRICS
```

---

## Key Modules

### 1. AWS Bedrock Enterprise LLM Services (`backend/llm/`)
- **AWS Bedrock Runtime SDK**: `backend/llm/bedrock_client.py` wrapper connecting to Anthropic Claude 3 Haiku / Claude 3.5 Sonnet / Amazon Titan models via `boto3`.
- **Multi-Provider LLM Router**: `backend/llm/explainability.py` dynamic routing supporting AWS Bedrock, Google Gemini, and rule-based fallbacks.
- **Natural Language Database Extraction**: `backend/llm/bedrock_extraction.py` parses merchant questions and executes relational queries across SQLAlchemy database tables (`payments`, `agent_decisions`, `audit_logs`).

### 2. ML & Data Services (`ml/`)
- **Synthetic Generator**: Generates 10,000+ realistic transaction records with non-random feature correlations.
- **Data Validation Pipeline**: Checks missing values, class imbalance, schema validity, and data leakage.
- **Recovery ML Model**: RandomForest classifier predicting $P(\text{recovery})$.
- **Root Cause Classifier**: Hybrid rule-based + ML classifier mapping technical failure codes to 5 primary categories (`TEMPORARY_BANK_FAILURE`, `PAYMENT_METHOD_FAILURE`, `CUSTOMER_ABANDONMENT`, `INSUFFICIENT_FUNDS`, `UNKNOWN`).
- **Intervention Expected Value Engine**: Ranks candidate interventions (`RETRY_LATER`, `SEND_PAYMENT_LINK`, `ALTERNATIVE_PAYMENT_METHOD`, `HUMAN_REVIEW`).

### 3. Guardrails & Policy Engine (`backend/policy/`)
- Hard deterministic rules: `MAX_RETRIES=2`, `MAX_AUTOMATED_AMOUNT=₹10,000`, `MIN_ACTION_CONFIDENCE=70%`, `CUSTOMER_OPTOUT=HARD_STOP`.

### 4. Razorpay Integration Adapter (`backend/razorpay/`)
- Unified interface for Razorpay Test Mode API (`create_payment_link`, `fetch_payment`) with fallback mock sandbox.

### 5. Audit Engine & Database (`backend/db/`)
- SQLAlchemy ORM (`customers`, `payments`, `recovery_attempts`, `agent_decisions`, `policy_events`, `audit_logs`, `human_approvals`).

### 6. Frontend Dashboard (`frontend/`)
- Next.js 14, TypeScript, Tailwind CSS merchant console.
