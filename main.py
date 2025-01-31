from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image
import io
import os

OUTPUT_DIR = "output_folder"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI()

# Setup static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_image(uploaded_file: UploadFile = File(...), quality=85):
    # Read the image file
    img = Image.open(uploaded_file.file)

    # Get the file format of the uploaded image
    content_type = uploaded_file.content_type
    if content_type == "image/jpeg":
        format = "JPEG"
    elif content_type == "image/png":
        format = "PNG"
    else:
        return {"error": "Unsupported file format."}

    # Compress the image based on the quality
    output_io = io.BytesIO()
    img.save(output_io, format=format, optimize=True, quality=int(quality))
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