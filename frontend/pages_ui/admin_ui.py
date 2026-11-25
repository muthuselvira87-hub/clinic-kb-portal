import streamlit as st
import pandas as pd
from backend.config import ADMIN_PIN
from frontend.api_client import ClinicAPIClient

CATEGORIES_DEFAULT = [
    "General Information",
    "Specialist Care",
    "Emergency Care",
    "Diagnostics",
    "Billing",
    "Appointments & Timings",
    "Pharmacy Services",
    "Preventive Medicine"
]

DEPARTMENTS_DEFAULT = [
    "General Helpdesk",
    "Emergency & Trauma Care",
    "Cardiology",
    "Pediatrics",
    "Dermatology",
    "Dental Clinic",
    "Laboratory & Radiology",
    "Billing & Accounts",
    "Pharmacy",
    "Physiotherapy"
]


def render_admin_page(client: ClinicAPIClient):
    st.markdown("### 🛠️ Clinic Knowledge Base Administration")
    st.caption("Manage clinic articles, ingest medical documents, and control vector search indexing.")

    # Access Control Check
    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    if not st.session_state["admin_authenticated"]:
        with st.form("admin_login_form"):
            st.markdown("#### 🔒 Staff Authentication")
            st.info("Enter the clinic administrator PIN to access management tools (Default: `admin123`).")
            pin_input = st.text_input("Administrator PIN", type="password")
            submit_login = st.form_submit_button("Authenticate")

            if submit_login:
                if pin_input == ADMIN_PIN:
                    st.session_state["admin_authenticated"] = True
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Invalid administrator PIN.")
        return

    # Authenticated Admin Bar
    col_auth1, col_auth2 = st.columns([5, 1])
    with col_auth1:
        st.success("🔓 Authenticated as Clinic Administrator")
    with col_auth2:
        if st.button("🚪 Logout"):
            st.session_state["admin_authenticated"] = False
            st.rerun()

    admin_tab1, admin_tab2, admin_tab3 = st.tabs([
        "📝 Article Editor",
        "📂 Document Ingestion",
        "⚙️ Vector Index Control"
    ])

    # ------------------ TAB 1: ARTICLE EDITOR ------------------
    with admin_tab1:
        editor_mode = st.radio("Select Action:", ["Create New Article", "Edit Existing Article", "View All Articles"], horizontal=True)

        if editor_mode == "Create New Article":
            st.markdown("##### ➕ Create New Clinic Knowledge Article")
            with st.form("create_article_form", clear_on_submit=True):
                title = st.text_input("Article Title *", placeholder="e.g. Orthopedics OPD Hours and Joint Care Services")
                col_cat, col_dept = st.columns(2)
                with col_cat:
                    category = st.selectbox("Category", CATEGORIES_DEFAULT)
                with col_dept:
                    department = st.selectbox("Department", DEPARTMENTS_DEFAULT)

                content = st.text_area("Content (Markdown supported) *", height=200, placeholder="Detailed article text...")
                tags_str = st.text_input("Tags (comma-separated)", placeholder="orthopedics, joints, bone fracture, arthritis")
                author = st.text_input("Author / Designation", value="Clinic Administration")
                status = st.selectbox("Publication Status", ["published", "draft"])

                submit_create = st.form_submit_button("Publish Article & Update Vector Index")

                if submit_create:
                    if not title.strip() or not content.strip():
                        st.error("Title and Content are required fields.")
                    else:
                        tags_list = [t.strip().lower() for t in tags_str.split(",") if t.strip()]
                        payload = {
                            "title": title.strip(),
                            "content": content.strip(),
                            "category": category,
                            "department": department,
                            "tags": tags_list,
                            "author": author.strip(),
                            "status": status
                        }
                        try:
                            res = client.create_article(payload)
                            st.success(f"✅ Article '{res.get('title')}' created and indexed successfully (ID: {res.get('id')})!")
                        except Exception as e:
                            st.error(f"Failed to create article: {e}")

        elif editor_mode == "Edit Existing Article":
            st.markdown("##### ✏️ Edit or Remove Knowledge Article")
            try:
                articles = client.get_articles(status="all")
            except Exception as e:
                st.error(f"Error loading articles: {e}")
                articles = []

            if not articles:
                st.info("No articles found to edit.")
            else:
                article_options = {f"#{a['id']} - {a['title']}": a for a in articles}
                selected_label = st.selectbox("Select Article to Edit:", list(article_options.keys()))
                selected_art = article_options[selected_label]

                with st.form("edit_article_form"):
                    edit_title = st.text_input("Article Title", value=selected_art.get("title", ""))
                    col_ecat, col_edept = st.columns(2)
                    with col_ecat:
                        cur_cat = selected_art.get("category", CATEGORIES_DEFAULT[0])
                        cat_idx = CATEGORIES_DEFAULT.index(cur_cat) if cur_cat in CATEGORIES_DEFAULT else 0
                        edit_cat = st.selectbox("Category", CATEGORIES_DEFAULT, index=cat_idx)
                    with col_edept:
                        cur_dept = selected_art.get("department", DEPARTMENTS_DEFAULT[0])
                        dept_idx = DEPARTMENTS_DEFAULT.index(cur_dept) if cur_dept in DEPARTMENTS_DEFAULT else 0
                        edit_dept = st.selectbox("Department", DEPARTMENTS_DEFAULT, index=dept_idx)

                    edit_content = st.text_area("Content", value=selected_art.get("content", ""), height=200)
                    existing_tags = ", ".join(selected_art.get("tags", []))
                    edit_tags_str = st.text_input("Tags", value=existing_tags)
                    edit_status = st.selectbox("Status", ["published", "draft"], index=0 if selected_art.get("status") == "published" else 1)

                    col_save, col_del = st.columns([4, 1])
                    with col_save:
                        submit_update = st.form_submit_button("💾 Save Changes")
                    with col_del:
                        delete_requested = st.form_submit_button("🗑️ Delete")

                    if submit_update:
                        update_payload = {
                            "title": edit_title.strip(),
                            "content": edit_content.strip(),
                            "category": edit_cat,
                            "department": edit_dept,
                            "tags": [t.strip().lower() for t in edit_tags_str.split(",") if t.strip()],
                            "status": edit_status
                        }
                        try:
                            client.update_article(selected_art["id"], update_payload)
                            st.success(f"✅ Article #{selected_art['id']} updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to update: {e}")

                    if delete_requested:
                        try:
                            client.delete_article(selected_art["id"])
                            st.warning(f"Article #{selected_art['id']} deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")

        elif editor_mode == "View All Articles":
            st.markdown("##### 📋 All Knowledge Base Articles")
            try:
                articles = client.get_articles(status="all")
                if articles:
                    df = pd.DataFrame([
                        {
                            "ID": a["id"],
                            "Title": a["title"],
                            "Category": a["category"],
                            "Department": a["department"],
                            "Status": a["status"],
                            "Tags": ", ".join(a.get("tags", [])),
                            "Updated": a.get("updated_at", "")[:10]
                        }
                        for a in articles
                    ])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No articles in database.")
            except Exception as e:
                st.error(f"Error loading articles: {e}")

    # ------------------ TAB 2: DOCUMENT INGESTION ------------------
    with admin_tab2:
        st.markdown("##### 📂 Ingest Documents (.PDF, .TXT, .MD)")
        st.caption("Upload clinic policy documents, physician rosters, or patient brochures. Text will be extracted, chunked, and indexed in Chroma.")

        uploaded_file = st.file_uploader("Choose a document", type=["txt", "md", "pdf"])

        col_doc_cat, col_doc_dept = st.columns(2)
        with col_doc_cat:
            doc_category = st.selectbox("Assign Category", CATEGORIES_DEFAULT, key="doc_cat_sel")
        with col_doc_dept:
            doc_department = st.selectbox("Assign Department", DEPARTMENTS_DEFAULT, key="doc_dept_sel")

        doc_title = st.text_input("Custom Document Title (Optional)", placeholder="Leave blank to use filename")

        if st.button("🚀 Ingest Document into Vector Store", disabled=uploaded_file is None):
            if uploaded_file is not None:
                with st.spinner(f"Parsing and chunking '{uploaded_file.name}'..."):
                    try:
                        file_bytes = uploaded_file.read()
                        res = client.upload_document(
                            file_bytes=file_bytes,
                            filename=uploaded_file.name,
                            title=doc_title if doc_title.strip() else None,
                            category=doc_category,
                            department=doc_department
                        )
                        st.success(f"✅ {res.get('message')} Generated **{res.get('chunks_created')}** searchable vector chunks.")
                    except Exception as e:
                        st.error(f"Error ingesting document: {e}")

    # ------------------ TAB 3: VECTOR INDEX CONTROL ------------------
    with admin_tab3:
        st.markdown("##### ⚙️ Vector Store Health & Synchronization")
        st.caption("Inspect and rebuild Chroma vector store to synchronize new or modified knowledge base articles.")

        try:
            status = client.get_index_status()
            col_v1, col_v2, col_v3 = st.columns(3)
            with col_v1:
                st.metric("Total Searchable Vectors", status.get("total_vectors", 0))
            with col_v2:
                st.metric("Published Articles", status.get("total_published_articles", 0))
            with col_v3:
                st.metric("Index Status", status.get("status", "Unknown").upper())

            st.write(f"**Embedding Model:** `{status.get('embedding_model')}`")
            st.write(f"**Collection Name:** `{status.get('collection_name')}`")
            if status.get("last_rebuild_time"):
                st.write(f"**Last Rebuilt:** `{status.get('last_rebuild_time')}`")

        except Exception as e:
            st.error(f"Could not connect to index service: {e}")

        st.divider()
        st.markdown("##### 🔄 Admin Re-indexing Workflow")
        st.info("Rebuilding clears outdated chunks and recalculates embeddings for all published articles and uploaded documents.")

        if st.button("⚡ Rebuild Vector Index Now", type="primary"):
            with st.spinner("Rebuilding Chroma vector index..."):
                try:
                    rebuild_res = client.rebuild_index()
                    st.success(
                        f"✅ Rebuild complete! Processed {rebuild_res.get('articles_processed')} articles, "
                        f"created {rebuild_res.get('total_vectors_created')} vectors."
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Rebuild failed: {e}")
