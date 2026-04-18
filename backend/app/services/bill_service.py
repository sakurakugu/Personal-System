"""账单领域服务聚合导出。"""

from __future__ import annotations

from app.modules.bills.common import (
    build_month_summary,
    calculate_account_record_deltas,
    ensure_default_bill_setup,
    resolve_template_occurred_at,
)
from app.modules.bills.operations import (
    create_bill_account,
    create_bill_category,
    create_bill_record,
    create_bill_template,
    delete_bill_account,
    delete_bill_category,
    delete_bill_record,
    delete_bill_template,
    update_bill_account,
    update_bill_category,
    update_bill_record,
    update_bill_template,
)
from app.modules.bills.queries import (
    generate_bill_templates_for_month,
    get_bill_month_summary,
    list_bill_accounts,
    list_bill_categories,
    list_bill_records,
    list_bill_templates,
)

_build_month_summary = build_month_summary
_calculate_account_record_deltas = calculate_account_record_deltas
_resolve_template_occurred_at = resolve_template_occurred_at

__all__ = [
    "create_bill_account",
    "create_bill_category",
    "create_bill_record",
    "create_bill_template",
    "delete_bill_account",
    "delete_bill_category",
    "delete_bill_record",
    "delete_bill_template",
    "update_bill_account",
    "update_bill_category",
    "update_bill_record",
    "update_bill_template",
    "generate_bill_templates_for_month",
    "get_bill_month_summary",
    "list_bill_accounts",
    "list_bill_categories",
    "list_bill_records",
    "list_bill_templates",
    "_build_month_summary",
    "_calculate_account_record_deltas",
    "_resolve_template_occurred_at",
    "ensure_default_bill_setup",
]
