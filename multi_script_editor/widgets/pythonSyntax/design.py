from core.settings_model import SettingsModel
import os, re



defaultColors = dict(
        background = (40,40,40),
        window = (50, 50, 50),
        output_background = (40,40,40),
        keywords = (65,255,130),
        digits = (250,255,62),
        definition = (255,160,250),
        operator = (230, 220, 110),
        extra = (110,180,230),
        methods = (120, 190, 205),
        comment = (110,100,100),
        string = (245,165,18),
        docstring = (130,160,75),
        boolean = (160,220,120),
        brace = (235,235,195),
        completer_text=(200,200,200),
        completer_selected_text= (105,105,105),
        completer_hover_text= (255,255,255),
        completer_background=(59,59,59),
        completer_alt_background= (65,65,65),
        completer_hover_background= (85,85,85),
        completer_selected_background= (123,123,123),
        default=(210,210,210),
        whitespace=(70,70,70),
        highlight_line=(85, 85, 85),
        tab_radius=12,
        use_theme_font_on_completer=True,
        use_theme_font_on_menus=False,
        use_theme_font_on_outline=True,
        use_theme_font_on_status_bar=False,
        use_theme_font_on_tab_label=True,
)

predefinedThemes = {
    'Multi Script Editor': defaultColors,
    'One Dark Pro': dict(
        background=(40, 44, 52),
        output_background=(40, 44, 52),
        keywords=(198, 120, 221),
        digits=(209, 154, 102),
        definition=(97, 175, 239),
        operator=(86, 182, 194),
        extra=(224, 108, 117),
        methods=(97, 175, 239),
        comment=(92, 99, 112),
        string=(152, 195, 121),
        docstring=(92, 99, 112),
        boolean=(209, 154, 102),
        brace=(171, 178, 191),
        completer_text=(171, 178, 191),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(33, 37, 43),
        completer_alt_background=(40, 44, 52),
        completer_hover_background=(44, 49, 58),
        completer_selected_background=(44, 49, 58),
        default=(171, 178, 191),
        whitespace=(59, 64, 72),
        highlight_line=(44, 49, 58)
    ),
    'Dracula Official': dict(
        background=(40, 42, 54),
        output_background=(40, 42, 54),
        keywords=(255, 121, 198),
        digits=(189, 147, 249),
        definition=(80, 250, 123),
        operator=(255, 121, 198),
        extra=(139, 233, 253),
        methods=(80, 250, 123),
        comment=(98, 114, 164),
        string=(241, 250, 140),
        docstring=(98, 114, 164),
        boolean=(189, 147, 249),
        brace=(248, 248, 242),
        completer_text=(248, 248, 242),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(33, 34, 44),
        completer_alt_background=(40, 42, 54),
        completer_hover_background=(68, 71, 90),
        completer_selected_background=(68, 71, 90),
        default=(248, 248, 242),
        whitespace=(68, 71, 90),
        highlight_line=(68, 71, 90)
    ),
    'Catppuccin': dict(
        background=(36, 39, 58),
        output_background=(36, 39, 58),
        keywords=(198, 160, 246),
        digits=(245, 169, 127),
        definition=(138, 173, 244),
        operator=(145, 215, 227),
        extra=(237, 135, 150),
        methods=(138, 173, 244),
        comment=(91, 96, 120),
        string=(166, 218, 149),
        docstring=(91, 96, 120),
        boolean=(245, 169, 127),
        brace=(202, 211, 245),
        completer_text=(202, 211, 245),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(30, 32, 48),
        completer_alt_background=(36, 39, 58),
        completer_hover_background=(54, 58, 79),
        completer_selected_background=(54, 58, 79),
        default=(202, 211, 245),
        whitespace=(54, 58, 79),
        highlight_line=(54, 58, 79)
    ),
    'Tokyo Night': dict(
        background=(26, 27, 38),
        output_background=(26, 27, 38),
        keywords=(187, 154, 247),
        digits=(255, 158, 100),
        definition=(122, 162, 247),
        operator=(137, 221, 255),
        extra=(247, 118, 142),
        methods=(122, 162, 247),
        comment=(86, 95, 137),
        string=(158, 206, 106),
        docstring=(86, 95, 137),
        boolean=(255, 158, 100),
        brace=(192, 202, 245),
        completer_text=(192, 202, 245),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(22, 22, 30),
        completer_alt_background=(26, 27, 38),
        completer_hover_background=(41, 46, 66),
        completer_selected_background=(41, 46, 66),
        default=(192, 202, 245),
        whitespace=(41, 46, 66),
        highlight_line=(41, 46, 66)
    ),
    'Nord': dict(
        background=(46, 52, 64),
        output_background=(46, 52, 64),
        keywords=(129, 161, 193),
        digits=(180, 142, 173),
        definition=(143, 188, 187),
        operator=(129, 161, 193),
        extra=(191, 97, 106),
        methods=(136, 192, 208),
        comment=(76, 86, 106),
        string=(163, 190, 140),
        docstring=(76, 86, 106),
        boolean=(208, 135, 112),
        brace=(216, 222, 233),
        completer_text=(216, 222, 233),
        completer_selected_text=(236, 239, 244),
        completer_hover_text=(236, 239, 244),
        completer_background=(59, 66, 82),
        completer_alt_background=(46, 52, 64),
        completer_hover_background=(67, 76, 94),
        completer_selected_background=(67, 76, 94),
        default=(216, 222, 233),
        whitespace=(67, 76, 94),
        highlight_line=(59, 66, 82)
    ),
    'Monokai Pro': dict(
        background=(45, 42, 46),
        output_background=(45, 42, 46),
        keywords=(255, 97, 136),
        digits=(171, 157, 242),
        definition=(169, 220, 118),
        operator=(255, 97, 136),
        extra=(120, 220, 232),
        methods=(169, 220, 118),
        comment=(114, 112, 114),
        string=(255, 216, 102),
        docstring=(114, 112, 114),
        boolean=(171, 157, 242),
        brace=(252, 252, 250),
        completer_text=(252, 252, 250),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(34, 31, 34),
        completer_alt_background=(45, 42, 46),
        completer_hover_background=(64, 62, 65),
        completer_selected_background=(64, 62, 65),
        default=(252, 252, 250),
        whitespace=(64, 62, 65),
        highlight_line=(64, 62, 65)
    ),
    'Monokai': dict(
        background=(39, 40, 34),
        output_background=(39, 40, 34),
        keywords=(249, 38, 114),
        digits=(174, 129, 255),
        definition=(166, 226, 46),
        operator=(249, 38, 114),
        extra=(102, 217, 239),
        methods=(166, 226, 46),
        comment=(117, 113, 94),
        string=(230, 219, 116),
        docstring=(117, 113, 94),
        boolean=(174, 129, 255),
        brace=(248, 248, 242),
        completer_text=(248, 248, 242),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(30, 31, 28),
        completer_alt_background=(39, 40, 34),
        completer_hover_background=(73, 72, 62),
        completer_selected_background=(73, 72, 62),
        default=(248, 248, 242),
        whitespace=(73, 72, 62),
        highlight_line=(62, 61, 50)
    ),
    'Solarized Dark': dict(
        background=(0, 43, 54),
        output_background=(0, 43, 54),
        keywords=(133, 153, 0),
        digits=(42, 161, 152),
        definition=(38, 139, 210),
        operator=(203, 75, 22),
        extra=(38, 139, 210),
        methods=(38, 139, 210),
        comment=(88, 110, 117),
        string=(42, 161, 152),
        docstring=(88, 110, 117),
        boolean=(211, 54, 130),
        brace=(131, 148, 150),
        completer_text=(131, 148, 150),
        completer_selected_text=(253, 246, 227),
        completer_hover_text=(253, 246, 227),
        completer_background=(7, 54, 66),
        completer_alt_background=(0, 43, 54),
        completer_hover_background=(88, 110, 117),
        completer_selected_background=(88, 110, 117),
        default=(131, 148, 150),
        whitespace=(7, 54, 66),
        highlight_line=(7, 54, 66)
    ),
    'Kimbie Dark': dict(
        background=(34, 26, 15),
        output_background=(34, 26, 15),
        keywords=(220, 57, 88),
        digits=(247, 154, 50),
        definition=(240, 100, 49),
        operator=(240, 100, 49),
        extra=(138, 177, 176),
        methods=(138, 177, 176),
        comment=(214, 186, 173),
        string=(136, 155, 74),
        docstring=(214, 186, 173),
        boolean=(247, 154, 50),
        brace=(211, 175, 134),
        completer_text=(211, 175, 134),
        completer_selected_text=(251, 235, 212),
        completer_hover_text=(251, 235, 212),
        completer_background=(54, 39, 18),
        completer_alt_background=(34, 26, 15),
        completer_hover_background=(81, 65, 44),
        completer_selected_background=(81, 65, 44),
        default=(211, 175, 134),
        whitespace=(81, 65, 44),
        highlight_line=(81, 65, 44)
    ),

    'Ayu Mirage': dict(
        background=(33, 39, 51),
        output_background=(33, 39, 51),
        keywords=(255, 167, 89),
        digits=(255, 204, 102),
        definition=(255, 204, 102),
        operator=(242, 135, 121),
        extra=(115, 208, 255),
        methods=(255, 204, 102),
        comment=(92, 103, 115),
        string=(186, 230, 126),
        docstring=(92, 103, 115),
        boolean=(255, 167, 89),
        brace=(203, 204, 198),
        completer_text=(203, 204, 198),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(25, 30, 42),
        completer_alt_background=(33, 39, 51),
        completer_hover_background=(52, 63, 76),
        completer_selected_background=(52, 63, 76),
        default=(203, 204, 198),
        whitespace=(52, 63, 76),
        highlight_line=(52, 63, 76)
    ),
    'Sonokai': dict(
        background=(44, 46, 52),
        output_background=(44, 46, 52),
        keywords=(255, 109, 126),
        digits=(245, 151, 98),
        definition=(158, 208, 114),
        operator=(255, 109, 126),
        extra=(118, 204, 224),
        methods=(158, 208, 114),
        comment=(127, 132, 144),
        string=(226, 199, 146),
        docstring=(127, 132, 144),
        boolean=(245, 151, 98),
        brace=(226, 226, 227),
        completer_text=(226, 226, 227),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(34, 36, 41),
        completer_alt_background=(44, 46, 52),
        completer_hover_background=(63, 68, 81),
        completer_selected_background=(63, 68, 81),
        default=(226, 226, 227),
        whitespace=(63, 68, 81),
        highlight_line=(63, 68, 81)
    ),
    'GitHub Dark': dict(
        background=(13, 17, 23),
        output_background=(13, 17, 23),
        keywords=(255, 123, 114),
        digits=(121, 192, 255),
        definition=(210, 168, 255),
        operator=(201, 209, 217),
        extra=(165, 214, 255),
        methods=(210, 168, 255),
        comment=(139, 148, 158),
        string=(165, 214, 255),
        docstring=(139, 148, 158),
        boolean=(121, 192, 255),
        brace=(201, 209, 217),
        completer_text=(201, 209, 217),
        completer_selected_text=(255, 255, 255),
        completer_hover_text=(255, 255, 255),
        completer_background=(1, 4, 9),
        completer_alt_background=(13, 17, 23),
        completer_hover_background=(33, 38, 45),
        completer_selected_background=(33, 38, 45),
        default=(201, 209, 217),
        whitespace=(33, 38, 45),
        highlight_line=(33, 38, 45)
    )
}

def getColors(theme=False):
    s = SettingsModel()
    settings = s.read_settings()
    if not theme:
        theme = settings.get('theme')

    if theme in predefinedThemes:
        result = {k:v for k,v in predefinedThemes[theme].items()}
        for k, v in defaultColors.items():
            if k not in result:
                result[k] = v
    else:
        result = {k:v for k,v in defaultColors.items()}

        if 'colors' in settings:
            colors = settings['colors'].get(theme)
            if colors:
                for k, v in colors.items():
                    result[k] = v

    if 'tab_background' not in result:
        result['tab_background'] = result.get('window', (50, 50, 50))
    if 'tab_border' not in result:
        result['tab_border'] = result.get('highlight_line', (85, 85, 85))
    if 'tab_text' not in result:
        result['tab_text'] = result.get('default', (210, 210, 210))
    if 'tab_hover_background' not in result:
        result['tab_hover_background'] = result.get('highlight_line', (85, 85, 85))
    if 'tab_hover_border' not in result:
        result['tab_hover_border'] = result.get('highlight_line', (85, 85, 85))
    if 'tab_hover_text' not in result:
        result['tab_hover_text'] = result.get('default', (210, 210, 210))
    if 'tab_selected_background' not in result:
        result['tab_selected_background'] = result.get('background', (40, 40, 40))
    if 'tab_selected_border' not in result:
        result['tab_selected_border'] = result.get('background', (40, 40, 40))
    if 'tab_selected_text' not in result:
        result['tab_selected_text'] = result.get('default', (210, 210, 210))

    return result

def editorStyle(theme=None):
    colors = getColors(theme)
    colors = {k:tuple(v) if isinstance(v, list) else v for k,v in colors.items()}
    return applyColorToMainStyle(colors)


def applyColorToMainStyle(colors=None):
    StyleCss = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'style', 'style.css')
    icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icons').replace('\\', '/')
    if os.path.exists(StyleCss):
        text = open(StyleCss).read()
        text = text.replace("../icons", icons_dir)
        proxys = re.findall(r'\[.*\]', text)
        for p in proxys:
            name = p[1:-1]
            if name in colors:
                c = colors[name]
                if isinstance(c, (list, tuple)):
                    val = '#%02x%02x%02x' % (c[0], c[1], c[2])
                    text = text.replace(f'rgb{p}', val)
                else:
                    val = str(c)
                    text = text.replace(p, val)
            elif name == 'textsize':
                text = text.replace(p, '10')
        return text
    return ''
