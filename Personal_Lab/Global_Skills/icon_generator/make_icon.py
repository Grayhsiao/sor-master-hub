import os
import subprocess
from PIL import Image

def create_icns(source_png, icon_name):
    iconset_dir = f"{icon_name}.iconset"
    if not os.path.exists(iconset_dir):
        os.makedirs(iconset_dir)
        
    img = Image.open(source_png)
    
    # macOS icon sizes
    sizes = [16, 32, 128, 256, 512]
    
    for size in sizes:
        # Normal size
        resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
        resized_img.save(os.path.join(iconset_dir, f"icon_{size}x{size}.png"))
        
        # Retina size (@2x)
        d_size = size * 2
        resized_img_2x = img.resize((d_size, d_size), Image.Resampling.LANCZOS)
        resized_img_2x.save(os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png"))
        
    print(f"Generated iconset at {iconset_dir}")
    
    # Convert to icns using native tool
    subprocess.run(["iconutil", "-c", "icns", iconset_dir])
    print(f"Created {icon_name}.icns")

if __name__ == "__main__":
    if os.path.exists("andy_doll.png"):
        create_icns("andy_doll.png", "andy_doll")
    else:
        print("andy_doll.png not found")
