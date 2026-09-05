import os
import sys
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

# Ensure project root is on sys.path regardless of execution CWD
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.db.database import Base, engine, get_db, SessionLocal
from backend.db import models
from backend.agent.orchestrator import AgentOrchestrator
from backend.batch.runner import run_batch_evaluation
from backend.policy.engine import PolicyEngine
from backend.llm.explainability import LLMExplainer

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Revora — AI Revenue Recovery Engine API",
    description="Backend services for Track 03: Revora AI Revenue Recovery Agent",
    version="1.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = AgentOrchestrator()
policy_engine = PolicyEngine()
llm_explainer = LLMExplainer()

# Pre-populate database from dataset if empty
def seed_database_from_csv(csv_path="ml/data/payments_dataset.csv"):
    if not os.path.exists(csv_path):
        return
    db = SessionLocal()
    try:
        if db.query(models.Payment).count() == 0:
            print("[INFO] Bulk seeding database from payments_dataset.csv...")
            df = pd.read_csv(csv_path).head(1000)  # Seed 1,000 records for fast high-performance queries
            
            existing_cust_ids = set(c[0] for c in db.query(models.Customer.customer_id).all())
            customers_to_add = []
            payments_to_add = []

            for _, row in df.iterrows():
                cid = str(row["customer_id"])
                if cid not in existing_cust_ids:
                    existing_cust_ids.add(cid)
                    customers_to_add.append(models.Customer(
                        customer_id=cid,
                        customer_age_days=int(row["customer_age_days"]),
                        customer_success_rate=float(row["customer_success_rate"]),
                        customer_opted_out=bool(row["customer_opted_out"])
                    ))
                    
                payments_to_add.append(models.Payment(
                    payment_id=str(row["payment_id"]),
                    customer_id=cid,
                    amount=float(row["amount"]),
                    currency=str(row["currency"]),
                    payment_method=str(row["payment_method"]),
                    bank=str(row["bank"]),
                    attempt_number=int(row["attempt_number"]),
                    previous_failures=int(row["previous_failures"]),
                    failure_code=str(row["failure_code"]),
                    failure_class=str(row["failure_class"]),
                    checkout_duration=int(row["checkout_duration"]),
                    cart_value=float(row["cart_value"]),
                    is_subscription=bool(row["is_subscription"]),
                    bank_failure_rate=float(row["bank_failure_rate"]),
                    status="FAILED",
                    recovered=False
                ))

            if customers_to_add:
                db.bulk_save_objects(customers_to_add)
            if payments_to_add:
                db.bulk_save_objects(payments_to_add)
            db.commit()
            print(f"[SUCCESS] Database successfully seeded with {len(payments_to_add)} records.")
    except Exception as e:
        db.rollback()
        print(f"[WARNING] Database seed skipped: {e}")
    finally:
        db.close()

seed_database_from_csv()

# --- Request / Response Models ---
class RecoverActionRequest(BaseModel):
    human_approved: bool = False
    notes: Optional[str] = None

class HumanReviewActionRequest(BaseModel):
    reviewer_notes: Optional[str] = None

class ChatRequest(BaseModel):
    message: str

# --- Endpoints ---

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Revora — AI Revenue Recovery Engine",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/policies")
def get_policies():
    return {
        "MAX_RETRIES": policy_engine.max_retries,
        "MAX_AUTOMATED_AMOUNT": policy_engine.max_automated_amount,
        "MIN_ACTION_CONFIDENCE": policy_engine.min_action_confidence,
        "CUSTOMER_OPTOUT": "HARD_STOP"
    }

@app.get("/payments")
def list_payments(
    status: Optional[str] = None,
    failure_class: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, le=500),
    offset: int = 0,
    db = Depends(get_db)
):
    query = db.query(models.Payment)
    
    if status:
        st = status.upper().strip()
        if st == "RECOVERED":
            query = query.filter((models.Payment.recovered == True) | (models.Payment.status == "RECOVERED"))
        elif st == "PENDING_APPROVAL":
            query = query.filter(models.Payment.status == "PENDING_APPROVAL")
        elif st == "FAILED":
            query = query.filter((models.Payment.recovered == False) & (models.Payment.status != "PENDING_APPROVAL"))
        else:
            query = query.filter(models.Payment.status == st)
            
    if failure_class:
        query = query.filter(models.Payment.failure_class == failure_class.upper().strip())
        
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            models.Payment.payment_id.ilike(s) |
            models.Payment.customer_id.ilike(s) |
            models.Payment.bank.ilike(s) |
            models.Payment.payment_method.ilike(s) |
            models.Payment.failure_code.ilike(s) |
            models.Payment.failure_class.ilike(s)
        )
        
    total = query.count()
    payments = query.order_by(models.Payment.timestamp.desc()).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "payments": payments
    }

@app.get("/payments/{payment_id}")
def get_payment_detail(payment_id: str, db = Depends(get_db)):
    pay = db.query(models.Payment).filter_by(payment_id=payment_id).first()
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    # Analyze payment to get live risk score, root cause, ranked interventions, and policy evaluation
    pay_dict = {
        "payment_id": pay.payment_id,
        "customer_id": pay.customer_id,
        "amount": pay.amount,
        "currency": pay.currency,
        "payment_method": pay.payment_method,
        "bank": pay.bank,
        "attempt_number": pay.attempt_number,
        "previous_failures": pay.previous_failures,
        "failure_code": pay.failure_code,
        "failure_class": pay.failure_class,
        "checkout_duration": pay.checkout_duration,
        "cart_value": pay.cart_value,
        "is_subscription": pay.is_subscription,
        "bank_failure_rate": pay.bank_failure_rate,
        "customer_opted_out": pay.customer.customer_opted_out if pay.customer else False
    }
    
    analysis = orchestrator.analyze_payment(pay_dict)
    
    return {
        "payment": pay,
        "analysis": analysis
    }

@app.post("/payments/{payment_id}/analyze")
def analyze_payment(payment_id: str, db = Depends(get_db)):
    pay = db.query(models.Payment).filter_by(payment_id=payment_id).first()
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    pay_dict = {
        "payment_id": pay.payment_id,
        "customer_id": pay.customer_id,
        "amount": pay.amount,
        "payment_method": pay.payment_method,
        "bank": pay.bank,
        "attempt_number": pay.attempt_number,
        "previous_failures": pay.previous_failures,
        "failure_code": pay.failure_code,
        "failure_class": pay.failure_class,
        "checkout_duration": pay.checkout_duration,
        "is_subscription": pay.is_subscription,
        "bank_failure_rate": pay.bank_failure_rate,
        "customer_opted_out": pay.customer.customer_opted_out if pay.customer else False
    }
    
    analysis = orchestrator.analyze_payment(pay_dict)
    
    # Save decision log
    dec = models.AgentDecision(
        payment_id=payment_id,
        p_recovery=analysis["p_recovery"],
        root_cause=analysis["root_cause"]["cause"],
        root_cause_confidence=analysis["root_cause"]["confidence"],
        evidence_json=analysis["root_cause"]["evidence"],
        selected_intervention=analysis["selected_intervention"]["intervention"],
        expected_recovery_value=analysis["selected_intervention"]["expected_recovery_value"],
        intervention_rankings_json=analysis["ranked_interventions"],
        policy_decision=analysis["policy_result"]["decision"],
        policy_rationale=analysis["policy_result"]["rationale"],
        llm_explanation=analysis["llm_explanation"]
    )
    db.add(dec)
    
    # Log audit event
    for evt in analysis["audit_events"]:
        db.add(models.AuditLog(
            payment_id=payment_id,
            event_type=evt["event_type"],
            actor=evt["actor"],
            decision=evt["decision"],
            reason=evt["reason"]
        ))
        
    db.commit()
    return analysis

@app.post("/payments/{payment_id}/recover")
def execute_recovery(payment_id: str, req: RecoverActionRequest = None, db = Depends(get_db)):
    pay = db.query(models.Payment).filter_by(payment_id=payment_id).first()
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    pay_dict = {
        "payment_id": pay.payment_id,
        "customer_id": pay.customer_id,
        "amount": pay.amount,
        "payment_method": pay.payment_method,
        "bank": pay.bank,
        "attempt_number": pay.attempt_number,
        "previous_failures": pay.previous_failures,
        "failure_code": pay.failure_code,
        "failure_class": pay.failure_class,
        "customer_opted_out": pay.customer.customer_opted_out if pay.customer else False
    }
    
    analysis = orchestrator.analyze_payment(pay_dict)
    human_approved = req.human_approved if req else False
    
    exec_res = orchestrator.execute_recovery_action(pay_dict, analysis, human_approved=human_approved)
    
    # Update payment state in DB
    if exec_res["status"] == "SUCCESS":
        pay.status = "RECOVERED"
        pay.recovered = True
        pay.recovered_amount = exec_res["recovered_amount"]
    elif exec_res["status"] == "PENDING_HUMAN_APPROVAL":
        pay.status = "PENDING_APPROVAL"
        # Add to human approval queue
        appr = models.HumanApproval(
            payment_id=payment_id,
            recommended_action=analysis["selected_intervention"]["intervention"],
            amount=pay.amount,
            reason=analysis["policy_result"]["rationale"],
            model_confidence=analysis["p_recovery"],
            status="PENDING"
        )
        db.add(appr)
    else:
        pay.status = "FAILED_ATTEMPT"
        
    for evt in exec_res["audit_events"]:
        db.add(models.AuditLog(
            payment_id=payment_id,
            event_type=evt["event_type"],
            actor=evt["actor"],
            decision=evt["decision"],
            reason=evt["reason"]
        ))
        
    db.commit()
    return exec_res

@app.post("/payments/{payment_id}/approve")
def approve_recovery(payment_id: str, req: HumanReviewActionRequest = None, db = Depends(get_db)):
    pay = db.query(models.Payment).filter_by(payment_id=payment_id).first()
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    appr = db.query(models.HumanApproval).filter_by(payment_id=payment_id, status="PENDING").first()
    if appr:
        appr.status = "APPROVED"
        appr.reviewer_notes = req.reviewer_notes if req else "Operator approved"
        appr.reviewed_at = datetime.utcnow()
        
    # Execute recovery with human_approved=True
    return execute_recovery(payment_id, RecoverActionRequest(human_approved=True), db)

@app.post("/payments/{payment_id}/reject")
def reject_recovery(payment_id: str, req: HumanReviewActionRequest = None, db = Depends(get_db)):
    pay = db.query(models.Payment).filter_by(payment_id=payment_id).first()
    if not pay:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    appr = db.query(models.HumanApproval).filter_by(payment_id=payment_id, status="PENDING").first()
    if appr:
        appr.status = "REJECTED"
        appr.reviewer_notes = req.reviewer_notes if req else "Operator rejected"
        appr.reviewed_at = datetime.utcnow()
        
    pay.status = "REJECTED_BY_OPERATOR"
    pay.stopping_reason = "HUMAN_REVIEW_REJECTED"
    
    db.add(models.AuditLog(
        payment_id=payment_id,
        event_type="HUMAN_REVIEW_REJECTED",
        actor="HUMAN_OPERATOR",
        decision="REJECTED",
        reason=req.reviewer_notes if req else "Action rejected by human operator."
    ))
    db.commit()
    return {"status": "REJECTED", "message": "Recovery action rejected by operator."}

@app.get("/payments/{payment_id}/audit")
def get_audit_trail(payment_id: str, db = Depends(get_db)):
    logs = db.query(models.AuditLog).filter_by(payment_id=payment_id).order_by(models.AuditLog.timestamp.asc()).all()
    return {"payment_id": payment_id, "logs": logs}

@app.get("/metrics")
def get_metrics():
    # Load model evaluation & batch metrics
    model_metrics = {}
    if os.path.exists("evaluation/model_metrics.json"):
        with open("evaluation/model_metrics.json") as f:
            model_metrics = json.load(f)
            
    batch_results = {}
    if os.path.exists("evaluation/batch_results.json"):
        with open("evaluation/batch_results.json") as f:
            batch_results = json.load(f)
            
    return {
        "model_metrics": model_metrics,
        "batch_metrics": batch_results.get("business_metrics", {})
    }

@app.post("/batch/run")
def trigger_batch_run(limit: int = Query(1000, le=10000)):
    res = run_batch_evaluation(limit=limit)
    return res

@app.post("/chat")
def merchant_chat(req: ChatRequest):
    # Fetch metrics context
    batch_results = {}
    if os.path.exists("evaluation/batch_results.json"):
        with open("evaluation/batch_results.json") as f:
            batch_results = json.load(f).get("business_metrics", {})
            
    reply = llm_explainer.answer_merchant_query(req.message, batch_results)
    return {"reply": reply}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
