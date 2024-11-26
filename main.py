from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import mysql.connector
from PIL import Image
import io
import os
import time

OUTPUT_DIR = "output_folder"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI()

# MySQL database configuration
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_db_connection():
    for i in range(5):
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Attempt {i + 1}: Error connecting to MySQL: {err}")
            time.sleep(2)
    raise Exception("Could not connect to MySQL after several attempts.")

def initialize_db():
    db_conn = get_db_connection()
    cursor = db_conn.cursor()

    create_images_table_query = """
    CREATE TABLE IF NOT EXISTS images (
        id INT AUTO_INCREMENT PRIMARY KEY,
        filename VARCHAR(255),
        url TEXT
    );
    """
    try:
        cursor.execute(create_images_table_query)

        if cursor.lastrowid > 0:
            print("The images table has been created.")
        else:
            print("The images table already exists in the database.")

        db_conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        db_conn.close()

def store_in_db(filename, url):
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    query = "INSERT INTO images (filename, url) VALUES (%s, %s)"
    try:
        cursor.execute(query, (filename, url))
        db_conn.commit()
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        db_conn.close()

initialize_db()

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

    # Store the image download link in the database
    url = f"http://127.0.0.1:8000/download/{uploaded_file.filename}"
    store_in_db(uploaded_file.filename, url)

    return {
        "filename": uploaded_file.filename,
        "url": url,
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