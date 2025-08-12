from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil
import os
import uuid
import json
from ultralytics import YOLO

# Load YOLO model (pre-trained COCO dataset)
model = YOLO("yolov8n.pt")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Create upload folder
os.makedirs("uploads", exist_ok=True)

# Load price list from JSON file
def load_prices():
    with open("prices.json", "r") as f:
        return json.load(f)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # Save uploaded image
    filename = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join("uploads", filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Reload prices each request (so updates take effect immediately)
    PRICE_LIST = load_prices()

    # Run YOLO object detection
    results = model(file_path)

    detected_items = []
    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id].lower()

            # Get price from PRICE_LIST or set 0 if unknown
            price = PRICE_LIST.get(label, 0)

            detected_items.append({"name": label, "price": price})

    total_price = sum(item["price"] for item in detected_items)

    return {
        "file": filename,
        "detected_items": detected_items,
        "total_price": total_price
    }

