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
              |
       +------+------+
       |             |
       v             v
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

### 1. ML & Data Services (`ml/`)
- **Synthetic Generator**: Generates 10,000+ realistic transaction records with non-random feature correlations.
- **Data Validation Pipeline**: Checks missing values, class imbalance, schema validity, and data leakage.
- **Recovery ML Model**: RandomForest classifier predicting $P(\text{recovery})$.
- **Root Cause Classifier**: Hybrid rule-based + ML classifier mapping technical failure codes to 5 primary categories (`TEMPORARY_BANK_FAILURE`, `PAYMENT_METHOD_FAILURE`, `CUSTOMER_ABANDONMENT`, `INSUFFICIENT_FUNDS`, `UNKNOWN`).
- **Intervention Expected Value Engine**: Ranks candidate interventions (`RETRY_LATER`, `SEND_PAYMENT_LINK`, `ALTERNATIVE_PAYMENT_METHOD`, `HUMAN_REVIEW`).

### 2. Guardrails & Policy Engine (`backend/policy/`)
- Hard deterministic rules: `MAX_RETRIES=2`, `MAX_AUTOMATED_AMOUNT=₹10,000`, `MIN_ACTION_CONFIDENCE=70%`, `CUSTOMER_OPTOUT=HARD_STOP`.

### 3. Razorpay Integration Adapter (`backend/razorpay/`)
- Unified interface for Razorpay Test Mode API (`create_payment_link`, `fetch_payment`) with fallback mock sandbox.

### 4. Audit Engine & Database (`backend/db/`)
- SQLAlchemy ORM (`customers`, `payments`, `recovery_attempts`, `agent_decisions`, `policy_events`, `audit_logs`, `human_approvals`).

### 5. Frontend Dashboard (`frontend/`)
- Next.js 14, TypeScript, Tailwind CSS merchant console.
