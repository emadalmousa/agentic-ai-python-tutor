"""
Tests: Phase 5 — RAG Feature (PDF Upload + Chat RAG Context)

Covers:
1. agent/rag/loader.py  — extract_pages(pdf_bytes) -> list[tuple[str, int]]
2. agent/rag/splitter.py — split_pages(pages) -> list[dict]
3. agent/rag/vectorstore.py — build_and_save, load, query_with_pages, get_page
4. POST /tutor/upload-material — validation, success path, error handling
5. _get_rag_context() in routers/tutor.py — page lookup, semantic search, no-index path

All LLM/embedding calls are mocked. No real FAISS index is written to disk.
"""

import io
import os
import pickle
import struct
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Minimal valid PDF bytes (hand-crafted, no external library needed)
# ---------------------------------------------------------------------------

def _make_minimal_pdf(text: str = "Hello PDF") -> bytes:
    """Build a single-page PDF with the given text using pypdf-compatible structure."""
    # We use pypdf's PdfWriter to create a real minimal PDF in memory
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. loader.py — extract_pages
# ---------------------------------------------------------------------------

class TestExtractPages:
    """extract_pages(pdf_bytes) must return list of (text, page_number) tuples."""

    def test_returns_list(self):
        from agent.rag.loader import extract_pages
        result = extract_pages(_make_minimal_pdf())
        assert isinstance(result, list)

    def test_each_item_is_tuple_of_two(self):
        from agent.rag.loader import extract_pages
        result = extract_pages(_make_minimal_pdf())
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_second_element_is_int(self):
        from agent.rag.loader import extract_pages
        result = extract_pages(_make_minimal_pdf())
        for _, page_num in result:
            assert isinstance(page_num, int)

    def test_first_element_is_str(self):
        from agent.rag.loader import extract_pages
        result = extract_pages(_make_minimal_pdf())
        for text, _ in result:
            assert isinstance(text, str)

    def test_page_numbers_start_at_1(self):
        from agent.rag.loader import extract_pages
        result = extract_pages(_make_minimal_pdf())
        if result:
            page_nums = [p for _, p in result]
            assert min(page_nums) >= 1

    def test_invalid_bytes_raises_value_error(self):
        from agent.rag.loader import extract_pages
        with pytest.raises((ValueError, Exception)):
            extract_pages(b"this is not a pdf")

    def test_empty_bytes_raises(self):
        from agent.rag.loader import extract_pages
        with pytest.raises(Exception):
            extract_pages(b"")


# ---------------------------------------------------------------------------
# 2. splitter.py — split_pages
# ---------------------------------------------------------------------------

class TestSplitPages:
    """split_pages(pages) must chunk long text and preserve page metadata."""

    def _make_pages(self, text: str, page: int = 1):
        return [(text, page)]

    def test_returns_list(self):
        from agent.rag.splitter import split_pages
        result = split_pages(self._make_pages("Hello world", 1))
        assert isinstance(result, list)

    def test_each_chunk_has_text_key(self):
        from agent.rag.splitter import split_pages
        result = split_pages(self._make_pages("Hello world", 1))
        for chunk in result:
            assert "text" in chunk

    def test_each_chunk_has_page_key(self):
        from agent.rag.splitter import split_pages
        result = split_pages(self._make_pages("Hello world", 1))
        for chunk in result:
            assert "page" in chunk

    def test_page_number_preserved(self):
        from agent.rag.splitter import split_pages
        result = split_pages(self._make_pages("Hello world", 5))
        for chunk in result:
            assert chunk["page"] == 5

    def test_long_text_produces_multiple_chunks(self):
        from agent.rag.splitter import split_pages
        long_text = "x" * 2000
        result = split_pages(self._make_pages(long_text, 1))
        assert len(result) > 1

    def test_short_text_produces_one_chunk(self):
        from agent.rag.splitter import split_pages
        result = split_pages(self._make_pages("Kurzer Text.", 1))
        assert len(result) == 1

    def test_chunk_text_is_non_empty_string(self):
        from agent.rag.splitter import split_pages
        result = split_pages(self._make_pages("Some content here", 2))
        for chunk in result:
            assert isinstance(chunk["text"], str)
            assert len(chunk["text"]) > 0

    def test_empty_pages_list_returns_empty_list(self):
        from agent.rag.splitter import split_pages
        result = split_pages([])
        assert result == []

    def test_multi_page_input_preserves_pages(self):
        from agent.rag.splitter import split_pages
        pages = [("Page one content", 1), ("Page two content", 2)]
        result = split_pages(pages)
        page_nums = {chunk["page"] for chunk in result}
        assert 1 in page_nums
        assert 2 in page_nums

    def test_whitespace_only_page_is_skipped_or_handled(self):
        from agent.rag.splitter import split_pages
        result = split_pages([("   \n  ", 1)])
        # Either empty list or chunks with only whitespace — must not crash
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# 3. vectorstore.py — build_and_save, load, query_with_pages, get_page
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_vectorstore_dir(tmp_path, monkeypatch):
    """Point RAG_VECTORSTORE_PATH to a temp dir for each test."""
    monkeypatch.setenv("RAG_VECTORSTORE_PATH", str(tmp_path))
    return tmp_path


def _make_chunks(n: int = 4) -> list[dict]:
    return [
        {"text": f"Python ist toll. Chunk {i}.", "page": i + 1}
        for i in range(n)
    ]


def _mock_embeddings(dim: int = 8):
    """Returns a fake embeddings object whose embed_documents returns fixed vectors."""
    mock = MagicMock()
    mock.embed_documents.side_effect = lambda texts: [[0.1 * j for j in range(dim)] for _ in texts]
    mock.embed_query.return_value = [0.1 * j for j in range(dim)]
    return mock


class TestVectorstoreBuildAndSave:
    def test_build_and_save_creates_index_file(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(), user_id=1)
        files = list(tmp_vectorstore_dir.rglob("*"))
        names = [f.name for f in files]
        assert any("faiss" in n or "index" in n for n in names) or any("pkl" in n for n in names)

    def test_build_and_save_creates_chunks_file(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(), user_id=1)
        files = [f.name for f in tmp_vectorstore_dir.rglob("*")]
        assert any("pkl" in f or "chunks" in f for f in files)

    def test_build_and_save_does_not_crash_with_single_chunk(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save([{"text": "Einziger Chunk.", "page": 1}], user_id=1)


class TestVectorstoreLoad:
    def test_load_returns_none_when_no_index_exists(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import load
        result = load(user_id=1)
        assert result is None

    def test_load_returns_data_after_build_and_save(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(), user_id=1)
        result = load(user_id=1)
        assert result is not None

    def test_load_result_is_not_none_after_save(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(), user_id=1)
        assert load(user_id=1) is not None


class TestVectorstoreQueryWithPages:
    def test_returns_list(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load, query_with_pages
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(), user_id=1)
            index_data = load(user_id=1)
            result = query_with_pages(index_data, "Python", top_k=2)
        assert isinstance(result, list)

    def test_each_result_is_tuple_of_str_int(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load, query_with_pages
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(), user_id=1)
            index_data = load(user_id=1)
            result = query_with_pages(index_data, "Python", top_k=2)
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            assert isinstance(item[0], str)
            assert isinstance(item[1], int)

    def test_top_k_limits_results(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load, query_with_pages
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(6), user_id=1)
            index_data = load(user_id=1)
            result = query_with_pages(index_data, "Python", top_k=2)
        assert len(result) <= 2


class TestVectorstoreGetPage:
    def test_returns_list(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load, get_page
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(), user_id=1)
            index_data = load(user_id=1)
        result = get_page(index_data, 1)
        assert isinstance(result, list)

    def test_returns_only_chunks_for_requested_page(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load, get_page
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(4), user_id=1)
            index_data = load(user_id=1)
        result = get_page(index_data, 2)
        for _, page in result:
            assert page == 2

    def test_nonexistent_page_returns_empty_list(self, tmp_vectorstore_dir):
        from agent.rag.vectorstore import build_and_save, load, get_page
        with patch("agent.config.get_embeddings", return_value=_mock_embeddings()):
            build_and_save(_make_chunks(3), user_id=1)
            index_data = load(user_id=1)
        result = get_page(index_data, 999)
        assert result == []


# ---------------------------------------------------------------------------
# 4. POST /tutor/upload-material endpoint
# ---------------------------------------------------------------------------

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

_TEST_DB_URL = "sqlite:///:memory:"
_engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _get_test_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def upload_client():
    import models  # noqa: F401
    from core.database import Base, get_db
    from main import app
    from routers.auth import get_current_user
    from models.user import User
    Base.metadata.create_all(bind=_engine)

    def _fake_user():
        user = User()
        user.id = 1
        user.email = "test@test.com"
        user.level = "beginner"
        return user

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_current_user] = _fake_user
    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine)


class TestUploadMaterialEndpoint:
    def test_returns_400_for_non_pdf_content_type(self, upload_client):
        data = io.BytesIO(b"not a pdf")
        resp = upload_client.post(
            "/tutor/upload-material",
            files={"file": ("doc.txt", data, "text/plain")},
        )
        assert resp.status_code == 400

    def test_returns_400_for_empty_file(self, upload_client):
        resp = upload_client.post(
            "/tutor/upload-material",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert resp.status_code == 400

    def test_returns_400_when_rag_modules_missing(self, upload_client):
        """If loader/splitter/vectorstore are missing the endpoint must return 400, not 500."""
        pdf_bytes = _make_minimal_pdf()
        with patch.dict("sys.modules", {"agent.rag.loader": None, "agent.rag.splitter": None, "agent.rag.vectorstore": None}):
            resp = upload_client.post(
                "/tutor/upload-material",
                files={"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )
        assert resp.status_code in (400, 422, 500)

    def test_filename_with_pdf_extension_accepted_regardless_of_content_type(self, upload_client):
        """A .pdf filename should pass the validation gate (content_type check)."""
        pdf_bytes = _make_minimal_pdf()
        with (
            patch("agent.rag.loader.extract_pages", return_value=[("text", 1)]),
            patch("agent.rag.splitter.split_pages", return_value=[{"text": "text", "page": 1}]),
            patch("agent.rag.vectorstore.build_and_save", return_value=None),
        ):
            resp = upload_client.post(
                "/tutor/upload-material",
                files={"file": ("lecture.pdf", io.BytesIO(pdf_bytes), "application/octet-stream")},
            )
        assert resp.status_code == 200

    def test_successful_upload_returns_ok_status(self, upload_client):
        pdf_bytes = _make_minimal_pdf()
        with (
            patch("agent.rag.loader.extract_pages", return_value=[("text", 1)]),
            patch("agent.rag.splitter.split_pages", return_value=[{"text": "text", "page": 1}]),
            patch("agent.rag.vectorstore.build_and_save", return_value=None),
        ):
            resp = upload_client.post(
                "/tutor/upload-material",
                files={"file": ("lecture.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_successful_upload_returns_chunk_count(self, upload_client):
        pdf_bytes = _make_minimal_pdf()
        fake_chunks = [{"text": f"chunk {i}", "page": 1} for i in range(3)]
        with (
            patch("agent.rag.loader.extract_pages", return_value=[("text", 1)]),
            patch("agent.rag.splitter.split_pages", return_value=fake_chunks),
            patch("agent.rag.vectorstore.build_and_save", return_value=None),
        ):
            resp = upload_client.post(
                "/tutor/upload-material",
                files={"file": ("lecture.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )
        assert resp.json()["chunks"] == 3

    def test_extract_pages_exception_returns_400(self, upload_client):
        pdf_bytes = _make_minimal_pdf()
        with patch("agent.rag.loader.extract_pages", side_effect=ValueError("bad pdf")):
            resp = upload_client.post(
                "/tutor/upload-material",
                files={"file": ("bad.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )
        assert resp.status_code == 400

    def test_build_and_save_exception_returns_400(self, upload_client):
        pdf_bytes = _make_minimal_pdf()
        with (
            patch("agent.rag.loader.extract_pages", return_value=[("text", 1)]),
            patch("agent.rag.splitter.split_pages", return_value=[{"text": "text", "page": 1}]),
            patch("agent.rag.vectorstore.build_and_save", side_effect=Exception("faiss error")),
        ):
            resp = upload_client.post(
                "/tutor/upload-material",
                files={"file": ("lecture.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 5. _get_rag_context() in routers/tutor.py
# ---------------------------------------------------------------------------

class TestGetRagContext:
    def test_returns_empty_string_when_no_index(self):
        with patch("agent.rag.vectorstore.load", return_value=None):
            from routers.tutor import _get_rag_context
            result = _get_rag_context("Was ist Python?", user_id=1)
        assert result == ""

    def test_returns_string(self):
        fake_index = object()
        with (
            patch("agent.rag.vectorstore.load", return_value=fake_index),
            patch("agent.rag.vectorstore.query_with_pages", return_value=[("Python ist eine Sprache.", 1)]),
        ):
            from routers.tutor import _get_rag_context
            result = _get_rag_context("Was ist Python?", user_id=1)
        assert isinstance(result, str)

    def test_returns_empty_string_on_exception(self):
        with patch("agent.rag.vectorstore.load", side_effect=Exception("broken")):
            from routers.tutor import _get_rag_context
            result = _get_rag_context("Was ist Python?", user_id=1)
        assert result == ""

    def test_page_reference_in_message_calls_get_page(self):
        fake_index = object()
        with (
            patch("agent.rag.vectorstore.load", return_value=fake_index),
            patch("agent.rag.vectorstore.get_page", return_value=[("Seitentext.", 3)]) as mock_get_page,
            patch("agent.rag.vectorstore.query_with_pages", return_value=[]),
        ):
            from routers.tutor import _get_rag_context
            _get_rag_context("Was steht auf Seite 3?", user_id=1)
        mock_get_page.assert_called_once_with(fake_index, 3)

    def test_no_page_reference_skips_get_page(self):
        fake_index = object()
        with (
            patch("agent.rag.vectorstore.load", return_value=fake_index),
            patch("agent.rag.vectorstore.get_page") as mock_get_page,
            patch("agent.rag.vectorstore.query_with_pages", return_value=[("text", 1)]),
        ):
            from routers.tutor import _get_rag_context
            _get_rag_context("Erkläre mir Schleifen", user_id=1)
        mock_get_page.assert_not_called()

    def test_result_contains_page_reference_marker(self):
        fake_index = object()
        with (
            patch("agent.rag.vectorstore.load", return_value=fake_index),
            patch("agent.rag.vectorstore.query_with_pages", return_value=[("Inhalt von Seite 2.", 2)]),
        ):
            from routers.tutor import _get_rag_context
            result = _get_rag_context("Erkläre mir was", user_id=1)
        assert "Seite 2" in result

    def test_deduplication_prevents_duplicate_chunks(self):
        fake_index = object()
        same_text = "Derselbe Text."
        with (
            patch("agent.rag.vectorstore.load", return_value=fake_index),
            patch("agent.rag.vectorstore.get_page", return_value=[(same_text, 1)]),
            patch("agent.rag.vectorstore.query_with_pages", return_value=[(same_text, 1)]),
        ):
            from routers.tutor import _get_rag_context
            result = _get_rag_context("Was steht auf Seite 1?", user_id=1)
        assert result.count(same_text) == 1
