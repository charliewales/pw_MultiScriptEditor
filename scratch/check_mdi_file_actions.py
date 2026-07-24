import urllib.request
urls = [
    'trash-can-outline', 'content-duplicate', 'rename-box', 'pencil-outline'
]
for u in urls:
    try:
        req = urllib.request.Request(f'https://raw.githubusercontent.com/Templarian/MaterialDesign-SVG/master/svg/{u}.svg', headers={'User-Agent': 'Mozilla/5.0'})
        urllib.request.urlopen(req)
        print(f'{u}: EXISTS')
    except Exception:
        print(f'{u}: NOT FOUND')
