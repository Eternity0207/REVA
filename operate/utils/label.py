from PIL import Image, ImageDraw

def annotate_boxes(image_path, boxes, output_path):
    """Annotate image with bounding boxes"""
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    for i, box in enumerate(boxes):
        bbox = box.get("bbox", [])
        if len(bbox) >= 2:
            x1, y1 = int(bbox[0][0]), int(bbox[0][1])
            x2, y2 = int(bbox[2][0]), int(bbox[2][1])
            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
    image.save(output_path)
    return output_path
