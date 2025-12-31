"""
Streamlit RAG Testing App - No Database Required
Test the RAG pipeline with custom queries
"""
import streamlit as st
import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Initialize logging
from src.utils.logging_config import setup_logging
setup_logging(log_level="INFO", log_dir="logs", enable_console=True, enable_file=True)

logger = logging.getLogger(__name__)
logger.info("Streamlit RAG Dashboard started")

from src.rag.vector_store import vector_store
from src.rag.reranker import reranker
from src.utils.query_logger import query_logger

# Page config
st.set_page_config(
    page_title="RAG Testing Dashboard",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 RAG Testing Dashboard")
st.markdown("Test your RAG pipeline with custom queries - **All queries logged to PostgreSQL**")

# Tabs
tab1, tab2 = st.tabs(["🔍 Search", "📊 Analytics"])

# Sidebar
with st.sidebar:
    st.header("Settings")
    top_k = st.slider("Number of results", min_value=1, max_value=10, value=5)
    use_reranking = st.checkbox("Use reranking", value=True)

    st.divider()

    st.header("Vector Store Stats")
    try:
        doc_count = vector_store.count()
        st.metric("Total Documents", doc_count)
    except Exception as e:
        st.error(f"Error: {str(e)}")

    st.divider()

    st.header("Sample Queries")
    st.markdown("""
    Try these:
    - How to handle stalled sales deals?
    - What to do with overdue tasks?
    - Strategies for multi-threading?
    - How to recover a red project?
    """)

# ===== TAB 1: SEARCH =====
with tab1:
    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Search Playbooks")

        # Query input
        query = st.text_input(
            "Enter your question:",
            placeholder="e.g., How do I revive a dead sales opportunity?",
            key="query_input"
        )

        search_button = st.button("🔍 Search", type="primary", use_container_width=True)

    with col2:
        st.header("Quick Actions")

        if st.button("🔄 Refresh Vector Store", use_container_width=True):
            st.rerun()

        if st.button("📊 Show All Playbooks", use_container_width=True):
            st.session_state['show_all'] = True

    # Search results
    if search_button and query:
        logger.info(f"User query: '{query}' | top_k={top_k} | reranking={use_reranking}")

        with st.spinner("Searching..."):
            try:
                # Perform search
                results = vector_store.similarity_search(query, top_k=top_k)
                logger.info(f"Vector search returned {len(results)} results")

                # Apply reranking if enabled
                if use_reranking and results:
                    results = reranker.rerank(query, results, top_k=top_k)
                    logger.info(f"Reranking completed, returning {len(results)} results")

                # Log query to database
                try:
                    query_id = query_logger.log_query(
                        query_text=query,
                        results=results,
                        top_k=top_k,
                        use_reranking=use_reranking,
                        user_session=st.session_state.get('session_id', 'streamlit')
                    )
                    logger.info(f"Query logged to database with ID: {query_id}")
                except Exception as log_error:
                    logger.warning(f"Failed to log query to database: {str(log_error)}")

                # Display results
                st.divider()
                st.subheader(f"Found {len(results)} Results")

                if not results:
                    st.warning("No results found. Try a different query.")
                else:
                    for i, result in enumerate(results, 1):
                        with st.expander(
                            f"Result {i} - Score: {result['score']:.4f} - "
                            f"{result['metadata'].get('title', 'Untitled')}",
                            expanded=(i == 1)
                        ):
                            # Metadata
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Playbook ID", result['metadata'].get('playbook_id', 'N/A'))
                            with col_b:
                                st.metric("Category", result['metadata'].get('category', 'N/A'))
                            with col_c:
                                score_label = "Rerank Score" if use_reranking and 'rerank_score' in result else "Similarity Score"
                                score_value = result.get('rerank_score', result['score'])
                                st.metric(score_label, f"{score_value:.4f}")

                            st.divider()

                            # Document content
                            st.markdown("**Content:**")
                            st.text_area(
                                "Document",
                                value=result['document'],
                                height=200,
                                key=f"doc_{i}",
                                label_visibility="collapsed"
                            )

            except Exception as e:
                logger.error(f"Search error for query '{query}': {str(e)}", exc_info=True)
                st.error(f"Search error: {str(e)}")
                st.exception(e)

    # Show all playbooks (if requested)
    if st.session_state.get('show_all', False):
        logger.info("User requested to view all playbooks")
        st.divider()
        st.subheader("All Playbooks in Vector Store")

        try:
            # Get sample of documents
            sample_results = vector_store.similarity_search("playbook strategy", top_k=20)
            logger.info(f"Retrieved {len(sample_results)} playbooks for display")

            st.info(f"Showing {len(sample_results)} playbooks")

            for i, result in enumerate(sample_results, 1):
                with st.expander(
                    f"{result['metadata'].get('playbook_id', 'N/A')} - "
                    f"{result['metadata'].get('title', 'Untitled')}"
                ):
                    st.markdown(f"**Category:** {result['metadata'].get('category', 'N/A')}")
                    st.text_area(
                        "Content",
                        value=result['document'][:500] + "...",
                        height=150,
                        key=f"all_{i}",
                        label_visibility="collapsed"
                    )

            if st.button("Hide All Playbooks"):
                st.session_state['show_all'] = False
                st.rerun()

        except Exception as e:
            st.error(f"Error loading playbooks: {str(e)}")

# ===== TAB 2: ANALYTICS =====
with tab2:
    st.header("📊 Query Analytics")

    # Get stats
    try:
        stats = query_logger.get_stats()

        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Queries", stats.get('total_queries', 0))
        with col2:
            st.metric("Total Chunks Retrieved", stats.get('total_chunks_retrieved', 0))
        with col3:
            st.metric("Avg Results/Query", stats.get('avg_results_per_query', 0))
        with col4:
            st.metric("Queries with Reranking", stats.get('queries_with_reranking', 0))

        st.divider()

        # Query History
        st.subheader("Recent Queries")
        history = query_logger.get_query_history(limit=20)

        if history:
            for query in history:
                with st.expander(f"{query['timestamp']} - {query['query_text'][:60]}..."):
                    st.write(f"**Full Query:** {query['query_text']}")
                    st.write(f"**Results:** {query['num_results']}")
                    st.write(f"**Top K:** {query['top_k']}")
                    st.write(f"**Reranking:** {'Yes' if query['use_reranking'] else 'No'}")
        else:
            st.info("No queries logged yet. Run some searches in the Search tab!")

        st.divider()

        # Top Queries
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Most Frequent Queries")
            top_queries = query_logger.get_top_queries(limit=10)

            if top_queries:
                for i, q in enumerate(top_queries, 1):
                    st.write(f"{i}. **{q['query_text']}** ({q['frequency']} times)")
            else:
                st.info("No query patterns yet")

        with col_b:
            st.subheader("Most Retrieved Playbooks")
            top_playbooks = query_logger.get_top_playbooks(limit=10)

            if top_playbooks:
                for i, p in enumerate(top_playbooks, 1):
                    st.write(
                        f"{i}. **{p['playbook_id']}** - {p['title']} "
                        f"({p['retrieval_count']} times, avg score: {p['avg_score']:.3f})"
                    )
            else:
                st.info("No playbooks retrieved yet")

    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
        st.exception(e)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    RAG Testing Dashboard | Queries logged to PostgreSQL | Powered by Weaviate + OpenAI
</div>
""", unsafe_allow_html=True)
