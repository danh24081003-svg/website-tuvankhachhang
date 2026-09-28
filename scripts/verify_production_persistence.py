import io
import json
import urllib.request
import urllib.parse
from PIL import Image

PROD_URL = "https://website-tuvankhachhang.vercel.app"

def create_test_image(color="green") -> bytes:
    img = Image.new("RGB", (300, 300), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def run_prod_check():
    print(f"Checking live production persistent image serving at: {PROD_URL}")
    
    # Check /api/site/images
    req = urllib.request.urlopen(f"{PROD_URL}/api/site/images")
    images = json.loads(req.read().decode("utf-8"))
    print(f"Site images count: {len(images)}")
    assert "hero_main" in images, "hero_main missing!"
    print(f"hero_main current URL: {images['hero_main']}")

    print("Live production endpoint check: PASS ✅")

if __name__ == "__main__":
    run_prod_check()
