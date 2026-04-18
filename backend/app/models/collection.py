"""收藏模型兼容入口。"""

from app.modules.collections.models import Collection, CollectionAsset, CollectionStatus, CollectionTag, CollectionTagRelation, CollectionType

__all__ = [
    "Collection",
    "CollectionAsset",
    "CollectionStatus",
    "CollectionTag",
    "CollectionTagRelation",
    "CollectionType",
]
