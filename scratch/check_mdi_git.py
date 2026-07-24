import urllib.request
urls = [
    'source-branch', 'git', 'file-compare', 'compare',
    'file-plus-outline', 'file-minus-outline', 'plus-box-outline', 'minus-box-outline',
    'source-commit', 'check-circle-outline',
    'undo-variant', 'delete-restore', 'restore',
    'history', 'clock-outline',
    'content-copy'
]
for u in urls:
    try:
        req = urllib.request.Request(f'https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/master/svg/{u}.svg', headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req)
        print(f'{u}: EXISTS')
    except Exception:
        print(f'{u}: NOT FOUND')
