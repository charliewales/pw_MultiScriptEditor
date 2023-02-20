import webbrowser

import sys
if sys.version_info.major >= 3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen
import re


QtWidgets_url = 'https://doc.qt.io/qtforpython-5/PySide2/QtWidgets'
QtGui_url = 'https://doc.qt.io/qtforpython-5/PySide2/QtGui'
QtCore_url = 'https://doc.qt.io/qtforpython-5/PySide2/QtCore'

try:
    import PySide2
except:
    QtWidgets_url = 'https://pyside.github.io/docs/pyside/PySide/QtGui'
    QtGui_url = 'https://pyside.github.io/docs/pyside/PySide/QtGui'
    QtCore_url = 'https://pyside.github.io/docs/pyside/PySide/QtCore'

def url_exists(url):
    found = 0
    try:
        ret = urlopen(url)
        if ret.code == 200:
            found = 1
    except Exception as e:
        print(e.__class__,  e, url)
    return found


def get_help(text):
    if text == 'QtWidgets':
        webbrowser.open('{}/index.html#module-PySide2.QtWidgets'.format(QtWidgets_url))
    elif text == 'QtGui':
        webbrowser.open('{}/index.html#module-PySide2.QtGui'.format(QtGui_url))
    elif text == 'QtCore':
        webbrowser.open('{}/index.html#module-PySide2.QtCore'.format(QtCore_url))
    else:

        if text.startswith('Q'):
            QtWidgets_class = '{}/{}.html'.format(QtWidgets_url, text)
            QtGui_class = '{}/{}.html'.format(QtGui_url, text)
            QtCore_class = '{}/{}.html'.format(QtCore_url, text)

            if url_exists(QtWidgets_class):
                webbrowser.open(QtWidgets_class)
            elif url_exists(QtGui_class):
                webbrowser.open(QtGui_class)
            elif url_exists(QtCore_class):
                webbrowser.open(QtCore_class)

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
            elif url_exists(OpenMayaUI):
                webbrowser.open(OpenMayaUI)
            elif url_exists(OpenMayaAnim):
                webbrowser.open(OpenMayaAnim)
            elif url_exists(OpenMayaRender):
                webbrowser.open(OpenMayaRender)

        elif text == 'OpenMaya':
            OpenMaya = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_html'
            webbrowser.open(OpenMaya)
        elif text == 'OpenMayaAnim':
            OpenMayaAnim  = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_anim_html'
            webbrowser.open(OpenMayaAnim )
        elif text == 'OpenMayaRender':
            OpenMayaRender  = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_render_html'
            webbrowser.open(OpenMayaRender )
        elif text == 'OpenMayaUI':
            OpenMayaUI = 'https://help.autodesk.com/view/MAYAUL/2022/ENU/?guid=Maya_SDK_py_ref_namespace_open_maya_u_i_html'
            webbrowser.open(OpenMayaUI)
        else:
            python_cmd_url = 'http://help.autodesk.com/cloudhelp/2023/ENU/Maya-Tech-Docs/CommandsPython/{}.html'.format(text)
            if url_exists(python_cmd_url):
                webbrowser.open(python_cmd_url)
