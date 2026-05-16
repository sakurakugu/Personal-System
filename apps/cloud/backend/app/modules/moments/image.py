"""动态图片服务。"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.operations import 最大上传字节数
from app.modules.files.upload_preparation import 是否为图片上传, 准备上传载荷
from app.modules.moments.models import 动态图片
from app.modules.moments.permissions import 确保动态写入权限
from app.modules.moments.presentation import 构建动态图片读取
from app.modules.moments.schemas import 动态图片排序更新, 动态图片信息
from app.modules.moments.service import 获取动态或404, 刷新动态最后编辑时间
from app.modules.users.models import 用户
from app.modules.feed.service import 清除Feed首页缓存
from app.shared.storage.client import 构建存储键, 尽力删除对象, upload_bytes

动态图片上限 = 20


def 构建动态图片目录(moment_id: str) -> str:
    """构造动态图片对象存储目录。"""
    return f"moments/{moment_id}"
async def 列出动态图片(
    db: AsyncSession,
    user: 用户,
    moment_id: str,
) -> list[动态图片信息]:
    """获取动态图片列表。"""
    moment = await 获取动态或404(db, moment_id)
    确保动态写入权限(moment, user)

    result = await db.execute(
        select(动态图片)
        .where(动态图片.moment_id == moment.id)
        .order_by(动态图片.sort_order.asc(), 动态图片.created_at.asc())
    )
    return [构建动态图片读取(record) for record in result.scalars().all()]


async def 上传动态图片(
    db: AsyncSession,
    user: 用户,
    moment_id: str,
    file: UploadFile,
) -> 动态图片信息:
    """上传动态图片。"""
    moment = await 获取动态或404(db, moment_id)
    确保动态写入权限(moment, user)

    current_count = (await db.execute(
        select(func.count()).select_from(动态图片).where(动态图片.moment_id == moment.id)
    )).scalar() or 0
    if current_count >= 动态图片上限:
        raise HTTPException(status_code=400, detail=f"动态最多只能上传 {动态图片上限} 张图片")

    content = await file.read()
    if len(content) > 最大上传字节数:
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    original_filename = file.filename or ""
    original_content_type = file.content_type or ""
    if not 是否为图片上传(original_filename, original_content_type):
        raise HTTPException(status_code=400, detail="动态图片只允许上传图片文件")

    prepared_upload = 准备上传载荷(
        filename=original_filename,
        content_type=original_content_type,
        content=content,
        compress_static_images=True,
    )
    storage_key = 构建存储键(
        user.id,
        prepared_upload.storage_name,
        directory=构建动态图片目录(moment_id),
    )
    upload_bytes(
        storage_key=storage_key,
        content=prepared_upload.content,
        content_type=prepared_upload.content_type,
    )

    record = 动态图片(
        moment_id=moment.id,
        original_name=prepared_upload.original_name,
        storage_key=storage_key,
        size=len(prepared_upload.content),
        mime_type=prepared_upload.content_type,
        sort_order=int(current_count),
    )
    db.add(record)
    刷新动态最后编辑时间(moment)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        尽力删除对象(storage_key)
        raise

    if moment.is_published:
        await 清除Feed首页缓存()
    await db.refresh(record)
    return 构建动态图片读取(record)


async def 重排动态图片(
    db: AsyncSession,
    user: 用户,
    moment_id: str,
    body: 动态图片排序更新,
) -> list[动态图片信息]:
    """更新动态图片顺序。"""
    moment = await 获取动态或404(db, moment_id)
    确保动态写入权限(moment, user)

    result = await db.execute(
        select(动态图片)
        .where(动态图片.moment_id == moment.id)
        .order_by(动态图片.sort_order.asc(), 动态图片.created_at.asc())
    )
    records = list(result.scalars().all())
    if len(records) != len(body.image_ids):
        raise HTTPException(status_code=400, detail="排序请求与当前图片数量不一致")

    current_ids = {record.id for record in records}
    requested_ids = set(body.image_ids)
    if current_ids != requested_ids:
        raise HTTPException(status_code=400, detail="排序请求包含无效图片")

    order_map = {image_id: index for index, image_id in enumerate(body.image_ids)}
    for record in records:
        record.sort_order = order_map[record.id]

    刷新动态最后编辑时间(moment)
    await db.commit()
    if moment.is_published:
        await 清除Feed首页缓存()

    records.sort(key=lambda item: item.sort_order)
    return [构建动态图片读取(record) for record in records]


async def 删除动态图片(
    db: AsyncSession,
    user: 用户,
    moment_id: str,
    image_id: str,
) -> None:
    """删除动态图片。"""
    moment = await 获取动态或404(db, moment_id)
    确保动态写入权限(moment, user)

    result = await db.execute(
        select(动态图片).where(
            动态图片.id == image_id,
            动态图片.moment_id == moment.id,
        )
    )
    image = result.scalar_one_or_none()
    if image is None:
        raise HTTPException(status_code=404, detail="图片不存在")

    storage_key = image.storage_key
    await db.delete(image)
    刷新动态最后编辑时间(moment)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    if moment.is_published:
        await 清除Feed首页缓存()
    尽力删除对象(storage_key)
