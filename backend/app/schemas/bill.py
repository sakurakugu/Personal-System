"""账单相关 Schema。"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _normalize_text(value: str | None) -> str | None:
    """清理可选文本字段。"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_required_name(value: str) -> str:
    """清理必填名称字段。"""
    normalized = value.strip()
    if not normalized:
        raise ValueError("名称不能为空")
    return normalized


class BillAccountCreate(BaseModel):
    """创建账单账户请求。"""

    name: str = Field(max_length=60)
    type: str
    initial_balance_cent: int = Field(default=0, ge=-999999999999, le=999999999999)
    note: str | None = Field(default=None, max_length=300)

    _normalize_name = field_validator("name")(_normalize_required_name)
    _normalize_note = field_validator("note")(_normalize_text)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        """校验账户类型。"""
        allowed = {"cash", "debit_card", "credit_card", "wechat", "alipay", "other"}
        if value not in allowed:
            raise ValueError("账户类型不合法")
        return value


class BillAccountUpdate(BaseModel):
    """更新账单账户请求。"""

    name: str | None = Field(default=None, max_length=60)
    type: str | None = None
    initial_balance_cent: int | None = Field(default=None, ge=-999999999999, le=999999999999)
    note: str | None = Field(default=None, max_length=300)

    _normalize_name = field_validator("name")(_normalize_text)
    _normalize_note = field_validator("note")(_normalize_text)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        """校验账户类型。"""
        if value is None:
            return None
        allowed = {"cash", "debit_card", "credit_card", "wechat", "alipay", "other"}
        if value not in allowed:
            raise ValueError("账户类型不合法")
        return value


class BillAccountSimpleRead(BaseModel):
    """账单账户简要响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    type: str


class BillAccountRead(BillAccountSimpleRead):
    """账单账户响应。"""

    initial_balance_cent: int
    current_balance_cent: int
    note: str | None = None
    created_at: datetime
    updated_at: datetime


class BillCategoryCreate(BaseModel):
    """创建账单分类请求。"""

    type: str
    name: str = Field(max_length=40)
    color: str = Field(default="#94a3b8", max_length=20)
    icon: str = Field(default="folder", max_length=40)
    sort_order: int = Field(default=0, ge=-999, le=999)

    _normalize_name = field_validator("name")(_normalize_required_name)
    _normalize_color = field_validator("color")(_normalize_required_name)
    _normalize_icon = field_validator("icon")(_normalize_required_name)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        """校验分类类型。"""
        allowed = {"expense", "income"}
        if value not in allowed:
            raise ValueError("分类类型不合法")
        return value


class BillCategoryUpdate(BaseModel):
    """更新账单分类请求。"""

    type: str | None = None
    name: str | None = Field(default=None, max_length=40)
    color: str | None = Field(default=None, max_length=20)
    icon: str | None = Field(default=None, max_length=40)
    sort_order: int | None = Field(default=None, ge=-999, le=999)

    _normalize_name = field_validator("name")(_normalize_text)
    _normalize_color = field_validator("color")(_normalize_text)
    _normalize_icon = field_validator("icon")(_normalize_text)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        """校验分类类型。"""
        if value is None:
            return None
        allowed = {"expense", "income"}
        if value not in allowed:
            raise ValueError("分类类型不合法")
        return value


class BillCategorySimpleRead(BaseModel):
    """账单分类简要响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    name: str
    color: str
    icon: str


class BillCategoryRead(BillCategorySimpleRead):
    """账单分类响应。"""

    sort_order: int
    created_at: datetime
    updated_at: datetime


class BillTemplateCreate(BaseModel):
    """创建固定账单模板请求。"""

    title: str = Field(max_length=80)
    type: str
    account_id: UUID
    target_account_id: UUID | None = None
    category_id: UUID | None = None
    amount_cent: int = Field(gt=0, le=999999999999)
    merchant: str | None = Field(default=None, max_length=120)
    note: str | None = None
    day_of_month: int = Field(ge=1, le=31)
    is_active: bool = True

    _normalize_title = field_validator("title")(_normalize_required_name)
    _normalize_merchant = field_validator("merchant")(_normalize_text)
    _normalize_note = field_validator("note")(_normalize_text)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        """校验模板类型。"""
        allowed = {"expense", "income", "transfer"}
        if value not in allowed:
            raise ValueError("模板类型不合法")
        return value


class BillTemplateUpdate(BaseModel):
    """更新固定账单模板请求。"""

    title: str | None = Field(default=None, max_length=80)
    type: str | None = None
    account_id: UUID | None = None
    target_account_id: UUID | None = None
    category_id: UUID | None = None
    amount_cent: int | None = Field(default=None, gt=0, le=999999999999)
    merchant: str | None = Field(default=None, max_length=120)
    note: str | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    is_active: bool | None = None

    _normalize_title = field_validator("title")(_normalize_text)
    _normalize_merchant = field_validator("merchant")(_normalize_text)
    _normalize_note = field_validator("note")(_normalize_text)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        """校验模板类型。"""
        if value is None:
            return None
        allowed = {"expense", "income", "transfer"}
        if value not in allowed:
            raise ValueError("模板类型不合法")
        return value


class BillTemplateRead(BaseModel):
    """固定账单模板响应。"""

    id: UUID
    title: str
    type: str
    amount_cent: int
    merchant: str | None = None
    note: str | None = None
    day_of_month: int
    is_active: bool
    account: BillAccountSimpleRead
    target_account: BillAccountSimpleRead | None = None
    category: BillCategorySimpleRead | None = None
    created_at: datetime
    updated_at: datetime


class BillTemplateGenerateResultRead(BaseModel):
    """固定账单生成结果响应。"""

    month: str
    created_count: int
    skipped_count: int


class BillRecordCreate(BaseModel):
    """创建账单流水请求。"""

    type: str
    account_id: UUID
    target_account_id: UUID | None = None
    category_id: UUID | None = None
    amount_cent: int = Field(gt=0, le=999999999999)
    merchant: str | None = Field(default=None, max_length=120)
    note: str | None = None
    occurred_at: datetime

    _normalize_merchant = field_validator("merchant")(_normalize_text)
    _normalize_note = field_validator("note")(_normalize_text)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        """校验流水类型。"""
        allowed = {"expense", "income", "transfer"}
        if value not in allowed:
            raise ValueError("流水类型不合法")
        return value


class BillRecordUpdate(BaseModel):
    """更新账单流水请求。"""

    type: str | None = None
    account_id: UUID | None = None
    target_account_id: UUID | None = None
    category_id: UUID | None = None
    amount_cent: int | None = Field(default=None, gt=0, le=999999999999)
    merchant: str | None = Field(default=None, max_length=120)
    note: str | None = None
    occurred_at: datetime | None = None

    _normalize_merchant = field_validator("merchant")(_normalize_text)
    _normalize_note = field_validator("note")(_normalize_text)

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str | None) -> str | None:
        """校验流水类型。"""
        if value is None:
            return None
        allowed = {"expense", "income", "transfer"}
        if value not in allowed:
            raise ValueError("流水类型不合法")
        return value


class BillRecordRead(BaseModel):
    """账单流水响应。"""

    id: UUID
    template_id: UUID | None = None
    template_title: str | None = None
    type: str
    amount_cent: int
    merchant: str | None = None
    note: str | None = None
    occurred_at: datetime
    account: BillAccountSimpleRead
    target_account: BillAccountSimpleRead | None = None
    category: BillCategorySimpleRead | None = None
    created_at: datetime
    updated_at: datetime


class BillSummaryDailyTotalRead(BaseModel):
    """账单日汇总响应。"""

    date: date
    income_cent: int
    expense_cent: int


class BillSummaryCategoryRead(BaseModel):
    """账单分类汇总响应。"""

    category_id: UUID
    type: str
    name: str
    color: str
    amount_cent: int
    record_count: int


class BillMonthSummaryRead(BaseModel):
    """账单月汇总响应。"""

    month: str
    income_cent: int
    expense_cent: int
    net_cent: int
    record_count: int
    daily_totals: list[BillSummaryDailyTotalRead] = []
    category_totals: list[BillSummaryCategoryRead] = []
