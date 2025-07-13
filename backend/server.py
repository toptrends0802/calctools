from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import io
from PyPDF2 import PdfWriter, PdfReader
from PIL import Image
import tempfile
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Mobile Tools Hub API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class PDFOperation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str  # 'merge' or 'split'
    file_count: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "completed"

class ImageOperation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str  # 'crop', 'rotate', 'filter'
    filter_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "completed"

class ConversionOperation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str  # 'length', 'weight', 'temperature'
    from_unit: str
    to_unit: str
    from_value: float
    to_value: float
    country: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Basic API routes
@api_router.get("/")
async def root():
    return {"message": "Mobile Tools Hub API - Ready to process your files!"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# PDF Processing Routes
@api_router.post("/pdf/merge")
async def merge_pdfs(files: List[UploadFile] = File(...)):
    """Merge multiple PDF files into one"""
    try:
        if len(files) < 2:
            raise HTTPException(status_code=400, detail="At least 2 PDF files required for merging")
        
        # Create a PDF writer object
        pdf_writer = PdfWriter()
        
        # Process each uploaded file
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF")
            
            # Read the PDF file
            pdf_content = await file.read()
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            
            # Add all pages to the writer
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
        
        # Create output stream
        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)
        
        # Log the operation
        operation = PDFOperation(
            operation_type="merge",
            file_count=len(files)
        )
        await db.pdf_operations.insert_one(operation.dict())
        
        # Return the merged PDF
        return StreamingResponse(
            io.BytesIO(output_stream.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=merged_document.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Error merging PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error merging PDFs: {str(e)}")

@api_router.post("/pdf/split/{page_number}")
async def split_pdf(page_number: int, file: UploadFile = File(...)):
    """Split a PDF and return a specific page"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read the PDF file
        pdf_content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        
        # Check if page number is valid
        if page_number < 1 or page_number > len(pdf_reader.pages):
            raise HTTPException(
                status_code=400, 
                detail=f"Page number {page_number} is invalid. PDF has {len(pdf_reader.pages)} pages."
            )
        
        # Create a new PDF with just the specified page
        pdf_writer = PdfWriter()
        pdf_writer.add_page(pdf_reader.pages[page_number - 1])  # Convert to 0-based index
        
        # Create output stream
        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)
        
        # Log the operation
        operation = PDFOperation(
            operation_type="split",
            file_count=1
        )
        await db.pdf_operations.insert_one(operation.dict())
        
        # Return the page as PDF
        return StreamingResponse(
            io.BytesIO(output_stream.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=page_{page_number}.pdf"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error splitting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error splitting PDF: {str(e)}")

@api_router.get("/pdf/info")
async def get_pdf_info(file: UploadFile = File(...)):
    """Get information about a PDF file"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Read the PDF file
        pdf_content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        
        return {
            "filename": file.filename,
            "page_count": len(pdf_reader.pages),
            "file_size": len(pdf_content),
            "metadata": pdf_reader.metadata if pdf_reader.metadata else {}
        }
        
    except Exception as e:
        logger.error(f"Error getting PDF info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting PDF info: {str(e)}")

# Image Processing Routes
@api_router.post("/image/rotate")
async def rotate_image(rotation: int, file: UploadFile = File(...)):
    """Rotate an image by specified degrees"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process the image
        image_content = await file.read()
        image = Image.open(io.BytesIO(image_content))
        
        # Rotate the image
        rotated_image = image.rotate(-rotation, expand=True)  # Negative for clockwise rotation
        
        # Save to output stream
        output_stream = io.BytesIO()
        image_format = image.format or 'PNG'
        rotated_image.save(output_stream, format=image_format)
        output_stream.seek(0)
        
        # Log the operation
        operation = ImageOperation(
            operation_type="rotate"
        )
        await db.image_operations.insert_one(operation.dict())
        
        # Return the rotated image
        return StreamingResponse(
            io.BytesIO(output_stream.read()),
            media_type=f"image/{image_format.lower()}",
            headers={"Content-Disposition": f"attachment; filename=rotated_{file.filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error rotating image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error rotating image: {str(e)}")

@api_router.post("/image/resize")
async def resize_image(width: int, height: int, file: UploadFile = File(...)):
    """Resize an image to specified dimensions"""
    try:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and process the image
        image_content = await file.read()
        image = Image.open(io.BytesIO(image_content))
        
        # Resize the image
        resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save to output stream
        output_stream = io.BytesIO()
        image_format = image.format or 'PNG'
        resized_image.save(output_stream, format=image_format)
        output_stream.seek(0)
        
        # Log the operation
        operation = ImageOperation(
            operation_type="resize"
        )
        await db.image_operations.insert_one(operation.dict())
        
        # Return the resized image
        return StreamingResponse(
            io.BytesIO(output_stream.read()),
            media_type=f"image/{image_format.lower()}",
            headers={"Content-Disposition": f"attachment; filename=resized_{file.filename}"}
        )
        
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resizing image: {str(e)}")

# Unit Conversion Routes
@api_router.post("/convert", response_model=ConversionOperation)
async def convert_units(
    category: str,
    from_unit: str,
    to_unit: str,
    value: float,
    country: str = "US"
):
    """Convert between different units"""
    try:
        # Define conversion factors (base unit: meter for length, kilogram for weight, celsius for temperature)
        conversions = {
            "length": {
                "US": {"meter": 1, "feet": 3.28084, "inch": 39.3701, "yard": 1.09361, "mile": 0.000621371},
                "IN": {"meter": 1, "feet": 3.28084, "inch": 39.3701, "centimeter": 100, "kilometer": 0.001},
                "CA": {"meter": 1, "feet": 3.28084, "inch": 39.3701, "kilometer": 0.001, "centimeter": 100},
                "AU": {"meter": 1, "feet": 3.28084, "inch": 39.3701, "mile": 0.000621371, "kilometer": 0.001}
            },
            "weight": {
                "US": {"kilogram": 1, "pound": 2.20462, "ounce": 35.274, "ton": 0.001},
                "IN": {"kilogram": 1, "pound": 2.20462, "gram": 1000, "tonne": 0.001},
                "CA": {"kilogram": 1, "pound": 2.20462, "gram": 1000, "tonne": 0.001},
                "AU": {"kilogram": 1, "pound": 2.20462, "gram": 1000, "tonne": 0.001}
            }
        }
        
        # Special handling for temperature
        if category == "temperature":
            if from_unit == "fahrenheit" and to_unit == "celsius":
                converted_value = (value - 32) * 5/9
            elif from_unit == "celsius" and to_unit == "fahrenheit":
                converted_value = value * 9/5 + 32
            elif from_unit == "celsius" and to_unit == "kelvin":
                converted_value = value + 273.15
            elif from_unit == "kelvin" and to_unit == "celsius":
                converted_value = value - 273.15
            elif from_unit == "fahrenheit" and to_unit == "kelvin":
                converted_value = (value - 32) * 5/9 + 273.15
            elif from_unit == "kelvin" and to_unit == "fahrenheit":
                converted_value = (value - 273.15) * 9/5 + 32
            else:
                converted_value = value  # Same unit
        else:
            if category not in conversions or country not in conversions[category]:
                raise HTTPException(status_code=400, detail="Invalid category or country")
            
            unit_set = conversions[category][country]
            
            if from_unit not in unit_set or to_unit not in unit_set:
                raise HTTPException(status_code=400, detail="Invalid units for this category/country")
            
            # Convert to base unit, then to target unit
            base_value = value / unit_set[from_unit]
            converted_value = base_value * unit_set[to_unit]
        
        # Create and save the conversion record
        conversion_operation = ConversionOperation(
            category=category,
            from_unit=from_unit,
            to_unit=to_unit,
            from_value=value,
            to_value=converted_value,
            country=country
        )
        
        await db.conversion_operations.insert_one(conversion_operation.dict())
        
        return conversion_operation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting units: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error converting units: {str(e)}")

# Analytics Routes
@api_router.get("/analytics/pdf")
async def get_pdf_analytics():
    """Get PDF operation analytics"""
    try:
        total_operations = await db.pdf_operations.count_documents({})
        merge_operations = await db.pdf_operations.count_documents({"operation_type": "merge"})
        split_operations = await db.pdf_operations.count_documents({"operation_type": "split"})
        
        return {
            "total_operations": total_operations,
            "merge_operations": merge_operations,
            "split_operations": split_operations
        }
    except Exception as e:
        logger.error(f"Error getting PDF analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting analytics")

@api_router.get("/analytics/image")
async def get_image_analytics():
    """Get image operation analytics"""
    try:
        total_operations = await db.image_operations.count_documents({})
        rotate_operations = await db.image_operations.count_documents({"operation_type": "rotate"})
        resize_operations = await db.image_operations.count_documents({"operation_type": "resize"})
        
        return {
            "total_operations": total_operations,
            "rotate_operations": rotate_operations,
            "resize_operations": resize_operations
        }
    except Exception as e:
        logger.error(f"Error getting image analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting analytics")

@api_router.get("/analytics/conversions")
async def get_conversion_analytics():
    """Get unit conversion analytics"""
    try:
        total_conversions = await db.conversion_operations.count_documents({})
        length_conversions = await db.conversion_operations.count_documents({"category": "length"})
        weight_conversions = await db.conversion_operations.count_documents({"category": "weight"})
        temp_conversions = await db.conversion_operations.count_documents({"category": "temperature"})
        
        return {
            "total_conversions": total_conversions,
            "length_conversions": length_conversions,
            "weight_conversions": weight_conversions,
            "temperature_conversions": temp_conversions
        }
    except Exception as e:
        logger.error(f"Error getting conversion analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting analytics")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)