"""对象存储共享能力。"""

from app.shared.storage.client import (
    ObjectStream,
    StorageBucketMissingError,
    构建公开URL,
    构建存储键,
    检查存储健康,
    创建存储客户端,
    确保存储桶存在,
    获取对象字节,
    打开对象流,
    尽力删除对象,
    尽力删除多个对象,
    upload_bytes,
)
from app.shared.storage.file_url import (
    构建公开文件URL,
    构建签名文件URL,
    从文件URL提取存储键,
    签署文件请求,
    签署托管文件URL,
    签署文本中托管文件URL,
    验证已签署文件请求,
)

__all__ = [
    "ObjectStream",
    "StorageBucketMissingError",
    "构建公开文件URL",
    "构建公开URL",
    "构建签名文件URL",
    "构建存储键",
    "检查存储健康",
    "创建存储客户端",
    "确保存储桶存在",
    "从文件URL提取存储键",
    "获取对象字节",
    "打开对象流",
    "尽力删除对象",
    "尽力删除多个对象",
    "签署文件请求",
    "签署托管文件URL",
    "签署文本中托管文件URL",
    "upload_bytes",
    "验证已签署文件请求",
]
