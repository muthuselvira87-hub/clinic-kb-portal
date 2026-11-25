import uuid
import streamlit as st
from frontend.api_client import ClinicAPIClient

QUICK_PROMPTS = [
    "What are the clinic timings?",
    "What are doctor consultation charges?",
    "Do you accept health insurance?",
    "Is pediatric care available?",
    "How can I book an appointment?",
    "What is the emergency contact number?"
]


def render_chat_page(client: ClinicAPIClient):
    st.markdown("### 🩺 Patient Helpdesk & AI Assistant")
    st.caption("Ask questions about clinic hours, specialist doctors, diagnostic tests, insurance, and medical services.")

    # Emergency Warning Banner
    st.warning(
        "🚨 **For Medical Emergencies**: If you or a loved one is experiencing severe chest pain, "
        "difficulty breathing, or acute trauma, please dial **108** immediately or visit our 24/7 Casualty Unit.",
        icon="⚠️"
    )

    # Initialize session state for chat
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = str(uuid.uuid4())[:8]

    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Hello! Welcome to MetroLife Health Clinic. I am your automated clinic helpdesk assistant. "
                    "How may I assist you today? You can ask about our OPD hours, specialist doctors, "
                    "lab investigations, or billing policies."
                ),
                "sources": [],
                "confidence": 1.0,
                "is_fallback": False,
                "query_id": None
            }
        ]

    # Quick Prompts Row
    st.markdown("**Frequently Asked Questions:**")
    cols = st.columns(3)
    prompt_clicked = None
    for idx, prompt in enumerate(QUICK_PROMPTS):
        col = cols[idx % 3]
        if col.button(f"💬 {prompt}", key=f"quick_btn_{idx}", use_container_width=True):
            prompt_clicked = prompt

    # Clear chat button in sidebar or header
    col_hdr1, col_hdr2 = st.columns([6, 1])
    with col_hdr2:
        if st.button("🧹 Clear Chat", help="Reset conversation"):
            st.session_state["messages"] = [
                {
                    "role": "assistant",
                    "content": "Hello! How can I help you today with your clinic inquiry?",
                    "sources": [],
                    "confidence": 1.0,
                    "is_fallback": False,
                    "query_id": None
                }
            ]
            st.rerun()

    # Display Chat History
    for msg_idx, message in enumerate(st.session_state["messages"]):
        role = message["role"]
        with st.chat_message(role, avatar="🧑‍⚕️" if role == "assistant" else "👤"):
            st.markdown(message["content"])

            # Render citations expander if available
            sources = message.get("sources", [])
            if sources:
                with st.expander(f"📚 Verified Sources & Citations ({len(sources)})", expanded=False):
                    for s_idx, src in enumerate(sources):
                        rel = int(src.get("relevance_score", 0.0) * 100)
                        st.markdown(
                            f"**{s_idx + 1}. {src.get('title', 'Knowledge Article')}** "
                            f"`Relevance: {rel}%` | *Dept: {src.get('department', 'General')}*"
                        )
                        st.caption(f"\"{src.get('content_snippet', '')}\"")
                        st.markdown(f"<small>Source: `{src.get('source', 'clinic_kb')}`</small>", unsafe_allow_html=True)
                        if s_idx < len(sources) - 1:
                            st.divider()

            # Feedback buttons for assistant answers
            if role == "assistant" and message.get("query_id") is not None:
                q_id = message["query_id"]
                feedback_key = f"feedback_given_{q_id}"

                if feedback_key not in st.session_state:
                    col_fb1, col_fb2, col_fb3 = st.columns([1, 1, 8])
                    if col_fb1.button("👍 Helpful", key=f"thumb_up_{msg_idx}_{q_id}"):
                        client.submit_feedback(q_id, rating=1)
                        st.session_state[feedback_key] = "up"
                        st.rerun()
                    if col_fb2.button("👎 Unhelpful", key=f"thumb_down_{msg_idx}_{q_id}"):
                        client.submit_feedback(q_id, rating=-1)
                        st.session_state[feedback_key] = "down"
                        st.rerun()
                else:
                    status = st.session_state[feedback_key]
                    st.caption("✅ *Thank you for your feedback!*" if status == "up" else "⚠️ *Feedback noted. We will improve this answer.*")

    # Handle user input via chat box or quick prompt click
    user_query = st.chat_input("Type your question here (e.g. 'Can I get a blood test on Sunday?')...")
    query_to_send = prompt_clicked or user_query

    if query_to_send:
        # Append user message
        st.session_state["messages"].append({"role": "user", "content": query_to_send})

        with st.chat_message("user", avatar="👤"):
            st.markdown(query_to_send)

        # Assistant thinking
        with st.chat_message("assistant", avatar="🧑‍⚕️"):
            with st.spinner("Searching clinic knowledge base..."):
                try:
                    res = client.ask_chat(
                        question=query_to_send,
                        session_id=st.session_state["session_id"]
                    )
                    answer = res["answer"]
                    sources = res.get("sources", [])
                    confidence = res.get("confidence_score", 0.0)
                    is_fallback = res.get("is_fallback", False)
                    query_id = res.get("query_id")

                    st.markdown(answer)

                    if sources:
                        with st.expander(f"📚 Verified Sources & Citations ({len(sources)})", expanded=False):
                            for s_idx, src in enumerate(sources):
                                rel = int(src.get("relevance_score", 0.0) * 100)
                                st.markdown(
                                    f"**{s_idx + 1}. {src.get('title', 'Knowledge Article')}** "
                                    f"`Relevance: {rel}%` | *Dept: {src.get('department', 'General')}*"
                                )
                                st.caption(f"\"{src.get('content_snippet', '')}\"")
                                st.markdown(f"<small>Source: `{src.get('source', 'clinic_kb')}`</small>", unsafe_allow_html=True)
                                if s_idx < len(sources) - 1:
                                    st.divider()

                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "confidence": confidence,
                        "is_fallback": is_fallback,
                        "query_id": query_id
                    })

                except Exception as e:
                    err_msg = f"Sorry, I encountered an error communicating with the helpdesk service: {e}"
                    st.error(err_msg)
                    st.session_state["messages"].append({
                        "role": "assistant",
                        "content": err_msg,
                        "sources": [],
                        "confidence": 0.0,
                        "is_fallback": True,
                        "query_id": None
                    })

        st.rerun()
