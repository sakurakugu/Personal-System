"""动态图片服务。"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.files.operations import 最大上传字节数
from app.modules.files.upload_preparation import is_image_upload, prepare_upload_payload
from app.modules.moments.models import MomentImage
from app.modules.moments.permissions import ensure_moment_write_permission
from app.modules.moments.presentation import build_moment_image_read
from app.modules.moments.schemas import MomentImageOrderUpdate, MomentImageRead
from app.modules.moments.service import get_moment_or_404
from app.modules.users.models import User
from app.shared.storage.client import build_storage_key, remove_object_best_effort, upload_bytes

动态图片上限 = 20


def build_moment_image_directory(moment_id: str) -> str:
    """构造动态图片对象存储目录。"""
    return f"moments/{moment_id}"
async def list_moment_images(
    db: AsyncSession,
    user: User,
    moment_id: str,
) -> list[MomentImageRead]:
    """获取动态图片列表。"""
    moment = await get_moment_or_404(db, moment_id)
    ensure_moment_write_permission(moment, user)

    result = await db.execute(
        select(MomentImage)
        .where(MomentImage.moment_id == moment.id)
        .order_by(MomentImage.sort_order.asc(), MomentImage.created_at.asc())
    )
    return [build_moment_image_read(record) for record in result.scalars().all()]


async def upload_moment_image(
    db: AsyncSession,
    user: User,
    moment_id: str,
    file: UploadFile,
) -> MomentImageRead:
    """上传动态图片。"""
    moment = await get_moment_or_404(db, moment_id)
    ensure_moment_write_permission(moment, user)

    current_count = (await db.execute(
        select(func.count()).select_from(MomentImage).where(MomentImage.moment_id == moment.id)
    )).scalar() or 0
    if current_count >= 动态图片上限:
        raise HTTPException(status_code=400, detail=f"动态最多只能上传 {动态图片上限} 张图片")

    content = await file.read()
    if len(content) > 最大上传字节数:
        raise HTTPException(status_code=413, detail="文件过大（最大 10MB）")

    original_filename = file.filename or ""
    original_content_type = file.content_type or ""
    if not is_image_upload(original_filename, original_content_type):
        raise HTTPException(status_code=400, detail="动态图片只允许上传图片文件")

    prepared_upload = prepare_upload_payload(
        filename=original_filename,
        content_type=original_content_type,
        content=content,
        compress_static_images=True,
    )
    storage_key = build_storage_key(
        user.id,
        prepared_upload.storage_name,
        directory=build_moment_image_directory(moment_id),
    )
    upload_bytes(
        storage_key=storage_key,
        content=prepared_upload.content,
        content_type=prepared_upload.content_type,
    )

    record = MomentImage(
        moment_id=moment.id,
        original_name=prepared_upload.original_name,
        storage_key=storage_key,
        size=len(prepared_upload.content),
        mime_type=prepared_upload.content_type,
        sort_order=int(current_count),
    )
    db.add(record)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        remove_object_best_effort(storage_key)
        raise

    await db.refresh(record)
    return build_moment_image_read(record)


async def reorder_moment_images(
    db: AsyncSession,
    user: User,
    moment_id: str,
    body: MomentImageOrderUpdate,
) -> list[MomentImageRead]:
    """更新动态图片顺序。"""
    moment = await get_moment_or_404(db, moment_id)
    ensure_moment_write_permission(moment, user)

    result = await db.execute(
        select(MomentImage)
        .where(MomentImage.moment_id == moment.id)
        .order_by(MomentImage.sort_order.asc(), MomentImage.created_at.asc())
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

    await db.commit()

    records.sort(key=lambda item: item.sort_order)
    return [build_moment_image_read(record) for record in records]


async def delete_moment_image(
    db: AsyncSession,
    user: User,
    moment_id: str,
    image_id: str,
) -> None:
    """删除动态图片。"""
    moment = await get_moment_or_404(db, moment_id)
    ensure_moment_write_permission(moment, user)

    result = await db.execute(
        select(MomentImage).where(
            MomentImage.id == image_id,
            MomentImage.moment_id == moment.id,
        )
    )
    image = result.scalar_one_or_none()
    if image is None:
        raise HTTPException(status_code=404, detail="图片不存在")

    storage_key = image.storage_key
    await db.delete(image)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    remove_object_best_effort(storage_key)
