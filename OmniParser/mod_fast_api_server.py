from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel
import torch
from PIL import Image
import base64
import io
import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from util.utils import get_som_labeled_img, check_ocr_box, get_caption_model_processor, get_yolo_model

# Create FastAPI app
app = FastAPI(title="OmniParser Server", description="Screenshot labeling server for REVA")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables to store models
som_model = None
caption_model_processor = None
device = 'cuda' if torch.cuda.is_available() else 'cpu'


class ImageRequest(BaseModel):
    base64_image: str  # Changed to match what apis.py sends


@app.on_event("startup")
async def load_models():
    """Initialize models when the FastAPI server starts"""
    global som_model, caption_model_processor, device

    logger.info(f"Loading models on device: {device}")

    try:
        # Load SOM model
        model_path = os.path.join(os.path.dirname(__file__), 'weights/icon_detect/model.pt')
        if os.path.exists(model_path):
            som_model = get_yolo_model(model_path)
            som_model.to(device)
            logger.success("SOM model loaded")
        else:
            logger.warning(f"SOM model not found at {model_path}")

        # Load caption model
        caption_model_processor = get_caption_model_processor(
            model_name="florence2",
            model_name_or_path="microsoft/Florence-2-base",
            device=device
        )
        logger.success("Caption model loaded")
    except Exception as e:
        logger.error(f"Error loading models: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "models_loaded": som_model is not None and caption_model_processor is not None,
        "device": device
    }


async def process_image(encoded_image: str):
    """Process a single image using the pre-loaded models"""
    image = Image.open(io.BytesIO(base64.b64decode(encoded_image)))

    # Create temporary directory for image
    image_dir = os.path.join(os.path.dirname(__file__), "image_dir")
    os.makedirs(image_dir, exist_ok=True)
    image_path = os.path.join(image_dir, "screenshot.png")
    image.save(image_path)

    # Configure processing parameters
    box_overlay_ratio = max(image.size) / 3200
    draw_bbox_config = {
        'text_scale': 0.8 * box_overlay_ratio,
        'text_thickness': max(int(2 * box_overlay_ratio), 1),
        'text_padding': max(int(3 * box_overlay_ratio), 1),
        'thickness': max(int(3 * box_overlay_ratio), 1),
    }
    BOX_TRESHOLD = 0.05

    # Process OCR
    ocr_bbox_rslt, _ = check_ocr_box(
        image_path,
        display_img=False,
        output_bb_format='xyxy',
        goal_filtering=None,
        easyocr_args={'paragraph': False, 'text_threshold': 0.8},
        use_paddleocr=False
    )
    text, ocr_bbox = ocr_bbox_rslt

    # Process image with pre-loaded models
    dino_labled_img, _, parsed_content_list = get_som_labeled_img(
        image_path,
        som_model,
        BOX_TRESHOLD=BOX_TRESHOLD,
        output_coord_in_ratio=True,
        ocr_bbox=ocr_bbox,
        draw_bbox_config=draw_bbox_config,
        caption_model_processor=caption_model_processor,
        ocr_text=text,
        use_local_semantics=True,
        iou_threshold=0.7,
        scale_img=False,
        batch_size=128
    )

    # Cleanup
    if os.path.exists(image_path):
        os.remove(image_path)

    return dino_labled_img, parsed_content_list


@app.post("/label/")
async def generate(request: ImageRequest):
    """Handle incoming requests using pre-loaded models"""
    try:
        if som_model is None or caption_model_processor is None:
            raise HTTPException(
                status_code=503,
                detail="Models are not loaded yet. Please try again in a few moments."
            )

        logger.info("Processing request...")
        begin = time.time()
        dino_labled_img, parsed_content_list = await process_image(request.base64_image)
        logger.success("Request processed successfully")
        end = time.time()
        logger.success(f"Process completed in: {end - begin:.2f} seconds")

        return JSONResponse({
            "labeled_image": dino_labled_img,  # Changed to match what apis.py expects
            "parsed_content_list": parsed_content_list,  # Changed to match what apis.py expects
            "coordinates": parsed_content_list  # Keep for backwards compatibility
        })
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)