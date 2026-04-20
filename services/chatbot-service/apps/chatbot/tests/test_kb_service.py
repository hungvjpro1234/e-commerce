"""
Tests for KB seeding and product normalization.
Product services are mocked so no real HTTP calls are made.
"""

from django.test import TestCase

from apps.chatbot.kb_service import seed_static_kb
from apps.chatbot.models import KnowledgeDocument
from apps.chatbot.product_fetcher import _build_document_sections


class StaticKBSeedTests(TestCase):
    def test_seed_creates_policy_and_faq_documents(self):
        docs, chunks = seed_static_kb()

        self.assertGreater(docs, 0)
        self.assertGreater(chunks, 0)

        policy_count = KnowledgeDocument.objects.filter(source_type="policy").count()
        faq_count = KnowledgeDocument.objects.filter(source_type="faq").count()

        self.assertGreater(policy_count, 0)
        self.assertGreater(faq_count, 0)

    def test_seed_is_idempotent(self):
        docs1, _ = seed_static_kb()
        docs2, _ = seed_static_kb()

        self.assertEqual(docs1, docs2)
        self.assertEqual(KnowledgeDocument.objects.count(), docs1)


class ProductFetcherNormalizationTests(TestCase):
    def test_build_document_sections_cloth(self):
        product = {
            "name": "Summer Hoodie",
            "description": "Lightweight cotton hoodie",
            "price": "29.99",
            "stock": 15,
            "is_active": True,
            "size": "M",
            "material": "Cotton",
            "color": "Blue",
            "gender": "Unisex",
        }
        sections = _build_document_sections(product, "cloth", ["size", "material", "color", "gender"])
        self.assertTrue(any("Summer Hoodie" in section for section in sections))
        self.assertTrue(any("29.99" in section for section in sections))
        self.assertTrue(any("Cotton" in section for section in sections))
        self.assertTrue(any("Blue" in section for section in sections))

    def test_build_document_sections_laptop(self):
        product = {
            "name": "Dell XPS 15",
            "description": "Premium ultrabook",
            "price": "1299.99",
            "stock": 5,
            "is_active": True,
            "brand": "Dell",
            "cpu": "Intel i7",
            "ram_gb": 16,
            "storage_gb": 512,
            "display_size": 15.6,
        }
        sections = _build_document_sections(
            product, "laptop", ["brand", "cpu", "ram_gb", "storage_gb", "display_size"]
        )
        joined = "\n".join(sections)
        self.assertIn("Dell XPS 15", joined)
        self.assertIn("Intel i7", joined)
        self.assertIn("1299.99", joined)

    def test_build_document_sections_accessory(self):
        product = {
            "name": "Logitech MX Master 3S",
            "description": "Wireless productivity mouse",
            "price": "109.00",
            "stock": 20,
            "is_active": True,
            "brand": "Logitech",
            "accessory_type": "Mouse",
            "compatibility": "Windows, macOS",
            "wireless": "Yes",
            "warranty_months": 24,
        }
        sections = _build_document_sections(
            product,
            "accessory",
            ["brand", "accessory_type", "compatibility", "wireless", "warranty_months"],
        )
        joined = "\n".join(sections)
        self.assertIn("Logitech MX Master 3S", joined)
        self.assertIn("Mouse", joined)
        self.assertIn("24", joined)
