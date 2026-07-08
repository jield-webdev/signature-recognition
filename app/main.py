from fastapi import FastAPI, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from handlers.validate_image import validate_image_handler
from handlers.mark_pdf import mark_pdf_handler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/validate-image")
async def validate_image(file: UploadFile):
    return await validate_image_handler(file)


@app.post("/mark-pdf")
async def mark_pdf(file: UploadFile, boxes: str = Form(...)):
    return await mark_pdf_handler(file, boxes)
