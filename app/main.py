from fastapi import FastAPI, Form, UploadFile

from handlers.validate_image import validate_image_handler
from handlers.mark_pdf import mark_pdf_handler

app = FastAPI()


@app.post("/validate-image")
async def validate_image(file: UploadFile):
    return await validate_image_handler(file)


@app.post("/mark-pdf")
async def mark_pdf(file: UploadFile, box_id: int = Form(...)):
    return await mark_pdf_handler(file, box_id)
