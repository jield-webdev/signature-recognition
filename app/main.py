from fastapi import FastAPI, UploadFile

from handlers.validate_image import validate_image_handler

app = FastAPI()


@app.post("/validate-file")
async def validate_file(file: UploadFile):
    return await validate_image_handler(file)
