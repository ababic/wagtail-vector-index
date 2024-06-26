from collections.abc import Generator, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.models import Distance

from wagtail_vector_index.storage.base import (
    Document,
    StorageProvider,
    StorageVectorIndexMixinProtocol,
)


@dataclass
class ProviderConfig:
    HOST: str
    API_KEY: str | None = None


if TYPE_CHECKING:
    MixinBase = StorageVectorIndexMixinProtocol["QdrantStorageProvider"]
else:
    MixinBase = object


class QdrantIndexMixin(MixinBase):
    def __init__(self, **kwargs: Any) -> None:
        self.index_name = self.__class__.__name__
        self.storage_provider = self._get_storage_provider()
        super().__init__(**kwargs)

    def rebuild_index(self) -> None:
        self.storage_provider.client.delete_collection(collection_name=self.index_name)
        self.storage_provider.client.create_collection(
            collection_name=self.index_name,
            vectors_config=qdrant_models.VectorParams(
                size=512, distance=Distance.COSINE
            ),
        )
        self.upsert(documents=self.get_documents())

    def upsert(self, *, documents: Iterable[Document]) -> None:
        points = [
            qdrant_models.PointStruct(
                id=document.embedding_pk,
                vector=document.vector,
                payload=document.metadata,
            )
            for document in documents
        ]
        self.storage_provider.client.upsert(
            collection_name=self.index_name, points=points
        )

    def delete(self, *, document_ids: Sequence[str]) -> None:
        self.storage_provider.client.delete(
            collection_name=self.index_name,
            points_selector=qdrant_models.PointIdsList(points=document_ids),
        )

    def get_similar_documents(
        self, query_vector: Sequence[float], *, limit: int = 5
    ) -> Generator[Document, None, None]:
        similar_documents = self.storage_provider.client.search(
            collection_name=self.index_name, query_vector=query_vector, limit=limit
        )
        for doc in similar_documents:
            yield Document(
                embedding_pk=doc["id"], vector=doc["vector"], metadata=doc["payload"]
            )


class QdrantStorageProvider(StorageProvider[ProviderConfig, QdrantIndexMixin]):
    config_class = ProviderConfig
    index_mixin = QdrantIndexMixin

    def __init__(self, config: Mapping[str, Any]) -> None:
        super().__init__(config)
        self.client = QdrantClient(url=self.config.HOST, api_key=self.config.API_KEY)

    def rebuild_indexes(self) -> None:
        pass
