import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Customer(Base):
    __tablename__ = "customers"
    
    customer_id = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, default="merch_razorpay_buildathon", index=True)
    customer_age_days = Column(Integer, default=30)
    customer_success_rate = Column(Float, default=0.85)
    customer_opted_out = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship("Payment", back_populates="customer")

class Payment(Base):
    __tablename__ = "payments"
    
    payment_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), index=True)
    merchant_id = Column(String, default="merch_razorpay_buildathon", index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    payment_method = Column(String, index=True)
    bank = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    attempt_number = Column(Integer, default=1)
    previous_failures = Column(Integer, default=0)
    failure_code = Column(String, index=True)
    failure_class = Column(String, index=True)
    checkout_duration = Column(Integer, default=30)
    cart_value = Column(Float, default=0.0)
    is_subscription = Column(Boolean, default=False)
    bank_failure_rate = Column(Float, default=0.05)
    
    # Recovery status fields
    status = Column(String, default="FAILED", index=True)  # FAILED, ANALYZED, RECOVERY_PENDING, RECOVERED, STOPPED
    recovered = Column(Boolean, default=False, index=True)
    recovered_amount = Column(Float, default=0.0)
    stopping_reason = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="payments")
    decisions = relationship("AgentDecision", back_populates="payment")
    audit_logs = relationship("AuditLog", back_populates="payment")
    approvals = relationship("HumanApproval", back_populates="payment")

class AgentDecision(Base):
    __tablename__ = "agent_decisions"
    
    decision_id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.payment_id"), index=True)
    p_recovery = Column(Float, nullable=False)
    root_cause = Column(String, nullable=False)
    root_cause_confidence = Column(Float, nullable=False)
    evidence_json = Column(JSON, nullable=True)
    selected_intervention = Column(String, nullable=False)
    expected_recovery_value = Column(Float, nullable=False)
    intervention_rankings_json = Column(JSON, nullable=True)
    policy_decision = Column(String, nullable=False)  # ALLOW, BLOCK, HUMAN_APPROVAL_REQUIRED
    policy_rationale = Column(String, nullable=False)
    llm_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="decisions")

class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"
    
    attempt_id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.payment_id"), index=True)
    intervention = Column(String, nullable=False)
    executor = Column(String, default="AGENT_AUTOMATED")  # AGENT_AUTOMATED, HUMAN_OPERATOR
    status = Column(String, nullable=False)  # EXECUTED, FAILED, SUCCESS, REJECTED
    payment_link_id = Column(String, nullable=True)
    payment_link_url = Column(String, nullable=True)
    execution_result_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    event_id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.payment_id"), index=True)
    event_type = Column(String, nullable=False, index=True)
    actor = Column(String, default="SYSTEM_AGENT")
    decision = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    payload_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    payment = relationship("Payment", back_populates="audit_logs")

class HumanApproval(Base):
    __tablename__ = "human_approvals"
    
    approval_id = Column(String, primary_key=True, default=generate_uuid)
    payment_id = Column(String, ForeignKey("payments.payment_id"), index=True)
    recommended_action = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    model_confidence = Column(Float, nullable=False)
    status = Column(String, default="PENDING", index=True)  # PENDING, APPROVED, REJECTED
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="approvals")
