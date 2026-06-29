from fastapi import HTTPException, UploadFile, status


async def validate_file_handler(file: UploadFile):
    if file.size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty.",
        )

    if file.content_type != "image/png":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type '{file.content_type}'. Expected 'image/png'.",
        )

    return {"mime_type": file.content_type}
