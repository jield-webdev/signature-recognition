from fastapi import FastAPI, UploadFile

from handlers.validate_image import validate_image_handler
from handlers.aruco_signature import aruco_signature_handler

app = FastAPI()


@app.post("/validate-image")
async def validate_image(file: UploadFile):
    return await validate_image_handler(file)


@app.post("/aruco-signature")
async def aruco_signature(file: UploadFile):
    return await aruco_signature_handler(file)
