"""评论服务测试。"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from uuid import UUID

from app.models.comment import Comment, CommentStatus
from app.modules.users.models import User, UserRole
from app.modules.comments.service import build_comment_tree
from app.utils.uuid import generate_uuid7


def utc_dt(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """构造 UTC 时间。"""
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def build_user(username: str) -> User:
    """构造测试用户。"""
    now = utc_dt(2026, 3, 28, 12, 0)
    return User(
        id=generate_uuid7(),
        username=username,
        nickname=f"{username}-昵称",
        email=f"{username}@example.com",
        password_hash="hashed",
        role=UserRole.user,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def build_comment(
    *,
    article_id: UUID,
    created_at: datetime,
    user: User | None,
    guest_name: str | None,
    parent: Comment | None = None,
) -> Comment:
    """构造测试评论。"""
    comment = Comment(
        id=generate_uuid7(),
        article_id=article_id,
        user_id=user.id if user else None,
        guest_name=guest_name,
        parent_id=parent.id if parent else None,
        content="测试评论",
        status=CommentStatus.approved,
        like_count=0,
        created_at=created_at,
    )
    comment.user = user
    comment.parent = parent
    return comment


class CommentServiceTest(unittest.TestCase):
    """评论树组装测试。"""

    def test_会按父子关系构建嵌套评论树(self) -> None:
        article_id = generate_uuid7()
        author = build_user("author")
        replier = build_user("replier")
        root = build_comment(
            article_id=article_id,
            created_at=utc_dt(2026, 3, 28, 9, 0),
            user=author,
            guest_name=None,
        )
        reply = build_comment(
            article_id=article_id,
            created_at=utc_dt(2026, 3, 28, 10, 0),
            user=None,
            guest_name="游客甲",
            parent=root,
        )
        nested_reply = build_comment(
            article_id=article_id,
            created_at=utc_dt(2026, 3, 28, 11, 0),
            user=replier,
            guest_name=None,
            parent=reply,
        )

        comment_tree = build_comment_tree([root, reply, nested_reply], {reply.id, nested_reply.id})

        self.assertEqual(len(comment_tree), 1)
        self.assertEqual(comment_tree[0].id, root.id)
        self.assertFalse(comment_tree[0].is_liked)
        self.assertEqual(len(comment_tree[0].replies), 1)

        first_reply = comment_tree[0].replies[0]
        self.assertEqual(first_reply.id, reply.id)
        self.assertTrue(first_reply.is_liked)
        self.assertEqual(first_reply.guest_name, "游客甲")
        self.assertIsNone(first_reply.user)
        assert first_reply.reply_to_user is not None
        self.assertEqual(first_reply.reply_to_user.username, author.username)

        second_reply = first_reply.replies[0]
        self.assertEqual(second_reply.id, nested_reply.id)
        self.assertTrue(second_reply.is_liked)
        assert second_reply.reply_to_user is not None
        self.assertEqual(second_reply.reply_to_user.guest_name, "游客甲")
        assert second_reply.user is not None
        self.assertEqual(second_reply.user.username, replier.username)


if __name__ == "__main__":
    unittest.main()
