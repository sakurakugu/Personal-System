"""账单模型兼容入口。"""

from app.modules.bills.models import BillAccount, BillAccountType, BillCategory, BillCategoryType, BillRecord, BillRecordType, BillTemplate

__all__ = [
    "BillAccount",
    "BillAccountType",
    "BillCategory",
    "BillCategoryType",
    "BillRecord",
    "BillRecordType",
    "BillTemplate",
]
