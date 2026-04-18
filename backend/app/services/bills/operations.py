"""账单操作兼容入口。"""

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
]
