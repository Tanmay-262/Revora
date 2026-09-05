# AI Revenue Recovery Agent

> **Track 03: AI Revenue Recovery — Razorpay AI Builder Buildathon**
> *"Find revenue that's slipping away and win it back."*

---

## 1. Problem Definition
Payment failures cause significant revenue leakage for online merchants. When payments fail due to bank downtime, card errors, or user drop-off, generic retry mechanisms or passive retries either fail to recover the revenue or introduce customer friction. Merchants need an autonomous, intelligent system that evaluates failed payments, diagnoses root causes, estimates expected recovery value, and executes bounded recovery interventions safely.

---

## 2. Solution
The **AI Revenue Recovery Agent** is a production-inspired, autonomous revenue recovery platform built for Razorpay merchants. It combines:
- **Synthetic Data Generation**: 10,000+ non-random, correlated transaction records.
- **Machine Learning Models**: Predicts $P(\text{recovery})$ with Random Forest / XGBoost models.
- **Root-Cause Classification**: Hybrid deterministic rule + evidence engine mapping errors to 5 primary failure classes.
- **Intervention Expected Value Engine**: Ranks recovery actions (`RETRY_LATER`, `SEND_PAYMENT_LINK`, `ALTERNATIVE_PAYMENT_METHOD`, `HUMAN_REVIEW`) by expected net financial value.
- **Deterministic Policy & Guardrail Engine**: Enforces hard monetary thresholds, retry limits, opt-out compliance, and minimum confidence gates (`ALLOW`, `BLOCK`, `HUMAN_APPROVAL_REQUIRED`).
- **AWS Bedrock Enterprise LLM Services**: Integrated via `boto3` for Anthropic Claude 3 Haiku / Claude 3.5 Sonnet / Amazon Titan models with dynamic multi-provider routing and natural-language database extraction.
- **Razorpay Test Mode Integration**: Automated Payment Link generation and payment status verification with offline sandbox fallback.
- **Immutable Audit Trail**: Logs every risk score, policy check, operator approval, and execution event.
- **Merchant Operations Dashboard**: Next.js 14 console featuring Executive KPIs, Recovery Queue, Payment Detail Drawer, Human Approvals Queue, held-out model benchmarks, and an AI Merchant Assistant.

---

## 3. High-Level System Architecture

```text
                    MERCHANT / USER
                          |
                          v
                 NEXT.JS DASHBOARD UI
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
RAZORPAY TEST API / MOCK SANDBOX
      |
      v
ACTION RESULT & AUDIT TRAIL
      |
      v
BATCH EVALUATION & BENCHMARKS
```

---

## 4. AWS Bedrock Enterprise & ML Components

### AWS Bedrock Enterprise LLM Integration (`backend/llm/`)
- **Bedrock SDK Client**: `backend/llm/bedrock_client.py` wrapper using `boto3.client('bedrock-runtime')` supporting Anthropic Claude models (`anthropic.claude-3-haiku-20240307-v1:0`) and Amazon Titan text models.
- **Multi-Provider LLM Router**: `backend/llm/explainability.py` dynamically routes reasoning requests between AWS Bedrock, Google Gemini, and rule-based fallbacks.
- **Bedrock Database Extraction**: `backend/llm/bedrock_extraction.py` parses natural language merchant queries into database extraction summaries across `payments`, `agent_decisions`, and `audit_logs` tables.

### ML Recovery Model ($P(\text{recovery})$)
- **Model**: Trained on 70% train / 15% val / 15% held-out test split.
- **Selected Architecture**: RandomForest Classifier with feature scaling and one-hot categorical encoding.
- **Input Features**: `amount`, `cart_value`, `payment_method`, `bank`, `attempt_number`, `previous_failures`, `customer_age_days`, `customer_success_rate`, `payment_success_rate`, `device_type`, `failure_code`, `failure_class`, `checkout_duration`, `is_subscription`, `customer_opted_out`, `bank_failure_rate`, `hour_of_day`, `day_of_week`.

---

## 5. Safety Policy Engine & Guardrails

The system enforces deterministic financial safety guardrails:
- **`MAX_RETRIES`**: Hard limit of 2 retries per payment.
- **`MAX_AUTOMATED_AMOUNT`**: Transactions > INR 10,000 automatically escalate to `HUMAN_APPROVAL_REQUIRED`.
- **`MIN_ACTION_CONFIDENCE`**: Confidence < 70% escalates to operator review.
- **`CUSTOMER_OPTOUT`**: `HARD_STOP` (0% communication, immediate block).
- **`HUMAN_REVIEW`**: Operator approval queue with explicit audit logging.

---

## 6. Razorpay Test Mode Integration

Integrated via `backend/razorpay/adapter.py`:
- `fetch_payment()`: Fetches payment status.
- `create_payment_link()`: Generates interactive Razorpay Payment Links (`https://rzp.io/i/...`).
- `fetch_payment_link()` / `cancel_payment_link()`: Manages payment link lifecycle.
- **Resilient Fallback**: Toggles seamlessly to `RazorpayMockAdapter` sandbox if live test keys are unavailable or network timeouts occur.

---

## 7. Synthetic Dataset

Generated via `ml/data/generate_dataset.py` (fixed seed 42):
- **Volume**: 10,000 synthetic payment failure records.
- **Correlations**: Realistic ground-truth relationships between bank downtime spikes, customer tenure, attempt counts, subscription status, and recovery success.

---

## 8. Empirical Evaluation Results

### Model Performance on Held-Out Test Set (15% Untouched Split)
| Metric | Value |
|---|---|
| **Precision** | **78.43%** |
| **Recall** | **90.09%** |
| **F1-Score** | **83.86%** |
| **ROC-AUC** | **77.72%** |
| **PR-AUC** | **83.98%** |

### Batch Financial Evaluation (1,000 Transaction Sample)
| Financial Metric | Baseline Strategy | AI Recovery Agent | Uplift |
|---|---|---|---|
| **Total Revenue At Risk** | INR 6,102,116 | INR 6,102,116 | - |
| **Recovered Revenue** | INR 1,463,849.74 | **INR 1,629,347.35** | **+11.31%** |
| **Recovery Rate** | 24.39% | **26.70%** | **+2.31% Net** |
| **Pending Approvals** | 0 | 157 Escalations | - |

---

## 9. Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+

### Step 1: Install Python Backend Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 2: Generate Dataset & Train ML Models
```bash
python ml/data/generate_dataset.py
python ml/data/validate_dataset.py
python ml/baseline.py
python ml/models/train_model.py
python ml/evaluation/evaluate_model.py
python backend/batch/runner.py
```

### Step 3: Start FastAPI Backend Server
```bash
python backend/main.py
```
Backend API will run at `http://localhost:8000`. OpenAPI docs available at `http://localhost:8000/docs`.

### Step 4: Start Next.js Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
Merchant Dashboard UI will open at `http://localhost:3000`.

### Step 5: Run Automated Test Suite
```bash
python -m pytest tests/
```

---

## 10. Environment Variables (`.env.example`)
```env
DATABASE_URL=sqlite:///./sql_app.db
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# LLM Provider Configuration (Options: bedrock | gemini | fallback)
LLM_PROVIDER=bedrock

# AWS Bedrock Enterprise Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Google Gemini API Key
LLM_API_KEY=your_gemini_api_key
GEMINI_API_KEY=your_gemini_api_key

NEXT_PUBLIC_API_URL=http://localhost:8000
MAX_RETRIES=2
MAX_AUTOMATED_AMOUNT=10000
MIN_ACTION_CONFIDENCE=0.70
```
