"""文件服务测试。"""

from __future__ import annotations

import io
import unittest
import zipfile
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from PIL import Image

from app.models.file import File, FileFolder, FilePurpose
from app.models.user import User, UserRole
from app.services.file_service import (
    build_archive_payload,
    build_archive_file_path,
    build_folder_breadcrumbs,
    build_folder_full_path,
    build_folder_tree_nodes,
    prepare_upload_payload,
    search_resources,
)


def create_png_bytes() -> bytes:
    """构造静态 PNG 图片。"""
    image = Image.new("RGBA", (8, 8), (255, 0, 0, 255))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def create_animated_gif_bytes() -> bytes:
    """构造两帧 GIF 动图。"""
    first = Image.new("RGB", (8, 8), (255, 0, 0))
    second = Image.new("RGB", (8, 8), (0, 0, 255))
    output = io.BytesIO()
    first.save(output, format="GIF", save_all=True, append_images=[second], loop=0, duration=120)
    return output.getvalue()


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_user() -> User:
    """构造测试用户。"""
    return User(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hash",
        role=UserRole.user,
    )


def build_scalars_result(records: list[object]) -> SimpleNamespace:
    """构造支持 scalars().all() 的查询结果桩。"""
    return SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: records,
        )
    )


class FileServiceTest(unittest.TestCase):
    """文件服务纯逻辑测试。"""

    def test_静态位图会转换为_avif(self) -> None:
        prepared = prepare_upload_payload(
            "cover.png",
            "image/png",
            create_png_bytes(),
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "cover.png")
        self.assertEqual(prepared.storage_name, "cover.avif")
        self.assertEqual(prepared.content_type, "image/avif")
        self.assertNotEqual(prepared.content[:16], create_png_bytes()[:16])

        with Image.open(io.BytesIO(prepared.content)) as converted:
            self.assertEqual(converted.format, "AVIF")
            self.assertEqual(converted.size, (8, 8))

    def test_svg_保持原格式(self) -> None:
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"></svg>'

        prepared = prepare_upload_payload(
            "vector.svg",
            "image/svg+xml",
            svg_content,
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "vector.svg")
        self.assertEqual(prepared.storage_name, "vector.svg")
        self.assertEqual(prepared.content_type, "image/svg+xml")
        self.assertEqual(prepared.content, svg_content)

    def test_动图保持原格式(self) -> None:
        gif_content = create_animated_gif_bytes()

        prepared = prepare_upload_payload(
            "motion.gif",
            "image/gif",
            gif_content,
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "motion.gif")
        self.assertEqual(prepared.storage_name, "motion.gif")
        self.assertEqual(prepared.content_type, "image/gif")
        self.assertEqual(prepared.content, gif_content)

    def test_普通上传图片保持原格式(self) -> None:
        png_content = create_png_bytes()

        prepared = prepare_upload_payload(
            "cover.png",
            "image/png",
            png_content,
            compress_static_images=False,
        )

        self.assertEqual(prepared.original_name, "cover.png")
        self.assertEqual(prepared.storage_name, "cover.png")
        self.assertEqual(prepared.content_type, "image/png")
        self.assertEqual(prepared.content, png_content)

    def test_空文件名图片会自动补_avif_名称(self) -> None:
        prepared = prepare_upload_payload(
            "",
            "image/png",
            create_png_bytes(),
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "image.png")
        self.assertEqual(prepared.storage_name, "image.avif")
        self.assertEqual(prepared.content_type, "image/avif")

    def test_文件夹树会按层级构造(self) -> None:
        user_id = uuid4()
        root_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=None, name="资料库")
        child_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=root_folder.id, name="封面")
        leaf_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=child_folder.id, name="文章")

        tree = build_folder_tree_nodes([root_folder, child_folder, leaf_folder])

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0].name, "资料库")
        self.assertEqual(len(tree[0].children), 1)
        self.assertEqual(tree[0].children[0].name, "封面")
        self.assertEqual(len(tree[0].children[0].children), 1)
        self.assertEqual(tree[0].children[0].children[0].name, "文章")

    def test_面包屑会包含根目录与当前路径(self) -> None:
        user_id = uuid4()
        root_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=None, name="资料库")
        child_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=root_folder.id, name="封面")
        leaf_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=child_folder.id, name="文章")

        breadcrumbs = build_folder_breadcrumbs(
            {
                root_folder.id: root_folder,
                child_folder.id: child_folder,
                leaf_folder.id: leaf_folder,
            },
            leaf_folder,
        )

        self.assertEqual([item.name for item in breadcrumbs], ["全部文件", "资料库", "封面", "文章"])
        self.assertIsNone(breadcrumbs[0].id)
        self.assertEqual(breadcrumbs[-1].id, leaf_folder.id)

    def test_完整路径会包含根目录与层级(self) -> None:
        user_id = uuid4()
        root_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=None, name="资料库")
        child_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=root_folder.id, name="封面")

        full_path = build_folder_full_path(
            {
                root_folder.id: root_folder,
                child_folder.id: child_folder,
            },
            child_folder,
        )

        self.assertEqual(full_path, "全部文件 / 资料库 / 封面")

    def test_压缩包路径支持目录与文件两种模式(self) -> None:
        self.assertEqual(build_archive_file_path(["资料库", "封面"], "cover.png"), "资料库/封面/cover.png")
        self.assertEqual(build_archive_file_path(["资料库", "封面"], ""), "资料库/封面")


class FileServiceAsyncTest(unittest.IsolatedAsyncioTestCase):
    """文件服务异步逻辑测试。"""

    async def test_跨目录搜索会返回完整路径(self) -> None:
        user = build_user()
        root_folder = FileFolder(
            id=uuid4(),
            user_id=user.id,
            parent_id=None,
            name="资料库",
            created_at=utc_dt(2026, 4, 7, 10, 0),
            updated_at=utc_dt(2026, 4, 7, 10, 0),
        )
        child_folder = FileFolder(
            id=uuid4(),
            user_id=user.id,
            parent_id=root_folder.id,
            name="封面素材",
            created_at=utc_dt(2026, 4, 7, 10, 5),
            updated_at=utc_dt(2026, 4, 7, 10, 5),
        )
        matched_file = File(
            id=uuid4(),
            user_id=user.id,
            folder_id=child_folder.id,
            purpose=FilePurpose.file,
            original_name="封面图.png",
            storage_key="user/files/cover.png",
            url="",
            size=1024,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 7, 11, 0),
        )
        db = AsyncMock()
        db.execute.return_value = build_scalars_result([matched_file])

        with patch("app.services.file_service.list_user_folders", AsyncMock(return_value=[root_folder, child_folder])):
            result = await search_resources(db, user, keyword="封面")

        self.assertEqual([folder.name for folder in result.folders], ["封面素材"])
        self.assertEqual(result.folders[0].path, "全部文件 / 资料库 / 封面素材")
        self.assertEqual([file.original_name for file in result.files], ["封面图.png"])
        self.assertEqual(result.files[0].path, "全部文件 / 资料库 / 封面素材")
        self.assertEqual(result.files[0].url, "/files/user/files/cover.png")

    async def test_打包下载会展开目录并处理重名路径(self) -> None:
        user = build_user()
        first_root = FileFolder(
            id=uuid4(),
            user_id=user.id,
            parent_id=None,
            name="素材",
            created_at=utc_dt(2026, 4, 7, 9, 0),
            updated_at=utc_dt(2026, 4, 7, 9, 0),
        )
        second_root = FileFolder(
            id=uuid4(),
            user_id=user.id,
            parent_id=None,
            name="素材",
            created_at=utc_dt(2026, 4, 7, 9, 10),
            updated_at=utc_dt(2026, 4, 7, 9, 10),
        )
        child_folder = FileFolder(
            id=uuid4(),
            user_id=user.id,
            parent_id=first_root.id,
            name="封面",
            created_at=utc_dt(2026, 4, 7, 9, 20),
            updated_at=utc_dt(2026, 4, 7, 9, 20),
        )
        selected_root_file = File(
            id=uuid4(),
            user_id=user.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="说明.txt",
            storage_key="storage/readme-1",
            url="",
            size=12,
            mime_type="text/plain",
            created_at=utc_dt(2026, 4, 7, 12, 0),
        )
        selected_root_file_same_name = File(
            id=uuid4(),
            user_id=user.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="说明.txt",
            storage_key="storage/readme-2",
            url="",
            size=18,
            mime_type="text/plain",
            created_at=utc_dt(2026, 4, 7, 12, 5),
        )
        nested_file = File(
            id=uuid4(),
            user_id=user.id,
            folder_id=child_folder.id,
            purpose=FilePurpose.file,
            original_name="cover.png",
            storage_key="storage/cover-1",
            url="",
            size=100,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 7, 12, 10),
        )
        second_root_file = File(
            id=uuid4(),
            user_id=user.id,
            folder_id=second_root.id,
            purpose=FilePurpose.file,
            original_name="cover.png",
            storage_key="storage/cover-2",
            url="",
            size=110,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 7, 12, 20),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result([selected_root_file, selected_root_file_same_name]),
            build_scalars_result([nested_file, second_root_file]),
        ]

        with (
            patch(
                "app.services.file_service.list_user_folders",
                AsyncMock(return_value=[first_root, second_root, child_folder]),
            ),
            patch(
                "app.services.file_service.fetch_object_bytes",
                side_effect=lambda storage_key: (f"payload:{storage_key}".encode(), "application/octet-stream"),
            ),
        ):
            archive_bytes = await build_archive_payload(
                db,
                user,
                folder_ids=[first_root.id, second_root.id],
                file_ids=[selected_root_file.id, selected_root_file_same_name.id],
            )

        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = sorted(archive.namelist())
            self.assertEqual(
                names,
                [
                    "素材 (2)/",
                    "素材 (2)/cover.png",
                    "素材/",
                    "素材/封面/",
                    "素材/封面/cover.png",
                    "说明 (2).txt",
                    "说明.txt",
                ],
            )
            self.assertEqual(archive.read("说明.txt"), b"payload:storage/readme-1")
            self.assertEqual(archive.read("说明 (2).txt"), b"payload:storage/readme-2")
            self.assertEqual(archive.read("素材/封面/cover.png"), b"payload:storage/cover-1")
            self.assertEqual(archive.read("素材 (2)/cover.png"), b"payload:storage/cover-2")


if __name__ == "__main__":
    unittest.main()
