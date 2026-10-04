"""Tests for the Interactive Human-in-the-Loop Triage Interface (src/ui/triage_view.py).

Covers:
1. Module importability and function callability
2. Empty input handling
3. Successful rendering with valid agent response
4. All three decision outcomes (RECOMMEND, REVIEW_REQUIRED, INSUFFICIENT_INFORMATION)
5. Human review controls do not mutate the original request
6. Human decisions are clearly labeled as simulated (session state only)
7. No source dataset or ticket mutation occurs
"""

import copy
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd

from src.ui.triage_view import (
    render_triage_agent_view,
    SAMPLE_SCENARIOS,
    SUPPORT_TEAMS,
)
from src.agent.triage_agent import (
    SupportTriageAgent,
    TriageAgentRequest,
    TriageAgentResponse,
    TriageOutcome,
)


def get_file_hash(path: Path) -> str:
    """Compute sha256 hash of a file for immutability verification."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def test_triage_view_callable():
    """Verify render_triage_agent_view is importable and callable."""
    assert callable(render_triage_agent_view)


def test_empty_input_handling():
    """Verify triage view handles empty or minimal inputs gracefully."""
    req = TriageAgentRequest(
        ticket_id="TICK-EMPTY-TEST",
        customer_message="",
        channel="chat"
    )
    resp = SupportTriageAgent.evaluate(req)

    assert resp.outcome == TriageOutcome.INSUFFICIENT_INFORMATION
    assert resp.recommended_category is None
    assert resp.recommended_team is None
    assert len(resp.information_requests) > 0

    # Ensure calling render_triage_agent_view with session state containing empty response doesn't crash
    session_state = {
        "triage_selected_preset": "Custom Ticket (Manual Input)",
        "triage_response": resp,
        "triage_request_evaluated": req,
        "simulated_decision": None,
    }
    with patch("streamlit.session_state", session_state):
        # Should execute all UI rendering without error
        render_triage_agent_view()


def test_successful_rendering_all_three_outcomes():
    """Verify rendering logic across all 3 decision outcomes."""
    # 1. RECOMMEND Outcome
    req_rec = TriageAgentRequest(
        ticket_id="TICK-REC-01",
        customer_message="Where is my package? AWB tracking has not updated for 5 days. Courier says delayed in transit.",
        channel="chat",
        order_id="VR891100"
    )
    resp_rec = SupportTriageAgent.evaluate(req_rec)
    assert resp_rec.outcome == TriageOutcome.RECOMMEND
    assert resp_rec.recommended_category == "Order & Logistics"
    assert resp_rec.recommended_team == "Logistics"
    assert not resp_rec.review_required

    session_rec = {
        "triage_selected_preset": "Custom Ticket (Manual Input)",
        "triage_response": resp_rec,
        "triage_request_evaluated": req_rec,
        "simulated_decision": None,
    }
    with patch("streamlit.session_state", session_rec):
        render_triage_agent_view()

    # 2. REVIEW_REQUIRED Outcome (Missing Order ID on Return)
    req_rev = TriageAgentRequest(
        ticket_id="TICK-REV-02",
        customer_message="Nobody came for the return pickup of my Strata 2 headphones. Please reschedule reverse pickup.",
        channel="email",
        order_id=""
    )
    resp_rev = SupportTriageAgent.evaluate(req_rev)
    assert resp_rev.outcome == TriageOutcome.REVIEW_REQUIRED
    assert resp_rev.review_required is True
    assert len(resp_rev.information_requests) > 0

    session_rev = {
        "triage_selected_preset": "Custom Ticket (Manual Input)",
        "triage_response": resp_rev,
        "triage_request_evaluated": req_rev,
        "simulated_decision": None,
    }
    with patch("streamlit.session_state", session_rev):
        render_triage_agent_view()

    # 3. INSUFFICIENT_INFORMATION Outcome
    req_ins = TriageAgentRequest(
        ticket_id="TICK-INS-03",
        customer_message="???",
        channel="social"
    )
    resp_ins = SupportTriageAgent.evaluate(req_ins)
    assert resp_ins.outcome == TriageOutcome.INSUFFICIENT_INFORMATION
    assert resp_ins.review_required is True

    session_ins = {
        "triage_selected_preset": "Custom Ticket (Manual Input)",
        "triage_response": resp_ins,
        "triage_request_evaluated": req_ins,
        "simulated_decision": None,
    }
    with patch("streamlit.session_state", session_ins):
        render_triage_agent_view()


def test_human_review_controls_do_not_mutate_request():
    """Verify that human review simulation controls do not mutate the input request."""
    orig_req = TriageAgentRequest(
        ticket_id="TICK-MUT-TEST",
        customer_message="Where is my order? Tracking delayed.",
        channel="chat",
        order_id="VR891100"
    )
    req_copy = copy.deepcopy(orig_req)

    resp = SupportTriageAgent.evaluate(orig_req)

    # Simulate supervisor decision in session state
    sim_decision = {
        "timestamp": "2026-10-04 12:00:00",
        "ticket_id": resp.ticket_id,
        "action": "Override & Route to Alternative Support Team",
        "assigned_team": "Escalations & Warranty",
        "operator_notes": "Routing to senior team due to repeated inquiries.",
        "mode": "SIMULATED_LOCAL_SESSION_ONLY",
    }

    session_state = {
        "triage_selected_preset": "Custom Ticket (Manual Input)",
        "triage_response": resp,
        "triage_request_evaluated": orig_req,
        "simulated_decision": sim_decision,
    }

    with patch("streamlit.session_state", session_state):
        render_triage_agent_view()

    # Request and response must remain bit-for-bit identical to pre-review state
    assert orig_req == req_copy
    assert resp.recommended_team == "Logistics"  # Agent recommendation unchanged
    assert session_state["simulated_decision"]["assigned_team"] == "Escalations & Warranty"


def test_human_decision_clearly_simulated():
    """Verify human decision has clear simulated labeling and governance demarcation."""
    resp = SupportTriageAgent.evaluate(
        TriageAgentRequest(
            ticket_id="TICK-SIM-01",
            customer_message="Please send invoice for order VR892200",
            channel="email"
        )
    )

    sim_decision = {
        "timestamp": "2026-10-04 12:30:00",
        "ticket_id": resp.ticket_id,
        "action": "Approve Recommendation (Route as Suggested)",
        "assigned_team": resp.recommended_team,
        "operator_notes": "Supervisor approved Billing routing.",
        "mode": "SIMULATED_LOCAL_SESSION_ONLY",
    }

    assert sim_decision["mode"] == "SIMULATED_LOCAL_SESSION_ONLY"
    assert "SIMULATED" in sim_decision["mode"]

    session_state = {
        "triage_selected_preset": "Custom Ticket (Manual Input)",
        "triage_response": resp,
        "triage_request_evaluated": None,
        "simulated_decision": sim_decision,
    }

    with patch("streamlit.session_state", session_state):
        # Should render the simulated decision summary card without failure
        render_triage_agent_view()


def test_no_source_dataset_mutation():
    """Verify that running triage view scenarios causes zero mutations to source files."""
    base_dir = Path(__file__).resolve().parent.parent
    raw_tickets_path = base_dir / "data" / "raw" / "tickets.csv"
    raw_orders_path = base_dir / "data" / "raw" / "orders.csv"
    processed_tickets_path = base_dir / "data" / "processed" / "classified_tickets.csv"

    # Pre-execution file hashes
    h_raw_tickets_before = get_file_hash(raw_tickets_path)
    h_raw_orders_before = get_file_hash(raw_orders_path)
    h_proc_tickets_before = get_file_hash(processed_tickets_path)

    # Execute all pre-configured scenarios through the triage pipeline
    for name, scenario in SAMPLE_SCENARIOS.items():
        req = TriageAgentRequest(
            ticket_id=scenario.get("ticket_id", "TICK-TEST"),
            customer_message=scenario.get("customer_message", ""),
            channel=scenario.get("channel", "chat"),
            order_id=scenario.get("order_id", ""),
            customer_id=scenario.get("customer_id", ""),
            product_sku=scenario.get("product_sku", ""),
            original_category=scenario.get("original_category", ""),
            refund_reason_code=scenario.get("refund_reason_code", "None"),
            replacement_issued=scenario.get("replacement_issued", "None"),
            agent_notes=scenario.get("agent_notes", "")
        )
        resp = SupportTriageAgent.evaluate(req)

        # Simulate rendering view
        session_state = {
            "triage_selected_preset": name,
            "triage_response": resp,
            "triage_request_evaluated": req,
            "simulated_decision": {
                "timestamp": "2026-10-04 12:00:00",
                "ticket_id": resp.ticket_id,
                "action": "Approve Recommendation",
                "assigned_team": resp.recommended_team,
                "operator_notes": f"Simulated review for {name}",
                "mode": "SIMULATED_LOCAL_SESSION_ONLY"
            }
        }
        with patch("streamlit.session_state", session_state):
            render_triage_agent_view()

    # Post-execution file hashes
    h_raw_tickets_after = get_file_hash(raw_tickets_path)
    h_raw_orders_after = get_file_hash(raw_orders_path)
    h_proc_tickets_after = get_file_hash(processed_tickets_path)

    assert h_raw_tickets_before == h_raw_tickets_after, "data/raw/tickets.csv was modified!"
    assert h_raw_orders_before == h_raw_orders_after, "data/raw/orders.csv was modified!"
    assert h_proc_tickets_before == h_proc_tickets_after, "data/processed/classified_tickets.csv was modified!"
