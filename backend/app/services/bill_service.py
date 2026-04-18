"""账单领域服务聚合导出。"""

from __future__ import annotations

from app.services.bills.operations import (
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
from app.services.bills.queries import (
    generate_bill_templates_for_month,
    get_bill_month_summary,
    list_bill_accounts,
    list_bill_categories,
    list_bill_records,
    list_bill_templates,
)

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
]
