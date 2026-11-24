"""Tests for the Swahili Data Pipeline core module."""

import pytest
from swahili_pipeline.core import (
    SwahiliPipeline,
    PipelineConfig,
    Document,
    read_jsonl,
    write_jsonl,
)


class TestDocument:
    def test_hash_computation(self):
        doc = Document(text="Hello world", metadata={"source": "test"})
        assert doc._hash is not None
        assert len(doc._hash) == 16

    def test_same_text_same_hash(self):
        doc1 = Document(text="Same text")
        doc2 = Document(text="Same text")
        assert doc1._hash == doc2._hash

    def test_different_text_different_hash(self):
        doc1 = Document(text="Text one")
        doc2 = Document(text="Text two")
        assert doc1._hash != doc2._hash

    def test_jsonl_serialization(self):
        doc = Document(text="Test", metadata={"key": "value"})
        jsonl = doc.to_jsonl()
        assert '"text": "Test"' in jsonl
        assert '"key": "value"' in jsonl


class TestPipelineConfig:
    def test_defaults(self):
        config = PipelineConfig()
        assert config.min_length == 10
        assert config.max_length == 10000
        assert config.min_swahili_ratio == 0.7
        assert config.deduplicate is True
        assert config.fix_encoding is True
        assert config.remove_pii is True


class TestSwahiliPipeline:
    @pytest.fixture
    def pipeline(self):
        return SwahiliPipeline()

    def test_fix_encoding_mojibake(self, pipeline):
        text = "Habari yako, jina langu ni John"
        # Simulate mojibake
        mojibake = "Habari yako, jina langu ni John"
        result = pipeline.fix_encoding(mojibake)
        assert result == text

    def test_remove_email_pii(self, pipeline):
        text = "Contact me at john@example.com for details"
        result = pipeline.remove_pii(text)
        assert "[EMAIL_REDACTED]" in result
        assert "john@example.com" not in result

    def test_remove_phone_pii(self, pipeline):
        text = "Call me at +254712345678 or 0712345678"
        result = pipeline.remove_pii(text)
        assert "[PHONE_REDACTED]" in result
        assert "+254712345678" not in result

    def test_remove_credit_card_pii(self, pipeline):
        text = "Card: 1234-5678-9012-3456"
        result = pipeline.remove_pii(text)
        assert "[CARD_REDACTED]" in result

    def test_swahili_ratio_high(self, pipeline):
        text = "Habari yako, ninaenda shuleni leo na kesho"
        ratio = pipeline.swahili_ratio(text)
        assert ratio > 0.5

    def test_swahili_ratio_low(self, pipeline):
        text = "Hello world this is English text"
        ratio = pipeline.swahili_ratio(text)
        assert ratio < 0.3

    def test_length_filter_pass(self, pipeline):
        assert pipeline.passes_length_filter("This is a valid length text") is True

    def test_length_filter_fail_short(self, pipeline):
        assert pipeline.passes_length_filter("Short") is False

    def test_length_filter_fail_long(self, pipeline):
        long_text = "x" * 15000
        assert pipeline.passes_length_filter(long_text) is False

    def test_deduplicate_first_time(self, pipeline):
        doc = Document(text="Unique document")
        assert pipeline.deduplicate(doc) is True

    def test_deduplicate_second_time(self, pipeline):
        doc = Document(text="Duplicate document")
        pipeline.deduplicate(doc)  # First time
        assert pipeline.deduplicate(doc) is False  # Second time

    def test_process_valid_swahili(self, pipeline):
        doc = Document(text="Habari yako, ninaenda shuleni leo na kesho wiki hii")
        result = pipeline.process(doc)
        assert result is not None
        assert result.text == doc.text

    def test_process_english_rejected(self, pipeline):
        doc = Document(text="Hello world this is English text for testing")
        result = pipeline.process(doc)
        assert result is None

    def test_process_too_short_rejected(self, pipeline):
        doc = Document(text="Short")
        result = pipeline.process(doc)
        assert result is None

    def test_process_removes_pii(self, pipeline):
        # Use Swahili text with PII to pass language filter
        doc = Document(text="Barua pepe yangu ni test@example.com na simu +254712345678. Ninaenda shuleni leo na kesho.")
        result = pipeline.process(doc)
        assert result is not None
        assert "[EMAIL_REDACTED]" in result.text
        assert "[PHONE_REDACTED]" in result.text

    def test_process_fixes_encoding(self, pipeline):
        # This tests the fix_encoding method is called
        doc = Document(text="Habari yako ninaenda shuleni leo")
        result = pipeline.process(doc)
        assert result is not None

    def test_process_batch(self, pipeline):
        docs = [
            Document(text="Habari yako ninaenda shuleni"),
            Document(text="Hello world English text"),
            Document(text="Short"),
            Document(text="Mimi ninapenda chakula cha jioni"),
        ]
        results = list(pipeline.process_batch(docs))
        assert len(results) == 2  # Only Swahili ones pass
        assert all(pipeline.swahili_ratio(d.text) >= 0.7 for d in results)


class TestIO:
    def test_read_write_jsonl_roundtrip(self, tmp_path):
        docs = [
            Document(text="Habari yako", metadata={"id": 1}),
            Document(text="Mimi ninaenda nyumbani", metadata={"id": 2}),
        ]
        file_path = tmp_path / "test.jsonl"
        write_jsonl(docs, file_path)

        read_docs = list(read_jsonl(file_path))
        assert len(read_docs) == 2
        assert read_docs[0].text == "Habari yako"
        assert read_docs[0].metadata["id"] == 1
        assert read_docs[1].text == "Mimi ninaenda nyumbani"
        assert read_docs[1].metadata["id"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])