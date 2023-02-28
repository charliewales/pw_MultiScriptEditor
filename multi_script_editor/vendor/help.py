import re
import sys
import webbrowser

try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

QtWidgets_url = 'https://doc.qt.io/qtforpython-5/PySide2/QtWidgets'
QtGui_url = 'https://doc.qt.io/qtforpython-5/PySide2/QtGui'
QtCore_url = 'https://doc.qt.io/qtforpython-5/PySide2/QtCore'

try:
    import PySide2
except:
    QtWidgets_url = 'https://pyside.github.io/docs/pyside/PySide/QtGui'
    QtGui_url = 'https://pyside.github.io/docs/pyside/PySide/QtGui'
    QtCore_url = 'https://pyside.github.io/docs/pyside/PySide/QtCore'


PYTHON_VERSION = sys.version_info.major

built_ins = list()
if PYTHON_VERSION >= 3:
    import builtins
    builtins_list = dir(builtins)
else:
    builtins_list = ['abs', 'all', 'any', 'apply', 'basestring', 'bin',
                     'bool', 'buffer', 'bytearray', 'bytes', 'callable',
                     'chr', 'classmethod', 'cmp', 'coerce', 'compile',
                     'complex', 'copyright', 'credits', 'delattr', 'dict',
                     'dir', 'divmod', 'enumerate', 'eval', 'execfile',
                     'exit', 'file', 'filter', 'float', 'format', 'frozenset',
                     'getattr', 'globals', 'hasattr', 'hash', 'help', 'hex',
                     'id', 'input', 'int', 'intern', 'isinstance', 'issubclass',
                     'iter', 'len', 'license', 'list', 'locals', 'long', 'map',
                     'max', 'memoryview', 'min', 'next', 'object', 'oct',
                     'open', 'ord', 'pow', 'print', 'property', 'quit', 'range',
                     'raw_input', 'reduce', 'reload', 'repr', 'reversed',
                     'round', 'set', 'setattr', 'slice', 'sorted',
                     'staticmethod', 'str', 'sum', 'super', 'tuple',
                     'type', 'unichr', 'unicode', 'vars', 'xrange', 'zip']

# store built-in functions
for bi in builtins_list:
    if bi.startswith('_') or bi[0].isupper():
        continue
    built_ins.append(bi)


def url_exists(url):
    found = False
    try:
        ret = urlopen(url)
        if ret.code == 200:
            found = True
    except Exception as e:
        print(e.__class__,  e, url)
    return found


def get_help(text):
    text = text.strip()
    if text == 'QtWidgets':
        webbrowser.open('{}/index.html'.format(QtWidgets_url))
    elif text == 'QtGui':
        webbrowser.open('{}/index.html'.format(QtGui_url))
    elif text == 'QtCore':
        webbrowser.open('{}/index.html'.format(QtCore_url))
    else:
        if text.startswith('Q'):
            QtWidgets_class = '{}/{}.html'.format(QtWidgets_url, text)
            QtGui_class = '{}/{}.html'.format(QtGui_url, text)
            QtCore_class = '{}/{}.html'.format(QtCore_url, text)

            if url_exists(QtWidgets_class):
                webbrowser.open(QtWidgets_class)
                return
            elif url_exists(QtGui_class):
                webbrowser.open(QtGui_class)
                return
            elif url_exists(QtCore_class):
                webbrowser.open(QtCore_class)
                return

        elif text.startswith('M'):
            class_parts = re.findall('[A-Z][^A-Z]*', text)
            class_parts = '_'.join(class_parts)
            class_html_name = class_parts.lower()

            OpenMaya = 'https://help.autodesk.com/cloudhelp/2022/ENU/Maya-SDK/py_ref/class_open_maya_1_1_{0}.html'.format(class_html_name)
            OpenMayaAnim = 'https://help.autodesk.com/cloudhelp/2022/ENU/Maya-SDK/py_ref/class_open_maya_anim_1_1_{0}.html'.format(class_html_name)
            OpenMayaRender = 'https://help.autodesk.com/cloudhelp/2022/ENU/Maya-SDK/py_ref/class_open_maya_render_1_1_{0}.html'.format(class_html_name)
            OpenMayaUI = 'https://help.autodesk.com/cloudhelp/2022/ENU/Maya-SDK/py_ref/class_open_maya_u_i_1_1_{0}.html'.format(class_html_name)

            if url_exists(OpenMaya):
                webbrowser.open(OpenMaya)
                return
            elif url_exists(OpenMayaUI):
                webbrowser.open(OpenMayaUI)
                return
            elif url_exists(OpenMayaAnim):
                webbrowser.open(OpenMayaAnim)
                return
            elif url_exists(OpenMayaRender):
                webbrowser.open(OpenMayaRender)
                return

        elif text == 'OpenMaya':
            OpenMaya = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_html'
            webbrowser.open(OpenMaya)
            return
        elif text == 'OpenMayaAnim':
            OpenMayaAnim  = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_anim_html'
            webbrowser.open(OpenMayaAnim )
            return
        elif text == 'OpenMayaRender':
            OpenMayaRender  = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_render_html'
            webbrowser.open(OpenMayaRender )
            return
        elif text == 'OpenMayaUI':
            OpenMayaUI = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_u_i_html'
            webbrowser.open(OpenMayaUI)
            return
        else:
            python_cmd_url = 'http://help.autodesk.com/cloudhelp/2023/ENU/Maya-Tech-Docs/CommandsPython/{}.html'.format(text)
            if url_exists(python_cmd_url):
                webbrowser.open(python_cmd_url)

            python_module = 'https://docs.python.org/{0}/library/{1}.html'.format(PYTHON_VERSION, text)
            if url_exists(python_module):
                webbrowser.open(python_module)

            if text in built_ins:
                python_function = 'https://docs.python.org/{0}/library/functions.html#{1}'.format(PYTHON_VERSION, text)
                if url_exists(python_function):
                    webbrowser.open(python_function)
