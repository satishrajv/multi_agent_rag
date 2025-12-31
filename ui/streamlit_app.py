"""
Streamlit dashboard for Multi-Agent RAG system
"""
import streamlit as st
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.sales_agent import sales_agent
from src.agents.delivery_agent import delivery_agent
from src.utils.database import db_manager


# Page configuration
st.set_page_config(
    page_title="Multi-Agent RAG Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'feedback_log' not in st.session_state:
    st.session_state.feedback_log = []


def render_sales_agent():
    """Render Sales Agent interface"""
    st.header("Sales / Opportunity Agent")

    # Input
    opp_id = st.text_input(
        "Enter Opportunity ID",
        value="OPP-2024-001",
        key="sales_opp_id"
    )

    if st.button("Analyze Opportunity", key="analyze_sales"):
        with st.spinner("Analyzing opportunity..."):
            result = sales_agent.analyze_opportunity(opp_id, use_cache=False)

            if "error" in result:
                st.error(result["error"])
                return

            # Display results
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader(f"{result['company']}")
                st.write(f"**Stage:** {result['stage']}")

                # Risk status
                if result['status'] == "AT RISK":
                    st.error(f"🚨 Status: {result['status']}")
                    st.metric("Risk Score", f"{result['risk_score']:.3f}")
                else:
                    st.success(f"✅ Status: {result['status']}")
                    st.metric("Risk Score", f"{result['risk_score']:.3f}")

                # Risk factors
                if result['risk_factors']:
                    st.write("**Risk Factors:**")
                    for factor in result['risk_factors']:
                        st.write(f"- {factor}")

            with col2:
                st.write("**Opportunity Details**")
                st.write(f"ID: {result['opportunity_id']}")
                st.write(f"Stage: {result['stage']}")
                st.write(f"Company: {result['company']}")

            # Recommended actions
            if result['recommended_actions']:
                st.subheader("Recommended Actions")

                for action in result['recommended_actions']:
                    with st.expander(
                        f"Priority {action['priority']}: {action['action']}",
                        expanded=(action['priority'] == 1)
                    ):
                        st.write(f"**Action:** {action['action']}")
                        st.write(f"**Reasoning:** {action['reasoning']}")

                        if action.get('playbook_id'):
                            st.write(f"_Based on playbook: {action['playbook_id']}_")

                        # Feedback buttons
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(
                                "✅ Accept",
                                key=f"accept_sales_{action['priority']}"
                            ):
                                # Log feedback
                                sales_agent.log_feedback(
                                    opportunity_id=opp_id,
                                    query=f"Risk analysis for {opp_id}",
                                    risk_score=result['risk_score'],
                                    retrieved_playbooks=result.get('recommended_actions', []),
                                    selected_playbook_id=action.get('playbook_id'),
                                    user_action='accepted'
                                )
                                st.success("Feedback recorded!")

                        with col_b:
                            if st.button(
                                "❌ Dismiss",
                                key=f"dismiss_sales_{action['priority']}"
                            ):
                                sales_agent.log_feedback(
                                    opportunity_id=opp_id,
                                    query=f"Risk analysis for {opp_id}",
                                    risk_score=result['risk_score'],
                                    retrieved_playbooks=result.get('recommended_actions', []),
                                    selected_playbook_id=None,
                                    user_action='rejected'
                                )
                                st.info("Feedback recorded")

            # Email draft
            if result['draft_email']:
                st.subheader("Draft Email")
                draft = result['draft_email']

                st.text_input("Subject", value=draft['subject'], key="email_subject")
                st.text_area("Body", value=draft['body'], height=200, key="email_body")

                if st.button("Copy to Clipboard", key="copy_email"):
                    st.success("Email copied!")


def render_delivery_agent():
    """Render Delivery Agent interface"""
    st.header("Delivery Triage Agent")

    # Input
    proj_id = st.text_input(
        "Enter Project ID",
        value="PROJ-2024-001",
        key="delivery_proj_id"
    )

    if st.button("Analyze Project", key="analyze_delivery"):
        with st.spinner("Analyzing project..."):
            result = delivery_agent.analyze_project(proj_id, use_cache=False)

            if "error" in result:
                st.error(result["error"])
                return

            # Display results
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader(f"{result['project_name']}")
                st.write(f"**Status:** {result['status']}")

                # Classification
                if result['classification'] == "TRUE RISK":
                    st.error(f"🚨 Classification: {result['classification']}")
                else:
                    st.success(f"✅ Classification: {result['classification']}")

                # Risk factors
                if result['risk_factors']:
                    st.write("**Risk Factors:**")
                    for factor in result['risk_factors']:
                        st.write(f"- {factor}")

            with col2:
                st.write("**Project Details**")
                st.write(f"ID: {result['project_id']}")
                st.write(f"Status: {result['status']}")
                st.write(f"Name: {result['project_name']}")

            # Recommended actions
            if result['recommended_actions']:
                st.subheader("Recommended Actions")

                for action in result['recommended_actions']:
                    with st.expander(
                        f"Priority {action['priority']}: {action['action']}",
                        expanded=True
                    ):
                        st.write(f"**Action:** {action['action']}")
                        st.write(f"**Reasoning:** {action['reasoning']}")

                        # Feedback buttons
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(
                                "✅ Accept",
                                key=f"accept_delivery_{action['priority']}"
                            ):
                                delivery_agent.log_feedback(
                                    project_id=proj_id,
                                    query=f"Risk triage for {proj_id}",
                                    classification=result['classification'],
                                    retrieved_playbooks=result.get('recommended_actions', []),
                                    selected_playbook_id=action.get('playbook_id'),
                                    user_action='accepted'
                                )
                                st.success("Feedback recorded!")

                        with col_b:
                            if st.button(
                                "❌ Dismiss",
                                key=f"dismiss_delivery_{action['priority']}"
                            ):
                                delivery_agent.log_feedback(
                                    project_id=proj_id,
                                    query=f"Risk triage for {proj_id}",
                                    classification=result['classification'],
                                    retrieved_playbooks=result.get('recommended_actions', []),
                                    selected_playbook_id=None,
                                    user_action='rejected'
                                )
                                st.info("Feedback recorded")


def main():
    """Main dashboard"""
    st.title("🤖 Multi-Agent RAG Dashboard")
    st.write("Intelligent agents for sales and delivery with continuous learning")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Sales Agent", "Delivery Agent", "Metrics"])

    with tab1:
        render_sales_agent()

    with tab2:
        render_delivery_agent()

    with tab3:
        st.header("System Metrics")
        st.info("Metrics dashboard coming soon...")

        # Show feedback count
        try:
            feedback_data = db_manager.get_feedback_for_training(days=7)
            st.metric("Feedback Records (Last 7 Days)", len(feedback_data))

            # Breakdown by agent
            if len(feedback_data) > 0:
                sales_count = len(feedback_data[feedback_data['agent_name'] == 'sales_agent'])
                delivery_count = len(feedback_data[feedback_data['agent_name'] == 'delivery_agent'])

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Sales Agent Feedback", sales_count)
                with col2:
                    st.metric("Delivery Agent Feedback", delivery_count)

        except Exception as e:
            st.warning(f"Could not fetch metrics: {str(e)}")


if __name__ == "__main__":
    main()
