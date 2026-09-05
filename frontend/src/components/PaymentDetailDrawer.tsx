'use client';

import React from 'react';
import { X, ShieldCheck, AlertTriangle, Zap, CheckCircle2, Bot, Play } from 'lucide-react';

interface PaymentDetailDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  detailData: any;
  onExecute: (paymentId: string) => void;
  isExecuting: boolean;
}

export const PaymentDetailDrawer: React.FC<PaymentDetailDrawerProps> = ({
  isOpen,
  onClose,
  detailData,
  onExecute,
  isExecuting
}) => {
  if (!isOpen || !detailData) return null;

  const { payment, analysis } = detailData;
  const pRecovery = (analysis?.p_recovery || 0.5) * 100;
  const rootCause = analysis?.root_cause || { cause: 'UNKNOWN', confidence: 0.5, evidence: [] };
  const selectedIntervention = analysis?.selected_intervention || {};
  const policyResult = analysis?.policy_result || { decision: 'ALLOW', rationale: '' };

  const isAllowed = policyResult.decision === 'ALLOW';
  const isHumanReq = policyResult.decision === 'HUMAN_APPROVAL_REQUIRED';

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/75 backdrop-blur-xs flex justify-end transition-opacity">
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 text-slate-100 h-full overflow-y-auto p-6 flex flex-col justify-between shadow-2xl">
        
        <div>
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold font-mono text-slate-100">{payment.payment_id}</h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-300">
                  {payment.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">Customer ID: {payment.customer_id}</p>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Amount & Risk Overview */}
          <div className="grid grid-cols-2 gap-3 my-5">
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Transaction Amount</span>
              <div className="text-xl font-bold text-slate-100 mt-1">
                ₹{payment.amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </div>
              <div className="text-xs text-slate-400 mt-1">
                Instrument: <span className="uppercase text-slate-200 font-medium">{payment.payment_method}</span> ({payment.bank})
              </div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">Recovery Probability</span>
              <div className="text-xl font-bold text-sky-400 mt-1">
                {pRecovery.toFixed(1)}%
              </div>
              <div className="text-xs text-slate-400 mt-1">ML Model Score</div>
            </div>
          </div>

          {/* Diagnosis & Root Cause */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-5">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Root Cause Diagnosis
            </h3>
            
            <div className="flex items-center justify-between bg-slate-900 p-3 rounded-lg border border-slate-800 mb-3">
              <div>
                <span className="text-[11px] text-slate-400">Classified Root Cause</span>
                <div className="text-xs font-bold text-amber-400 mt-0.5">
                  {rootCause.cause.replace(/_/g, ' ')}
                </div>
              </div>
              <div className="text-right">
                <span className="text-[11px] text-slate-400">Confidence</span>
                <div className="text-xs font-semibold text-slate-200">
                  {(rootCause.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            <div>
              <span className="text-[11px] font-medium text-slate-400 block mb-1.5">Evidence Log:</span>
              <ul className="space-y-1">
                {rootCause.evidence?.map((ev: string, idx: number) => (
                  <li key={idx} className="text-xs text-slate-300 flex items-center gap-2 bg-slate-900 px-3 py-1.5 rounded border border-slate-800">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    {ev}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Recommended Intervention */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-5">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-sky-400" />
              Recommended Intervention
            </h3>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3.5 mb-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-bold text-sky-400">
                  {selectedIntervention.intervention?.replace(/_/g, ' ')}
                </span>
                <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  EV: ₹{selectedIntervention.expected_recovery_value?.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </span>
              </div>
              <p className="text-xs text-slate-400">{selectedIntervention.description}</p>
            </div>

            {/* Other Ranked Options */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 block">Ranked Alternatives:</span>
              {analysis?.ranked_interventions?.slice(1).map((opt: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between text-xs bg-slate-900/60 p-2 rounded border border-slate-800">
                  <span className="font-medium text-slate-300">{opt.intervention?.replace(/_/g, ' ')}</span>
                  <div className="flex items-center gap-3 text-slate-400">
                    <span>P: {(opt.probability_success * 100).toFixed(0)}%</span>
                    <span className="font-semibold text-slate-200">EV: ₹{opt.expected_recovery_value}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Policy Check Results */}
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-5">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Safety & Policy Guardrails
            </h3>

            <div className={`p-3 rounded-lg border text-xs ${
              isAllowed
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                : isHumanReq
                ? 'bg-amber-500/10 border-amber-500/20 text-amber-300'
                : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
            }`}>
              <div className="font-bold uppercase tracking-wider mb-0.5">Decision: {policyResult.decision}</div>
              <div>{policyResult.rationale}</div>
            </div>
          </div>

          {/* AI Explanation Summary */}
          {analysis?.llm_explanation && (
            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 mb-5">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Bot className="w-3.5 h-3.5 text-indigo-400" />
                AI Analyst Narrative
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed italic bg-slate-900 p-3 rounded-lg border border-slate-800">
                "{analysis.llm_explanation}"
              </p>
            </div>
          )}

        </div>

        {/* Footer Action Button */}
        <div className="pt-4 border-t border-slate-800 mt-4">
          <button
            onClick={() => onExecute(payment.payment_id)}
            disabled={isExecuting || policyResult.decision === 'BLOCK' || payment.recovered}
            className={`w-full py-3 rounded-lg font-bold text-xs transition-colors flex items-center justify-center gap-2 shadow-sm ${
              payment.recovered
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : isAllowed
                ? 'bg-sky-600 hover:bg-sky-500 text-white'
                : 'bg-amber-600 hover:bg-amber-500 text-white'
            }`}
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {isExecuting
              ? 'Dispatching Recovery Action...'
              : payment.recovered
              ? 'Payment Already Recovered'
              : isAllowed
              ? 'Execute Bounded Recovery Action'
              : 'Escalate to Operator Approval'}
          </button>
        </div>

      </div>
    </div>
  );
};
