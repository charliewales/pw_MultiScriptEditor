import os
import urllib.request
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt, QRectF

def generate_icons():
    app = QApplication([])
    out_dir = r"e:\Proyectos\GitHub\pw_MultiScriptEditor\multi_script_editor\icons"
    os.makedirs(out_dir, exist_ok=True)
    
    icons_to_make = {
        "delete_file": "trash-can-outline",
        "duplicate_file": "content-duplicate",
        "rename_file": "rename-box",
    }
    
    for name, mdi_name in icons_to_make.items():
        url = f"https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/master/svg/{mdi_name}.svg"
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
                # Scale slightly inward to 56x56
                renderer.render(painter, QRectF(4.0, 4.0, 56.0, 56.0))
                painter.end()
                
                out_path = os.path.join(out_dir, f"{name}.png")
                img.save(out_path, "PNG")
                print(f"Generated: {name}.png from {mdi_name}")
        except Exception as e:
            print(f"Failed to generate {name}: {e}")

if __name__ == '__main__':
    generate_icons()
