import builtins
import re
import sys
import webbrowser

try:
    from urllib.request import urlopen
except:
    from urllib2 import urlopen

QtWidgets_url = 'https://doc.qt.io/qtforpython-{}/PySide{}/QtWidgets'
QtGui_url = 'https://doc.qt.io/qtforpython-{}/PySide{}/QtGui'
QtCore_url = 'https://doc.qt.io/qtforpython-{}/PySide{}/QtCore'

try:
    try:
        QtCore_url = QtCore_url.format("5", "2")
        QtWidgets_url = QtWidgets_url.format("5", "2")
        QtGui_url = QtGui_url.format("5", "2")
    except:
        QtCore_url = QtCore_url.format("6", "6")
        QtWidgets_url = QtWidgets_url.format("6", "6")
        QtGui_url = QtGui_url.format("6", "6")
except:
    QtWidgets_url = 'https://pyside.github.io/docs/pyside/PySide/QtGui'
    QtGui_url = 'https://pyside.github.io/docs/pyside/PySide/QtGui'
    QtCore_url = 'https://pyside.github.io/docs/pyside/PySide/QtCore'


PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"

built_ins = []
builtins_list = dir(builtins)

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

            OpenMaya = 'https://help.autodesk.com/cloudhelp/2027/ENU/MAYA-API-REF/cpp_ref/class_{0}.html'.format(class_html_name)
            OpenMayaAnim = 'https://help.autodesk.com/cloudhelp/2027/ENU/MAYA-API-REF/cpp_ref/class_{0}.html'.format(class_html_name)
            OpenMayaRender = 'https://help.autodesk.com/cloudhelp/2027/ENU/MAYA-API-REF/cpp_ref/class_{0}.html'.format(class_html_name)
            OpenMayaUI = 'https://help.autodesk.com/cloudhelp/2027/ENU/MAYA-API-REF/cpp_ref/class_{0}.html'.format(class_html_name)

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
            OpenMaya = 'https://help.autodesk.com/cloudhelp/2027/ENU/MAYA-API-REF/cpp_ref/group___open_maya.html'
            webbrowser.open(OpenMaya)
            return
        elif text == 'OpenMayaAnim':
            OpenMayaAnim  = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_anim_html'
            webbrowser.open(OpenMayaAnim )
            return
        elif text == 'OpenMayaRender':
            OpenMayaRender  = 'https://help.autodesk.com/cloudhelp/2027/ENU/MAYA-API-REF/cpp_ref/group___open_maya_render.html'
            webbrowser.open(OpenMayaRender )
            return
        elif text == 'OpenMayaUI':
            OpenMayaUI = 'https://help.autodesk.com/cloudhelp/2027/ENU/MAYA-API-REF/cpp_ref/group___open_maya_u_i.html'
            webbrowser.open(OpenMayaUI)
            return
        else:
            python_cmd_url = 'http://help.autodesk.com/cloudhelp/2027/ENU/Maya-Tech-Docs/CommandsPython/{}.html'.format(text)
            if url_exists(python_cmd_url):
                webbrowser.open(python_cmd_url)

            python_module = 'https://docs.python.org/{0}/library/{1}.html'.format(PYTHON_VERSION, text)
            if url_exists(python_module):
                webbrowser.open(python_module)

            if text in built_ins:
                python_function = 'https://docs.python.org/{0}/library/functions.html#{1}'.format(PYTHON_VERSION, text)
                if url_exists(python_function):
                    webbrowser.open(python_function)
