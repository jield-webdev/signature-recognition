from fastapi import FastAPI, UploadFile

from handlers.validate_file import validate_file_handler

app = FastAPI()


@app.post("/validate-file")
async def validate_file(file: UploadFile):
    return await validate_file_handler(file)
