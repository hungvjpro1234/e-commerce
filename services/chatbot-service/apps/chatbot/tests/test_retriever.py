"""
Unit tests for the retriever module. No database or OpenAI required.
"""

from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.chatbot.retriever import cosine_similarity, lexical_retrieve


class FakeChunk:
    def __init__(self, content, *, source_type="product", product_service="", source_id="", embedding=None):
        self.content = content
        self.embedding = embedding
        self.id = "fake-id"
        self.document = MagicMock(
            title="Fake Doc",
            source_type=source_type,
            product_service=product_service,
            source_id=source_id,
            updated_at=1,
        )


class LexicalRetrieveTests(SimpleTestCase):
    def _make_chunks(self, texts):
        return [FakeChunk(text) for text in texts]

    def test_returns_most_relevant_chunk_first(self):
        chunks = self._make_chunks([
            "Dell XPS laptop with 16GB RAM and 512GB SSD storage",
            "Return policy: 30 day returns for unused items",
            "Apple iPhone 15 mobile phone with 128GB storage",
        ])
        result = lexical_retrieve("laptop RAM storage", chunks, top_k=2)
        self.assertEqual(len(result), 2)
        self.assertIn("laptop", result[0].content)

    def test_returns_empty_when_no_overlap(self):
        chunks = self._make_chunks(["cat sat on mat", "dog ran fast"])
        result = lexical_retrieve("laptop price", chunks, top_k=5)
        self.assertEqual(result, [])

    def test_respects_top_k(self):
        chunks = self._make_chunks([
            "laptop laptop laptop",
            "laptop keyboard",
            "laptop screen display",
            "laptop battery power",
        ])
        result = lexical_retrieve("laptop", chunks, top_k=2)
        self.assertEqual(len(result), 2)

    def test_prioritizes_matching_domain(self):
        chunks = [
            FakeChunk("Beauty serum with niacinamide and hydration", product_service="beauty"),
            FakeChunk("Cotton hoodie for men and women", product_service="cloth"),
        ]
        result = lexical_retrieve("serum hydration", chunks, top_k=1, domain="beauty", intent="product")
        self.assertEqual(result[0].document.product_service, "beauty")

    def test_empty_chunk_list(self):
        result = lexical_retrieve("anything", [], top_k=5)
        self.assertEqual(result, [])


class CosineSimilarityTests(SimpleTestCase):
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        self.assertAlmostEqual(cosine_similarity(v, v), 1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        self.assertAlmostEqual(cosine_similarity(a, b), 0.0)

    def test_zero_vector(self):
        self.assertEqual(cosine_similarity([0.0, 0.0], [1.0, 2.0]), 0.0)
