import os

from fastapi import FastAPI, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import opencv_config
from handlers.validate_image import validate_image_handler
from handlers.mark_pdf import mark_pdf_handler
from limits import MAX_REQUEST_BYTES
from request_size_limit import RequestSizeLimitMiddleware

app = FastAPI()
app.add_middleware(RequestSizeLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)

allow_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", include_in_schema=False)
def healthz():
    return {"status": "ok"}


@app.post("/validate-image")
async def validate_image(file: UploadFile):
    return await validate_image_handler(file)


@app.post("/mark-pdf")
async def mark_pdf(file: UploadFile, boxes: str = Form(...)):
    return await mark_pdf_handler(file, boxes)
