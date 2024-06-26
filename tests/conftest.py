from collections.abc import Sequence
from contextlib import contextmanager

import pytest
from wagtail_vector_index.ai_utils.backends.base import (
    BaseChatBackend,
    BaseChatConfig,
    BaseEmbeddingBackend,
    BaseEmbeddingConfig,
)
from wagtail_vector_index.ai_utils.types import AIResponse


@pytest.fixture
def patch_embedding_fields():
    @contextmanager
    def _patch_embedding_fields(model, new_embedding_fields):
        old_embedding_fields = model.embedding_fields
        model.embedding_fields = new_embedding_fields
        yield
        model.embedding_fields = old_embedding_fields

    return _patch_embedding_fields


class ChatMockBackend(BaseChatBackend):
    config_cls = BaseChatConfig

    def chat(self, messages: Sequence[str]) -> AIResponse:
        return AIResponse(choices=["AI! Don't talk to me about AI!"])


class EmbeddingMockBackend(BaseEmbeddingBackend):
    config_cls = BaseEmbeddingConfig

    def embed(self, inputs):
        values = [
            i * self.embedding_output_dimensions
            for i in range(self.embedding_output_dimensions)
        ]
        for _ in inputs:
            yield values


@pytest.fixture(autouse=True)
def use_mock_ai_backend(settings):
    settings.WAGTAIL_VECTOR_INDEX = {
        "EMBEDDING_BACKENDS": {
            "default": {
                "CLASS": "conftest.EmbeddingMockBackend",
                "CONFIG": {
                    "MODEL_ID": "mock-embedding",
                    "TOKEN_LIMIT": 1024,
                    "EMBEDDING_OUTPUT_DIMENSIONS": 6,
                },
            }
        },
        "CHAT_BACKENDS": {
            "default": {
                "CLASS": "conftest.ChatMockBackend",
                "CONFIG": {
                    "MODEL_ID": "mock-chat",
                    "TOKEN_LIMIT": 1024,
                },
            }
        },
    }
