from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    query: str
    page: int = 1
    page_size: int = Field(10, ge=1, le=50)
