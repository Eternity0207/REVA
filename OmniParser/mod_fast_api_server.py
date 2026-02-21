"""OmniParser Server"""
import base64
from io import BytesIO
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image

app = FastAPI(title="OmniParser")

class ImageRequest(BaseModel):
    base64_image: str

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/label/")
async def label(request: ImageRequest):
    try:
        img_data = base64.b64decode(request.base64_image)
        img = Image.open(BytesIO(img_data))

        # TODO: YOLO + Florence-2 detection

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        labeled_b64 = base64.b64encode(buffer.getvalue()).decode()

        return JSONResponse({
            "labeled_image": labeled_b64,
            "parsed_content_list": []
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    print("OmniParser: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
