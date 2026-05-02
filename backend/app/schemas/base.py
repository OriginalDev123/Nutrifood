from pydantic import BaseModel
from typing import List, Generic, TypeVar, Optional

# T đại diện cho một Type bất kỳ (FoodResponse, FoodLogResponse,...)
T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Cấu trúc phản hồi phân trang chuẩn hóa cho NutriAI"""
    items: List[T]        # Danh sách dữ liệu của trang hiện tại
    total: int            # Tổng số bản ghi thỏa mãn điều kiện (để tính tổng số trang)
    page: int             # Số trang hiện tại
    page_size: int        # Số bản ghi mỗi trang
    pages: int            # Tổng số trang (total / page_size)