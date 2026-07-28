from typing import Annotated

from pydantic import BaseModel, Field, StrictInt

from layout.constants import MIN_BOX_HEIGHT, MIN_BOX_WIDTH
from boxes.box_id import MAX_BOX_ID


FiniteFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class BoxPlacement(BaseModel):
    """A signature box requested by the caller, in PDF points, top-left origin."""

    box_id: StrictInt = Field(ge=1, le=MAX_BOX_ID)
    page: StrictInt = Field(ge=0)
    x: FiniteFloat = Field(ge=0)
    y: FiniteFloat = Field(ge=0)
    width: FiniteFloat = Field(ge=MIN_BOX_WIDTH)
    height: FiniteFloat = Field(ge=MIN_BOX_HEIGHT)
