"""
Clinic Helpdesk KB Portal - Comprehensive Test Runner
Executes Week 1, Week 2, and Week 3 test suites with clear reporting.
"""
import sys
import time
import traceback
from pathlib import Path

# Force UTF-8 encoding on standard output for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def run_all_tests():
    print("=" * 70)
    print("RUNNING CLINIC HELPDESK KB PORTAL TEST SUITE (PRJ-090)")
    print("=" * 70)

    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    start_time = time.time()

    def run_test(name: str, test_func, *args, **kwargs):
        nonlocal total_tests, passed_tests, failed_tests
        total_tests += 1
        sys.stdout.write(f"  * {name:<55} ")
        sys.stdout.flush()
        try:
            test_func(*args, **kwargs)
            sys.stdout.write("[PASS]\n")
            passed_tests += 1
            return True
        except Exception as e:
            sys.stdout.write("[FAIL]\n")
            traceback.print_exc()
            failed_tests += 1
            return False

    # ------------------ WEEK 1: DOCUMENT LOADING & CHUNKING ------------------
    print("\n--- [WEEK 1 TESTS]: Chunking & Ingestion ---")
    try:
        from tests import test_chunking
        run_test("Text Splitter Configuration", test_chunking.test_text_splitter_configuration)
        run_test("Metadata & Chunk Index Preservation", test_chunking.test_chunk_text_metadata_preservation)
        run_test("FAQ Q&A Text Parser", test_chunking.test_parse_faq_txt)

        # Temporary path test
        import tempfile
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_test("Text/MD File Text Extraction", test_chunking.test_extract_text_from_txt_and_md, Path(tmp_dir))
    except Exception as e:
        print(f"Failed loading Week 1 tests: {e}")
        failed_tests += 1

    # ------------------ WEEK 2: RAG RETRIEVAL & CITATIONS ------------------
    print("\n--- [WEEK 2 TESTS]: RAG Retrieval, Citations & Fallback ---")
    try:
        from tests import test_rag_retrieval
        rag = test_rag_retrieval.get_test_rag_instance()

        run_test("Standard Query Retrieval & Accuracy", test_rag_retrieval.test_standard_query_retrieval, rag)
        run_test("Citation Structure & Fields Validation", test_rag_retrieval.test_citation_structure, rag)
        run_test("Emergency Triage Detection & Alert", test_rag_retrieval.test_emergency_query_triage, rag)
        run_test("Out-of-Scope Fallback Handling", test_rag_retrieval.test_out_of_scope_fallback_handling, rag)
    except Exception as e:
        print(f"Failed loading Week 2 tests: {e}")
        failed_tests += 1

    # ------------------ WEEK 3: FASTAPI E2E & ANALYTICS ------------------
    print("\n--- [WEEK 3 TESTS]: FastAPI Endpoints, Analytics & CRUD ---")
    try:
        from tests import test_api_e2e
        client = test_api_e2e.get_test_client()

        run_test("API Root & Health Check Endpoint", test_api_e2e.test_home_endpoint, client)
        run_test("Knowledge Article CRUD & Auto-Index", test_api_e2e.test_articles_crud, client)
        run_test("Chat Q&A Flow with Feedback Submission", test_api_e2e.test_chat_and_feedback_flow, client)
        run_test("Analytics Aggregation & Insights", test_api_e2e.test_analytics_summary, client)
        run_test("Vector Store Index Status & Rebuild", test_api_e2e.test_index_status_and_rebuild, client)
    except Exception as e:
        print(f"Failed loading Week 3 tests: {e}")
        failed_tests += 1

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"TEST EXECUTION SUMMARY:")
    print(f"  * Total Tests : {total_tests}")
    print(f"  * Passed      : {passed_tests} [PASS]")
    print(f"  * Failed      : {failed_tests} {'[FAIL]' if failed_tests > 0 else ''}")
    print(f"  * Elapsed Time: {elapsed:.2f}s")
    print("=" * 70)

    if failed_tests > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    run_all_tests()
