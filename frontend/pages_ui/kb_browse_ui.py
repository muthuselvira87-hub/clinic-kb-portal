import streamlit as st
from frontend.api_client import ClinicAPIClient


def render_kb_browse_page(client: ClinicAPIClient):
    st.markdown("### 📚 Clinic Knowledge Base & Directory")
    st.caption("Browse published patient care articles, specialist departments, and medical guides.")

    # Search & Filter Controls
    col_search, col_cat, col_tag = st.columns([3, 2, 2])

    with col_search:
        search_query = st.text_input("🔍 Search articles by keyword...", placeholder="e.g. cardiology, billing, ecg")

    with col_cat:
        try:
            categories_data = client.get_categories()
            category_options = ["All"] + [c["category"] for c in categories_data]
        except Exception:
            category_options = ["All"]
        selected_category = st.selectbox("Category", category_options)

    with col_tag:
        try:
            tags_data = client.get_tags()
            tag_options = ["All"] + [t["tag"] for t in tags_data]
        except Exception:
            tag_options = ["All"]
        selected_tag = st.selectbox("Filter by Tag", tag_options)

    # Fetch articles from backend
    try:
        articles = client.get_articles(
            category=None if selected_category == "All" else selected_category,
            tag=None if selected_tag == "All" else selected_tag,
            search=search_query if search_query.strip() else None,
            status="published"
        )
    except Exception as e:
        st.error(f"Error fetching articles: {e}")
        articles = []

    st.markdown(f"**Found {len(articles)} article(s)**")
    st.divider()

    if not articles:
        st.info("No articles match your search or filter criteria. Try adjusting your search query.")
        return

    # Render Articles
    for art in articles:
        with st.container():
            col_t1, col_t2 = st.columns([4, 2])
            with col_t1:
                st.markdown(f"#### 📄 {art.get('title')}")
            with col_t2:
                st.markdown(
                    f"<div style='text-align: right;'>"
                    f"<span style='background-color:#e0f2fe;color:#0369a1;padding:4px 8px;border-radius:12px;font-size:12px;margin-right:6px;'>🏷️ {art.get('category')}</span>"
                    f"<span style='background-color:#fef3c7;color:#b45309;padding:4px 8px;border-radius:12px;font-size:12px;'>🏥 {art.get('department')}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

            # Content preview & expander
            content = art.get("content", "")
            with st.expander("📖 View Full Article", expanded=False):
                st.markdown(content)
                st.caption(f"✍️ **Author**: {art.get('author', 'Staff')} | 📅 **Updated**: {art.get('updated_at', 'Recently')[:10] if art.get('updated_at') else 'N/A'}")

            # Tags chips
            tags = art.get("tags", [])
            if tags:
                tag_badges = " ".join([f"`#{t}`" for t in tags])
                st.markdown(f"<small>{tag_badges}</small>", unsafe_allow_html=True)

            st.divider()
