"""文件服务测试。"""

from __future__ import annotations

import io
import unittest
import zipfile
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from urllib.parse import urlsplit
from uuid import uuid4

from PIL import Image

from app.modules.articles.models import 文章, 文章图片, 文章状态
from app.modules.files.archive import 构建归档文件路径
from app.modules.files.explorer import 搜索资源
from app.modules.files.folders import (
    构建文件夹面包屑,
    构建文件夹完整路径,
    构建文件夹树节点,
)
from app.modules.files.models import File, FileFolder, FilePurpose
from app.modules.files.operations import 构建归档载荷, 重命名文件
from app.modules.moments.models import 动态, 动态图片
from app.modules.files.upload_preparation import 按内容类型规范化文件名, 准备上传载荷
from app.modules.users.models import 用户, 用户角色


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


def build_user() -> 用户:
    """构造测试用户。"""
    return 用户(
        id=uuid4(),
        username="tester",
        email="tester@example.com",
        password_hash="hash",
        role=用户角色.user,
    )


def build_article(user: 用户, *, title: str = "测试文章") -> 文章:
    """构造测试文章。"""
    return 文章(
        id=uuid4(),
        title=title,
        slug="test-article",
        content="content",
        excerpt=None,
        cover_url=None,
        status=文章状态.private,
        view_count=0,
        like_count=0,
        author_id=user.id,
        category_id=None,
        is_deleted=False,
        deleted_at=None,
        published_at=None,
        created_at=utc_dt(2026, 4, 7, 9, 0),
        last_edited_at=utc_dt(2026, 4, 7, 9, 0),
        updated_at=utc_dt(2026, 4, 7, 9, 0),
    )


def build_scalars_result(records: list[object]) -> SimpleNamespace:
    """构造支持 scalars().all() 的查询结果桩。"""
    return SimpleNamespace(
        scalars=lambda: SimpleNamespace(
            all=lambda: records,
        )
    )


def build_moment(user: 用户, *, title: str | None = "测试动态") -> 动态:
    """构造测试动态。"""
    return 动态(
        id=uuid4(),
        title=title,
        content="content",
        is_published=False,
        view_count=0,
        like_count=0,
        user_id=user.id,
        is_deleted=False,
        deleted_at=None,
        published_at=None,
        created_at=utc_dt(2026, 5, 4, 9, 0),
        updated_at=utc_dt(2026, 5, 4, 9, 0),
    )


class 文件服务测试(unittest.TestCase):
    """文件服务纯逻辑测试。"""

    def test_静态位图会转换为_avif(self) -> None:
        prepared = 准备上传载荷(
            "cover.png",
            "image/png",
            create_png_bytes(),
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "cover.avif")
        self.assertEqual(prepared.storage_name, "cover.avif")
        self.assertEqual(prepared.content_type, "image/avif")
        self.assertNotEqual(prepared.content[:16], create_png_bytes()[:16])

        with Image.open(io.BytesIO(prepared.content)) as converted:
            self.assertEqual(converted.format, "AVIF")
            self.assertEqual(converted.size, (8, 8))

    def test_svg_保持原格式(self) -> None:
        svg_content = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"></svg>'

        prepared = 准备上传载荷(
            "vector.svg",
            "image/svg+xml",
            svg_content,
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "vector.svg")
        self.assertEqual(prepared.storage_name, "vector.svg")
        self.assertEqual(prepared.content_type, "image/svg+xml")
        self.assertEqual(prepared.content, svg_content)

    def test_文章动图_gif_会转换为_avif(self) -> None:
        gif_content = create_animated_gif_bytes()

        prepared = 准备上传载荷(
            "motion.gif",
            "image/gif",
            gif_content,
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "motion.avif")
        self.assertEqual(prepared.storage_name, "motion.avif")
        self.assertEqual(prepared.content_type, "image/avif")
        self.assertNotEqual(prepared.content, gif_content)

        with Image.open(io.BytesIO(prepared.content)) as converted:
            self.assertEqual(converted.format, "AVIF")
            self.assertTrue(getattr(converted, "is_animated", False))
            self.assertEqual(getattr(converted, "n_frames", 1), 2)

    def test_普通上传图片保持原格式(self) -> None:
        png_content = create_png_bytes()

        prepared = 准备上传载荷(
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
        prepared = 准备上传载荷(
            "",
            "image/png",
            create_png_bytes(),
            compress_static_images=True,
        )

        self.assertEqual(prepared.original_name, "image.avif")
        self.assertEqual(prepared.storage_name, "image.avif")
        self.assertEqual(prepared.content_type, "image/avif")

    def test_avif_文件名会与真实格式保持一致(self) -> None:
        self.assertEqual(按内容类型规范化文件名("cover.png", "image/avif"), "cover.avif")
        self.assertEqual(按内容类型规范化文件名("cover", "image/avif"), "cover.avif")
        self.assertEqual(按内容类型规范化文件名("", "image/avif"), "image.avif")

    def test_文件夹树会按层级构造(self) -> None:
        user_id = uuid4()
        root_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=None, name="资料库")
        child_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=root_folder.id, name="封面")
        leaf_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=child_folder.id, name="文章")

        tree = 构建文件夹树节点([root_folder, child_folder, leaf_folder])

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0].name, "资料库")
        self.assertEqual(len(tree[0].children), 1)
        self.assertEqual(tree[0].children[0].name, "封面")
        self.assertEqual(len(tree[0].children[0].children), 1)
        self.assertEqual(tree[0].children[0].children[0].name, "文章")

    def test_导航栏会包含根目录与当前路径(self) -> None:
        user_id = uuid4()
        root_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=None, name="资料库")
        child_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=root_folder.id, name="封面")
        leaf_folder = FileFolder(id=uuid4(), user_id=user_id, parent_id=child_folder.id, name="文章")

        breadcrumbs = 构建文件夹面包屑(
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

        full_path = 构建文件夹完整路径(
            {
                root_folder.id: root_folder,
                child_folder.id: child_folder,
            },
            child_folder,
        )

        self.assertEqual(full_path, "全部文件 / 资料库 / 封面")

    def test_压缩包路径支持目录与文件两种模式(self) -> None:
        self.assertEqual(构建归档文件路径(["资料库", "封面"], "cover.png"), "资料库/封面/cover.png")
        self.assertEqual(构建归档文件路径(["资料库", "封面"], ""), "资料库/封面")


class 文件服务异步测试(unittest.IsolatedAsyncioTestCase):
    """文件服务异步逻辑测试。"""

    async def test_重命名普通_avif_文件会自动纠正后缀(self) -> None:
        user = build_user()
        record = File(
            id=uuid4(),
            user_id=user.id,
            folder_id=None,
            purpose=FilePurpose.file,
            original_name="封面.avif",
            storage_key="user/files/cover.avif",
            size=1024,
            mime_type="image/avif",
            created_at=utc_dt(2026, 4, 8, 9, 0),
        )
        db = AsyncMock()
        db.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: record)

        result = await 重命名文件(db, user, file_id=record.id, original_name="封面图.png")

        self.assertEqual(record.original_name, "封面图.avif")
        self.assertEqual(result.original_name, "封面图.avif")
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(record)

    async def test_重命名文章_avif_图片会自动纠正后缀(self) -> None:
        user = build_user()
        article = build_article(user, title="封面设计记录")
        article_image = 文章图片(
            id=uuid4(),
            article_id=article.id,
            original_name="封面插图.avif",
            storage_key="user/articles/cover.avif",
            size=2048,
            mime_type="image/avif",
            created_at=utc_dt(2026, 4, 8, 9, 30),
            article=article,
        )
        db = AsyncMock()
        db.execute.side_effect = [
            SimpleNamespace(scalar_one_or_none=lambda: None),
            SimpleNamespace(scalar_one_or_none=lambda: article_image),
        ]

        result = await 重命名文件(db, user, file_id=article_image.id, original_name="封面插图.jpg")

        self.assertEqual(article_image.original_name, "封面插图.avif")
        self.assertEqual(result.original_name, "封面插图.avif")
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(article_image)

    async def test_重命名动态_avif_图片会自动纠正后缀(self) -> None:
        user = build_user()
        moment = build_moment(user, title="封面碎片")
        moment_image = 动态图片(
            id=uuid4(),
            moment_id=moment.id,
            original_name="封面插图.avif",
            storage_key="user/moments/cover.avif",
            size=2048,
            mime_type="image/avif",
            sort_order=0,
            created_at=utc_dt(2026, 5, 4, 9, 30),
            moment=moment,
        )
        db = AsyncMock()
        db.execute.side_effect = [
            SimpleNamespace(scalar_one_or_none=lambda: None),
            SimpleNamespace(scalar_one_or_none=lambda: None),
            SimpleNamespace(scalar_one_or_none=lambda: moment_image),
        ]

        result = await 重命名文件(db, user, file_id=moment_image.id, original_name="封面插图.jpg")

        self.assertEqual(moment_image.original_name, "封面插图.avif")
        self.assertEqual(result.original_name, "封面插图.avif")
        self.assertEqual(result.purpose, FilePurpose.moment_image)
        self.assertEqual(result.moment_id, moment.id)
        self.assertEqual(result.moment_title, "封面碎片")
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(moment_image)

    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
    async def test_跨目录搜索会返回完整路径(self, _mock_time) -> None:
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
            size=1024,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 7, 11, 0),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result([matched_file]),
            build_scalars_result([]),
            build_scalars_result([]),
        ]

        with patch("app.modules.files.explorer.列出用户文件夹", AsyncMock(return_value=[root_folder, child_folder])):
            result = await 搜索资源(db, user, keyword="封面")

        self.assertEqual([folder.name for folder in result.folders], ["封面素材"])
        self.assertEqual(result.folders[0].path, "全部文件 / 资料库 / 封面素材")
        self.assertEqual([file.original_name for file in result.files], ["封面图.png"])
        self.assertEqual(result.files[0].path, "全部文件 / 资料库 / 封面素材")
        self.assertEqual(urlsplit(result.files[0].url).path, "/files/user/files/cover.png")
        self.assertIn("signature=", result.files[0].url)
        self.assertIsNotNone(result.files[0].thumbnail_url)
        assert result.files[0].thumbnail_url is not None
        self.assertEqual(urlsplit(result.files[0].thumbnail_url).path, "/files/user/files/cover.png")
        self.assertIn("thumbnail_width=144", result.files[0].thumbnail_url)
        self.assertNotIn("signature=", result.files[0].thumbnail_url)
        self.assertEqual(result.files[0].purpose, FilePurpose.file)

    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
    async def test_跨目录搜索会包含文章图片(self, _mock_time) -> None:
        user = build_user()
        article = build_article(user, title="封面设计记录")
        article_image = 文章图片(
            id=uuid4(),
            article_id=article.id,
            original_name="封面插图.png",
            storage_key="user/articles/cover.png",
            size=2048,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 7, 11, 30),
            article=article,
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result([]),
            build_scalars_result([article_image]),
            build_scalars_result([]),
        ]

        with patch("app.modules.files.explorer.列出用户文件夹", AsyncMock(return_value=[])):
            result = await 搜索资源(db, user, keyword="封面")

        self.assertEqual([file.original_name for file in result.files], ["封面插图.png"])
        self.assertEqual(result.files[0].purpose, FilePurpose.article_image)
        self.assertEqual(result.files[0].article_id, article.id)
        self.assertEqual(result.files[0].article_title, "封面设计记录")
        self.assertEqual(result.files[0].path, "全部文件 / 文章图片 / 封面设计记录")
        self.assertEqual(urlsplit(result.files[0].url).path, "/files/user/articles/cover.png")
        self.assertIn("signature=", result.files[0].url)
        self.assertIsNotNone(result.files[0].thumbnail_url)
        assert result.files[0].thumbnail_url is not None
        self.assertNotIn("signature=", result.files[0].thumbnail_url)

    @patch("app.shared.storage.file_url.time.time", return_value=1_700_000_000)
    async def test_跨目录搜索会包含动态图片(self, _mock_time) -> None:
        user = build_user()
        moment = build_moment(user, title="旅行碎片")
        moment_image = 动态图片(
            id=uuid4(),
            moment_id=moment.id,
            original_name="封面插图.png",
            storage_key="user/moments/cover.png",
            size=2048,
            mime_type="image/png",
            sort_order=0,
            created_at=utc_dt(2026, 5, 4, 10, 0),
            moment=moment,
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result([]),
            build_scalars_result([]),
            build_scalars_result([moment_image]),
        ]

        with patch("app.modules.files.explorer.列出用户文件夹", AsyncMock(return_value=[])):
            result = await 搜索资源(db, user, keyword="旅行")

        self.assertEqual([file.original_name for file in result.files], ["封面插图.png"])
        self.assertEqual(result.files[0].purpose, FilePurpose.moment_image)
        self.assertEqual(result.files[0].moment_id, moment.id)
        self.assertEqual(result.files[0].moment_title, "旅行碎片")
        self.assertEqual(result.files[0].path, "全部文件 / 动态图片 / 旅行碎片")
        self.assertEqual(urlsplit(result.files[0].url).path, "/files/user/moments/cover.png")
        self.assertIn("signature=", result.files[0].url)
        self.assertIsNotNone(result.files[0].thumbnail_url)
        assert result.files[0].thumbnail_url is not None
        self.assertNotIn("signature=", result.files[0].thumbnail_url)

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
            size=110,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 7, 12, 20),
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result([selected_root_file, selected_root_file_same_name]),
            build_scalars_result([]),
            build_scalars_result([]),
            build_scalars_result([nested_file, second_root_file]),
        ]

        with (
            patch(
                "app.modules.files.operations.列出用户文件夹",
                AsyncMock(return_value=[first_root, second_root, child_folder]),
            ),
            patch(
                "app.modules.files.archive.获取对象字节",
                side_effect=lambda storage_key: (f"payload:{storage_key}".encode(), "application/octet-stream"),
            ),
        ):
            archive_bytes = await 构建归档载荷(
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

    async def test_打包下载会包含文章图片目录(self) -> None:
        user = build_user()
        article = build_article(user, title="旅行手记")
        article_image = 文章图片(
            id=uuid4(),
            article_id=article.id,
            original_name="photo.png",
            storage_key="storage/article-photo",
            size=88,
            mime_type="image/png",
            created_at=utc_dt(2026, 4, 7, 12, 40),
            article=article,
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result([]),
            build_scalars_result([article_image]),
            build_scalars_result([]),
        ]

        with (
            patch("app.modules.files.operations.列出用户文件夹", AsyncMock(return_value=[])),
            patch(
                "app.modules.files.archive.获取对象字节",
                side_effect=lambda storage_key: (f"payload:{storage_key}".encode(), "application/octet-stream"),
            ),
        ):
            archive_bytes = await 构建归档载荷(
                db,
                user,
                folder_ids=[],
                file_ids=[article_image.id],
            )

        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = sorted(archive.namelist())
            self.assertEqual(names, ["文章图片/", "文章图片/旅行手记/", "文章图片/旅行手记/photo.png"])
            self.assertEqual(archive.read("文章图片/旅行手记/photo.png"), b"payload:storage/article-photo")

    async def test_打包下载会包含动态图片目录(self) -> None:
        user = build_user()
        moment = build_moment(user, title="旅行碎片")
        moment_image = 动态图片(
            id=uuid4(),
            moment_id=moment.id,
            original_name="photo.png",
            storage_key="storage/moment-photo",
            size=88,
            mime_type="image/png",
            sort_order=0,
            created_at=utc_dt(2026, 5, 4, 12, 40),
            moment=moment,
        )
        db = AsyncMock()
        db.execute.side_effect = [
            build_scalars_result([]),
            build_scalars_result([]),
            build_scalars_result([moment_image]),
        ]

        with (
            patch("app.modules.files.operations.列出用户文件夹", AsyncMock(return_value=[])),
            patch(
                "app.modules.files.archive.获取对象字节",
                side_effect=lambda storage_key: (f"payload:{storage_key}".encode(), "application/octet-stream"),
            ),
        ):
            archive_bytes = await 构建归档载荷(
                db,
                user,
                folder_ids=[],
                file_ids=[moment_image.id],
            )

        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = sorted(archive.namelist())
            self.assertEqual(names, ["动态图片/", "动态图片/旅行碎片/", "动态图片/旅行碎片/photo.png"])
            self.assertEqual(archive.read("动态图片/旅行碎片/photo.png"), b"payload:storage/moment-photo")


if __name__ == "__main__":
    unittest.main()
