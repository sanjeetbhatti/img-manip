from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import mysql.connector
from PIL import Image
import io
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

OUTPUT_DIR = "output_folder"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI()

executor = ThreadPoolExecutor(max_workers=4)

# MySQL database configuration
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def get_db_connection():
    """
    Establish a connection to the MySQL database with retry logic.
    
    Attempts to connect to the database up to 5 times with 2-second delays
    between attempts. This handles cases where the database might not be
    ready immediately after container startup.
    
    Returns:
        mysql.connector.connection.MySQLConnection: Database connection object
        
    Raises:
        Exception: If connection fails after 5 attempts
    """
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
    """
    Initialize the database by creating the images table if it doesn't exist.
    
    Creates a table to store metadata about processed images including
    filename and download URL. This function is called at application startup.
    """
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

def store_in_db_sync(filename, url):
    """
    Store image metadata in the database synchronously.
    
    Args:
        filename (str): The name of the uploaded file
        url (str): The download URL for the compressed image
    """
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

async def store_in_db(filename, url):
    """
    Store image metadata in the database asynchronously.
    
    Wraps the synchronous database operation in a ThreadPoolExecutor
    to prevent blocking the event loop.
    
    Args:
        filename (str): The name of the uploaded file
        url (str): The download URL for the compressed image
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, store_in_db_sync, filename, url)

def get_images_sync():
    """
    Retrieve all processed images from the database synchronously.
    
    Returns:
        list: List of tuples containing (filename, url) pairs
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor()
    try:
        query = "SELECT filename, url FROM images"
        cursor.execute(query)
        results = cursor.fetchall()
        return [(filename, url) for filename, url in results]
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    finally:
        cursor.close()
        db_conn.close()

async def get_images_async():
    """
    Retrieve all processed images from the database asynchronously.
    
    Wraps the synchronous database operation in a ThreadPoolExecutor
    to prevent blocking the event loop.
    
    Returns:
        list: List of tuples containing (filename, url) pairs
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_images_sync)

def save_file_sync(output_path, file_data):
    """
    Save file data to disk synchronously.
    
    Args:
        output_path (str): The path where the file should be saved
        file_data (bytes): The file data to write
    """
    with open(output_path, "wb") as out_file:
        out_file.write(file_data)

async def save_file(output_path, file_data):
    """
    Save file data to disk asynchronously.
    
    Wraps the synchronous file operation in a ThreadPoolExecutor
    to prevent blocking the event loop.
    
    Args:
        output_path (str): The path where the file should be saved
        file_data (bytes): The file data to write
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, save_file_sync, output_path, file_data)

initialize_db()

# Setup static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Serve the main application page.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        HTMLResponse: Rendered index.html template
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload/")
async def upload_image(uploaded_file: UploadFile = File(...), quality=85):
    """
    Upload and compress an image file.
    
    Accepts an image file (PNG or JPEG) and compresses it based on the
    specified quality setting. Returns file statistics and download URL.
    
    Args:
        uploaded_file (UploadFile): The image file to process
        quality (int): Compression quality (1-100, default 85)
        
    Returns:
        dict: JSON response containing:
            - filename: Original filename
            - url: Download URL for compressed image
            - message: Success message
            - stats: File statistics (size, compression ratio, etc.)
            
    Raises:
        HTTPException: 400 if file format is unsupported or file is invalid
    """
    try:
        # Get original file size
        original_size = len(uploaded_file.file.read())
        uploaded_file.file.seek(0)  
        
        # Read the image file
        img = Image.open(uploaded_file.file)

        # Get the file format of the uploaded image
        content_type = uploaded_file.content_type
        if content_type == "image/jpeg":
            format = "JPEG"
        elif content_type == "image/png":
            format = "PNG"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format.")

        # Compress the image based on the quality
        output_io = io.BytesIO()
        img.save(output_io, format=format, optimize=True, quality=int(quality))
        output_io.seek(0)
        file_data = output_io.getvalue()
        
        # Calculate compressed file size
        compressed_size = len(file_data)
        
        # Calculate compression ratio
        compression_ratio = round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0

        # Save the compressed image
        output_path = os.path.join(OUTPUT_DIR, uploaded_file.filename)
        await save_file(output_path, file_data)

        # Store the image download link in the database
        url = f"http://127.0.0.1:8000/download/{uploaded_file.filename}"
        await store_in_db(uploaded_file.filename, url)

        return {
            "filename": uploaded_file.filename,
            "url": url,
            "message": "Image compressed successfully!",
            "stats": {
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "format": format,
                "quality": int(quality)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail="Unsupported or invalid file. Please upload a valid PNG or JPEG image.")

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    """
    Download a compressed image file.
    
    Args:
        file_name (str): The name of the file to download
        
    Returns:
        FileResponse: The file for download
        
    Raises:
        HTTPException: 404 if file is not found
    """
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

@app.get("/images")
async def get_images():
    """
    Retrieve all processed images from the database.
    
    Returns:
        dict: JSON response containing list of (filename, url) pairs
    """
    results = await get_images_async()
    return {"images": results}