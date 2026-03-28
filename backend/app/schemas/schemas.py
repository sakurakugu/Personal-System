"""Pydantic v2 模式定义。

此模块定义了所有 API 的请求和响应数据模式（Schema），
用于数据验证、序列化和文档生成。

模式按功能模块组织：认证、用户、分类、标签、文章、评论、
待办事项、文件、统计、友链、公告、动态等。
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


已注销后缀 = "（已注销）"


def _validate_email_no_plus(value: EmailStr | None) -> EmailStr | None:
    """
    验证邮箱不包含加号（防止使用别名邮箱）。

    Args:
        value: 邮箱地址

    Returns:
        EmailStr | None: 验证后的邮箱

    Raises:
        ValueError: 邮箱包含加号
    """
    if value is None:
        return value
    if "+" in str(value):
        raise ValueError("邮箱不能包含加号")
    return value


def _validate_username(value: str) -> str:
    """
    规范化并校验用户名。
    Args:
        value: 原始用户名
    Returns:
        str: 规范化后的用户名
    Raises:
        ValueError: 用户名非法
    """
    normalized = value.strip()
    if not normalized:
        raise ValueError("用户名不能为空")
    if 已注销后缀 in normalized:
        raise ValueError(f"用户名不能包含保留标记 {已注销后缀}")
    return normalized


# ═══════════════════════════════════════════════════════════
#  认证
# ═══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    """登录请求。"""
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """规范化用户名。"""
        return _validate_username(value)


class RegisterRequest(BaseModel):
    """注册请求。"""
    username: str = Field(min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """规范化用户名。"""
        return _validate_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> EmailStr:
        """验证邮箱格式。"""
        return _validate_email_no_plus(value) or value


class TokenResponse(BaseModel):
    """令牌响应，包含 access_token 和 refresh_token。"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """刷新令牌请求。"""
    refresh_token: str


# ═══════════════════════════════════════════════════════════
#  用户
# ═══════════════════════════════════════════════════════════

class UserRead(BaseModel):
    """用户信息公开数据。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str
    nickname: str | None = None
    email: str
    role: str
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """用户资料更新请求。"""
    username: str | None = Field(default=None, min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    bio: str | None = None
    avatar_url: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        """规范化用户名。"""
        if value is None:
            return None
        return _validate_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr | None) -> EmailStr | None:
        """验证邮箱格式。"""
        return _validate_email_no_plus(value)


class UserCreateByAdmin(BaseModel):
    """管理员创建用户请求。"""
    username: str = Field(min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = "user"
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool = True

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """规范化用户名。"""
        return _validate_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr) -> EmailStr:
        """验证邮箱格式。"""
        return _validate_email_no_plus(value) or value


class UserAdminUpdate(BaseModel):
    """管理员更新用户请求。"""
    username: str | None = Field(default=None, min_length=2, max_length=50)
    nickname: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    role: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        """规范化用户名。"""
        if value is None:
            return None
        return _validate_username(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: EmailStr | None) -> EmailStr | None:
        """验证邮箱格式。"""
        return _validate_email_no_plus(value)


class UserPasswordReset(BaseModel):
    """管理员重置用户密码请求。"""
    password: str = Field(min_length=6, max_length=128)


class UserChangePassword(BaseModel):
    """用户修改自己密码请求。"""
    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


# ═══════════════════════════════════════════════════════════
#  分类
# ═══════════════════════════════════════════════════════════

class CategoryCreate(BaseModel):
    """创建分类请求。"""
    name: str = Field(max_length=100)
    description: str | None = None


class CategoryRead(BaseModel):
    """分类数据响应。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    description: str | None = None
    created_at: datetime


# ═══════════════════════════════════════════════════════════
#  标签
# ═══════════════════════════════════════════════════════════

class TagCreate(BaseModel):
    """创建标签请求。"""
    name: str = Field(max_length=60)


class TagRead(BaseModel):
    """标签数据响应。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    slug: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════
#  文章
# ═══════════════════════════════════════════════════════════

class ArticleCreate(BaseModel):
    """创建文章请求。"""
    title: str = Field(max_length=300)
    content: str = ""
    excerpt: str | None = None
    cover_url: str | None = None
    status: str = "draft"
    category_id: UUID | None = None
    tag_ids: list[UUID] = []


class ArticleUpdate(BaseModel):
    """更新文章请求。"""
    title: str | None = None
    content: str | None = None
    excerpt: str | None = None
    cover_url: str | None = None
    status: str | None = None
    category_id: UUID | None = None
    tag_ids: list[UUID] | None = None


class ArticleRead(BaseModel):
    """文章详情响应。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    slug: str
    content: str
    excerpt: str | None = None
    cover_url: str | None = None
    status: str
    view_count: int
    author: UserRead
    category: CategoryRead | None = None
    tags: list[TagRead] = []
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ArticleListItem(BaseModel):
    """文章列表项响应（不包含完整内容）。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    slug: str
    excerpt: str | None = None
    cover_url: str | None = None
    status: str
    view_count: int
    author: UserRead
    category: CategoryRead | None = None
    tags: list[TagRead] = []
    published_at: datetime | None = None
    created_at: datetime


class CommentPendingRead(BaseModel):
    """待审核评论响应，包含文章信息。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    article_id: UUID
    content: str
    guest_name: str | None = None
    created_at: datetime
    user: UserRead | None = None
    article: ArticleListItem | None = None


# ═══════════════════════════════════════════════════════════
#  评论
# ═══════════════════════════════════════════════════════════

class CommentCreate(BaseModel):
    """创建评论请求。"""
    article_id: UUID
    content: str = Field(min_length=1)
    parent_id: UUID | None = None  # 回复的评论 ID
    guest_name: str | None = None  # 游客名称


class CommentReplyToUser(BaseModel):
    """评论回复目标用户信息。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str
    nickname: str | None = None
    guest_name: str | None = None


class CommentRead(BaseModel):
    """评论数据响应（支持嵌套回复）。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    article_id: UUID
    user_id: UUID | None = None
    guest_name: str | None = None
    parent_id: UUID | None = None
    content: str
    status: str
    like_count: int = 0  # 点赞数
    is_liked: bool = False  # 当前用户是否点赞（由接口动态设置）
    created_at: datetime
    user: UserRead | None = None
    reply_to_user: CommentReplyToUser | None = None  # 回复目标用户信息
    replies: list["CommentRead"] = []


class CommentModerate(BaseModel):
    """评论审核请求。"""
    status: str  # approved / rejected


class CommentLikeRead(BaseModel):
    """评论点赞响应。"""
    comment_id: str
    user_id: UUID | None = None
    is_liked: bool
    like_count: int


# ═══════════════════════════════════════════════════════════
#  待办事项
# ═══════════════════════════════════════════════════════════

class TodoCreate(BaseModel):
    """创建待办事项请求。"""
    title: str = Field(max_length=300)
    description: str | None = None
    # 优先级双维度 (0-100)
    importance: int = Field(default=33, ge=0, le=100)  # 重要性
    urgency: int = Field(default=33, ge=0, le=100)     # 紧急性
    # 时间范围
    start_date: datetime | None = None   # 开始时间
    end_date: datetime | None = None     # 截止时间
    # 标记
    is_pinned: bool = False              # 是否置顶
    # 标签
    tags: list[str] | None = None        # 标签列表
    # 循环设置
    recurrence_type: str = "none"        # 循环类型
    recurrence_interval: int = Field(default=1, ge=1, le=365)   # 循环间隔
    recurrence_count: int = Field(default=0, ge=-1, le=999)     # 循环次数，-1=无限，0=不循环
    # 每循环完成次数
    times_per_interval: int = Field(default=1, ge=1, le=999)    # 每循环间隔需要完成的次数

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | str | None) -> list[str] | None:
        """统一标签格式为去重后的标签数组。"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("，", ",").split(",")
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags)) or None

    @field_validator("recurrence_type")
    @classmethod
    def validate_recurrence_type(cls, value: str) -> str:
        """校验循环类型。"""
        allowed = {"none", "daily", "weekly", "monthly", "yearly", "workday", "weekend", "holiday", "custom"}
        if value not in allowed:
            raise ValueError("循环类型不合法")
        return value

    @model_validator(mode="after")
    def validate_recurrence_fields(self) -> "TodoCreate":
        """校验循环相关字段组合是否合法。"""
        if self.recurrence_type == "none":
            if self.recurrence_count != 0:
                raise ValueError("不循环任务的循环次数必须为 0")
            if self.times_per_interval != 1:
                raise ValueError("不循环任务的每周期完成次数必须为 1")
        return self


class TodoUpdate(BaseModel):
    """更新待办事项请求。"""
    title: str | None = None
    description: str | None = None
    status: str | None = None
    importance: int | None = Field(default=None, ge=0, le=100)
    urgency: int | None = Field(default=None, ge=0, le=100)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_pinned: bool | None = None
    is_deleted: bool | None = None       # 用于软删除/恢复
    tags: list[str] | None = None
    recurrence_type: str | None = None
    recurrence_interval: int | None = Field(default=None, ge=1, le=365)
    recurrence_count: int | None = Field(default=None, ge=-1, le=999)
    # 每循环完成次数
    times_per_interval: int | None = Field(default=None, ge=1, le=999)  # 每循环间隔需要完成的次数
    interval_progress: int | None = Field(default=None, ge=0, le=999)   # 当前循环间隔已完成的次数

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | str | None) -> list[str] | None:
        """统一标签格式为去重后的标签数组。"""
        if value is None:
            return None
        if isinstance(value, str):
            value = value.replace("，", ",").split(",")
        tags = [tag.strip() for tag in value if tag.strip()]
        return list(dict.fromkeys(tags)) or None

    @field_validator("recurrence_type")
    @classmethod
    def validate_recurrence_type(cls, value: str | None) -> str | None:
        """校验循环类型。"""
        if value is None:
            return None
        allowed = {"none", "daily", "weekly", "monthly", "yearly", "workday", "weekend", "holiday", "custom"}
        if value not in allowed:
            raise ValueError("循环类型不合法")
        return value

    @model_validator(mode="after")
    def validate_progress_fields(self) -> "TodoUpdate":
        """校验更新时的循环进度字段。"""
        if self.interval_progress is not None and self.times_per_interval is not None:
            if self.interval_progress > self.times_per_interval:
                raise ValueError("当前周期进度不能大于每周期完成次数")
        if self.recurrence_type == "none":
            if self.recurrence_count not in (None, 0):
                raise ValueError("不循环任务的循环次数必须为 0")
            if self.times_per_interval not in (None, 1):
                raise ValueError("不循环任务的每周期完成次数必须为 1")
        return self


class TodoRead(BaseModel):
    """待办事项数据响应。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    description: str | None = None
    status: str
    # 优先级双维度
    importance: int
    urgency: int
    # 时间范围
    start_date: datetime | None = None
    end_date: datetime | None = None
    # 标记
    is_pinned: bool
    # 软删除
    is_deleted: bool
    deleted_at: datetime | None = None
    # 标签
    tags: list[str] | None = None
    # 循环设置
    recurrence_type: str = "none"
    recurrence_interval: int = 1
    recurrence_count: int = 0
    # 每循环完成次数
    times_per_interval: int = 1
    interval_progress: int = 0
    progress_reset_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TodoTagRead(BaseModel):
    """待办标签响应。"""
    name: str
    count: int


# ═══════════════════════════════════════════════════════════
#  文件
# ═══════════════════════════════════════════════════════════

class FileRead(BaseModel):
    """文件数据响应。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    original_name: str
    url: str
    size: int
    mime_type: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════
#  统计 / 系统
# ═══════════════════════════════════════════════════════════

class DashboardStats(BaseModel):
    """用户仪表板统计数据响应。"""
    total_articles: int
    total_comments: int
    total_views: int
    total_todos: int
    recent_views: list[dict] = []  # [{date, count}, ...]


class TodoCompletionHistoryItemRead(BaseModel):
    """待办完成历史明细项。"""
    todo_id: UUID
    title: str
    completed_count: int


class TodoCompletionHistoryDayRead(BaseModel):
    """待办完成历史单日汇总。"""
    date: date
    completed_count: int
    items: list[TodoCompletionHistoryItemRead] = []


class TodoCompletionHistoryRead(BaseModel):
    """待办完成历史区间响应。"""
    start_date: date
    end_date: date
    max_completed_count: int
    total_completed_count: int
    days: list[TodoCompletionHistoryDayRead]


class HolidayCalendarYearRead(BaseModel):
    """节假日日历年份响应。"""
    year: int
    supported: bool
    holiday_dates: list[date]
    workday_dates: list[date]


class SystemStatus(BaseModel):
    """系统状态响应（CPU、内存、磁盘）。"""
    cpu_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    uptime_seconds: float


class HealthComponentStatus(BaseModel):
    """健康检查组件状态。"""
    status: str
    detail: str | None = None


class HealthCheckRead(BaseModel):
    """健康检查响应。"""
    status: str
    checked_at: datetime
    database: HealthComponentStatus
    redis: HealthComponentStatus


class SystemSettingsRead(BaseModel):
    """系统设置数据响应。"""
    comments_enabled: bool
    comments_stealth: bool
    comments_min_role: str = "guest"  # guest / user / admin / super_admin
    register_enabled: bool = True


class SystemSettingsUpdate(BaseModel):
    """系统设置更新请求。"""
    comments_enabled: bool | None = None
    comments_stealth: bool | None = None
    comments_min_role: str | None = None  # guest / user / admin / super_admin
    register_enabled: bool | None = None


# ═══════════════════════════════════════════════════════════
#  友链
# ═══════════════════════════════════════════════════════════

class LinkCreate(BaseModel):
    """创建友链请求（管理员）。"""
    name: str = Field(max_length=100)
    url: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=100)


class LinkUpdate(BaseModel):
    """更新友链请求。"""
    name: str | None = Field(default=None, max_length=100)
    url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    status: str | None = None  # pending, approved, rejected


class LinkRead(BaseModel):
    """友链数据响应（完整）。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    url: str
    description: str | None = None
    logo_url: str | None = None
    status: str
    is_auto_exchange: bool
    contact_email: str | None = None
    contact_name: str | None = None
    created_at: datetime
    updated_at: datetime


class LinkPublicRead(BaseModel):
    """公开可见的友链信息。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    url: str
    description: str | None = None
    logo_url: str | None = None


class LinkExchangeRequest(BaseModel):
    """友链交换申请请求。"""
    name: str = Field(max_length=100)
    url: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=200)
    logo_url: str | None = Field(default=None, max_length=500)
    contact_email: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=100)
    my_site_url: str = Field(max_length=500)  # 对方网站 URL，用于自动检测


# ═══════════════════════════════════════════════════════════
#  公告
# ═══════════════════════════════════════════════════════════

class AnnouncementCreate(BaseModel):
    """创建公告请求。"""
    title: str = Field(max_length=200)
    content: str
    is_active: bool = True


class AnnouncementUpdate(BaseModel):
    """更新公告请求。"""
    title: str | None = Field(default=None, max_length=200)
    content: str | None = None
    is_active: bool | None = None


class AnnouncementRead(BaseModel):
    """公告数据响应（完整）。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    content: str
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class AnnouncementPublicRead(BaseModel):
    """公开可见的公告信息。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    content: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════
#  动态（Moments）
# ═══════════════════════════════════════════════════════════

class MomentCreate(BaseModel):
    """发布动态请求。"""
    title: str | None = Field(default=None, max_length=100)
    content: str = Field(max_length=1000)


class MomentDraftSave(BaseModel):
    """保存草稿请求。"""
    title: str | None = Field(default=None, max_length=100)
    content: str = Field(max_length=1000)


class MomentRead(BaseModel):
    """动态数据响应（完整）。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str | None = None
    content: str
    is_published: bool
    user_id: UUID
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MomentPublicRead(BaseModel):
    """公开的动态信息（博客端展示）。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str | None = None
    content: str
    published_at: datetime
    user: "UserRead"


class MomentDraftRead(BaseModel):
    """草稿信息响应。"""
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str | None = None
    content: str
    updated_at: datetime


# ═══════════════════════════════════════════════════════════
#  分页响应
# ═══════════════════════════════════════════════════════════

class PaginatedResponse(BaseModel):
    """通用分页响应。"""
    items: list
    total: int
    page: int
    page_size: int
    pages: int
