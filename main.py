from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image
import io
import os

OUTPUT_DIR = "output_folder"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to Image Manipulation Server"}

@app.post("/upload/")
async def upload_image(uploaded_file: UploadFile = File(...), quality=85):
    # Read the image file
    img = Image.open(uploaded_file.file)

    # Compress the image based on the quality
    output_io = io.BytesIO()
    img.save(output_io, format='JPEG', optimize=True, quality=int(quality))
    output_io.seek(0)

    # Save the compressed image
    output_path = os.path.join(OUTPUT_DIR, uploaded_file.filename)
    with open(output_path, "wb") as out_file:
        out_file.write(output_io.getvalue())

    return {
        "filename": uploaded_file.filename,
        "url": f"http://127.0.0.1:8000/download/{uploaded_file.filename}",
        "message": "Image compressed successfully!"
    }

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    file_path = os.path.join(OUTPUT_DIR, file_name)
    if os.path.exists(file_path):
        return FileResponse(
            path=file_path,
            media_type='application/octet-stream',
            filename=file_name,
            headers={"Content-Disposition": f"attachment; filename={file_name}"}
        )
    else:
        return {"error": "File not found"}, 404