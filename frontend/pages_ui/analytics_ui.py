import streamlit as st
import pandas as pd
from frontend.api_client import ClinicAPIClient


def render_analytics_page(client: ClinicAPIClient):
    st.markdown("### 📊 Helpdesk Analytics & Content Insights")
    st.caption("Monitor patient search inquiries, helpfulness feedback, top asked questions, and knowledge gaps.")

    try:
        data = client.get_analytics_summary()
    except Exception as e:
        st.error(f"Error fetching analytics data: {e}")
        return

    # Metric Row
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Total Patient Inquiries", data.get("total_queries", 0))
    with col_m2:
        st.metric("Satisfaction Rate", f"{data.get('satisfaction_rate', 100.0)}%", f"👍 {data.get('helpful_ratings', 0)} / 👎 {data.get('unhelpful_ratings', 0)}")
    with col_m3:
        st.metric("Knowledge Gaps / Unanswered", data.get("unanswered_count", 0))
    with col_m4:
        st.metric("Feedback Submissions", data.get("helpful_ratings", 0) + data.get("unhelpful_ratings", 0))

    st.divider()

    # Visualizations Row
    col_ch1, col_ch2 = st.columns(2)

    with col_ch1:
        st.markdown("#### 🔝 Top Asked Patient Questions")
        top_qs = data.get("top_questions", [])
        if top_qs:
            df_top = pd.DataFrame([
                {"Question": q["question"], "Inquiries": q["count"]}
                for q in top_qs
            ]).set_index("Question")
            st.bar_chart(df_top, use_container_width=True)
        else:
            st.info("No query data collected yet. Patient inquiries will appear here.")

    with col_ch2:
        st.markdown("#### 🏥 Inquiries by Category / Department")
        dept_dist = data.get("department_distribution", [])
        if dept_dist:
            df_dept = pd.DataFrame([
                {"Category": d["department"], "Count": d["count"]}
                for d in dept_dist
            ]).set_index("Category")
            st.bar_chart(df_dept, use_container_width=True)
        else:
            st.info("No categorized inquiries available yet.")

    st.divider()

    # Unanswered / Content Gaps Section
    st.markdown("#### ⚠️ Knowledge Gaps & Unanswered Queries")
    st.caption("These queries resulted in low confidence or fallback. Create knowledge base articles to address these recurring patient needs.")

    try:
        unanswered_items = client.get_unanswered_queries(resolved=False)
        if unanswered_items:
            for item in unanswered_items:
                col_u1, col_u2, col_u3, col_u4 = st.columns([5, 2, 2, 2])
                with col_u1:
                    st.write(f"❓ **{item.get('question')}**")
                with col_u2:
                    st.caption(f"Asked **{item.get('frequency')}** time(s)")
                with col_u3:
                    conf = int(item.get("confidence_score", 0.0) * 100)
                    st.caption(f"Score: `{conf}%`")
                with col_u4:
                    if st.button("Mark Resolved", key=f"resolve_btn_{item.get('id')}"):
                        client.resolve_unanswered_query(item.get("id"))
                        st.success("Resolved!")
                        st.rerun()
                st.divider()
        else:
            st.success("🎉 Excellent! No unresolved knowledge gaps currently.")
    except Exception as e:
        st.warning(f"Could not load unanswered queries: {e}")

    # Full Query Audit Log
    st.markdown("#### 📜 Recent Query Audit Log")
    recent = data.get("recent_queries", [])
    if recent:
        df_recent = pd.DataFrame([
            {
                "ID": r.get("id"),
                "Timestamp": r.get("created_at", "")[:19].replace("T", " "),
                "Question": r.get("question"),
                "Answer Preview": r.get("answer", "")[:80] + "...",
                "Confidence": f"{int(r.get('confidence_score', 0.0) * 100)}%",
                "Category": r.get("category"),
                "Fallback": "Yes" if r.get("is_fallback") else "No"
            }
            for r in recent
        ])
        st.dataframe(df_recent, use_container_width=True)

        # CSV Download Button
        csv_data = df_recent.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Audit Log (CSV)",
            data=csv_data,
            file_name="clinic_kb_query_logs.csv",
            mime="text/csv"
        )
    else:
        st.info("No query logs recorded yet.")
