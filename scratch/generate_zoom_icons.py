import os
import urllib.request
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QImage, QColor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QSize

ICONS = {
    "zoom_in.png": "magnify-plus-outline",
    "zoom_out.png": "magnify-minus-outline",
    "zoom_reset.png": "backup-restore"  # or 'magnify-scan' if backup-restore doesn't fit? Actually backup-restore is already used for restore backup.
}

# Let's try some alternatives for reset if we don't like backup-restore
# Maybe "magnify-scan" or "magnify-remove-outline"
ICONS["zoom_reset.png"] = "focus-field" 

# Actually 'magnify-plus' and 'magnify-minus' are definitely in MDI.
# Let's try to just download them, if it fails it will print.

BASE_URL = "https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/master/svg/{}.svg"

def download_and_generate():
    app = QApplication([])
    out_dir = r"e:\Proyectos\GitHub\pw_MultiScriptEditor\multi_script_editor\icons"
    os.makedirs(out_dir, exist_ok=True)
    
    # Let's define alternatives in case the primary one fails (404)
    alternatives = {
        "magnify-plus-outline": "magnify-plus",
        "magnify-minus-outline": "magnify-minus",
        "focus-field": "line-scan",
        "line-scan": "crop-free"
    }

    for filename, mdi_name in ICONS.items():
        while True:
            url = BASE_URL.format(mdi_name)
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    svg_data = response.read()
                    
                    svg_text = svg_data.decode('utf-8')
                    if '<path' in svg_text:
                        svg_text = svg_text.replace('<path', '<path fill="#FFFFFF"')
                    else:
                        svg_text = svg_text.replace('<svg', '<svg fill="#FFFFFF"')
                    
                    svg_data = svg_text.encode('utf-8')
                    renderer = QSvgRenderer(svg_data)
                    
                    img = QImage(64, 64, QImage.Format_ARGB32)
                    img.fill(Qt.transparent)
                    
                    painter = QPainter(img)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setOpacity(0.5)
                    renderer.render(painter)
                    painter.end()
                    
                    out_path = os.path.join(out_dir, filename)
                    img.save(out_path, "PNG")
                    print(f"Generated: {filename} from {mdi_name}")
                    break
            except urllib.error.HTTPError as e:
                if e.code == 404 and mdi_name in alternatives:
                    print(f"404 for {mdi_name}, trying alternative: {alternatives[mdi_name]}")
                    mdi_name = alternatives[mdi_name]
                else:
                    print(f"Failed to generate {filename} ({mdi_name}): {e}")
                    break
            except Exception as e:
                print(f"Failed to generate {filename}: {e}")
                break

if __name__ == '__main__':
    download_and_generate()
