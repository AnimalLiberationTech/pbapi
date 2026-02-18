from typing import Generic, TypeVar, Optional, Union, List, Dict, Any

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """API response wrapper for all endpoints"""

    status_code: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Human-readable message about the response")
    data: Optional[Union[T, List[T], Dict[str, Any]]] = Field(
        None, description="Response data (object, list, or dict)"
    )
