import streamlit as st
from src.rag_chain import answer_query
from src.monitor import get_recent_logs

st.set_page_config(page_title="Company Chatbot", layout="wide")
st.title("Company Chatbot")

if "role" not in st.session_state:
    st.session_state.role = "employee"
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Login")
    selected_role = st.selectbox(
        "Log in as",
        ["finance_team", "hr_team", "c_level", "employee"],
        index=["finance_team", "hr_team", "c_level", "employee"].index(
            st.session_state.role
        ),
    )
    if selected_role != st.session_state.role:
        st.session_state.role = selected_role
        st.session_state.messages = []
        st.rerun()

    st.caption(f"Logged in as: **{st.session_state.role}**")

    role_files = {
        "finance_team": ["finance/q3_report.txt", "finance/marketing_expenses.txt", "general/company_overview.txt"],
        "hr_team": ["human_resources/employee_handbook.txt", "human_resources/payroll_policy.txt", "general/company_overview.txt"],
        "c_level": ["finance/q3_report.txt", "finance/marketing_expenses.txt", "human_resources/employee_handbook.txt", "human_resources/payroll_policy.txt", "general/company_overview.txt"],
        "employee": ["general/company_overview.txt"],
    }
    with st.expander("Accessible Files"):
        for f in role_files.get(st.session_state.role, []):
            st.markdown(f"- `{f}`")

    with st.expander("Admin: Recent Queries"):
        logs = get_recent_logs(10)
        if logs:
            for log in logs:
                ts, role, query, answer, blocked, reason, lat = log
                icon = ""
                if blocked:
                    icon = reason
                st.markdown(f"**{role}** {icon}: _{query}_")
                st.caption(f"{ts[:19]} | {lat:.0f}ms")
                st.divider()
        else:
            st.info("No queries yet.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption(f"Sources: {', '.join(msg['sources'])}")
        if msg.get("blocked"):
            st.warning(msg["content"])

if prompt := st.chat_input("Ask a question about the company..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = answer_query(prompt, st.session_state.role)
        if result["blocked"]:
            st.warning(result["answer"])
        else:
            st.markdown(result["answer"])
        if result.get("sources"):
            st.caption(f"Sources: {', '.join(result['sources'])}")

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "blocked": result["blocked"],
            "sources": result.get("sources"),
        }
    )
