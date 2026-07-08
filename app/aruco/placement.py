from pydantic import BaseModel, Field

from aruco.layout import MIN_BOX_HEIGHT, MIN_BOX_WIDTH
from aruco.utils import MAX_BOX_ID


class BoxPlacement(BaseModel):
    """A signature box requested by the caller, in PDF points, top-left origin."""

    box_id: int = Field(ge=1, le=MAX_BOX_ID)
    page: int = Field(ge=0)
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=MIN_BOX_WIDTH)
    height: float = Field(ge=MIN_BOX_HEIGHT)
