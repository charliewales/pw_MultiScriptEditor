"""
hqt - QT helper for Houdini v1.3
Use function "show"
========================================================================================
manual:
help(hqt.show)
========================================================================================
By default for Windows and Houdini 13 script append path <C:/Python27/Lib/site-packages>
to environment PATH. If PySide installed in different folder you mast append this path manually.
"""
qt = 0

import hou
import os, inspect

# import hqt to main
main = __import__('__main__')
ns = main.__dict__
if not __name__ in ns:
    exec('import {0}'.format(__name__), ns)

# Cleaned up global/wildcard imports to use explicit imports from vendor.Qt for better performance and maintainability
from vendor.Qt.QtCore import QEventLoop, QTimer, Qt
from vendor.Qt.QtGui import QIcon, QCursor
from vendor.Qt.QtWidgets import QAction, QApplication, QMenu

import tempfile

############################################################
############  GENERAL METHODS  #############################
############################################################

def show(cls, clear=False, ontop=False, name=None, floating=False, position=(), size=(), pane=None, replacePyPanel=False, hideTitleMenu=True, dialog=False, useThisPanel=None):
    """
    Main hqt function
    Parameters:
        cls                  : class of widget. NOT instance!
        clear=False          : delete exists window. For h13 only
        ontop=False          : window always on top (only floating window). For h13 only
        name=None            : window title in h13 or tab title in h14
        floating=False       : floating window or insert in tab Pane. For h14 only
        position=()          : tuple of int. Window Position. For floating window only
        size=()              : tuple of int. Window Size. For floating window only
        pane=None            : int number of pane to insert new tab. For h14 only
        replacePyPanel=False : replace exists PythonPanel or create new. For h14 only
        hideTitleMenu=True   : True = hide PythonPanel menu, False = collapse only. For h14 only
        useThisPanel         : hou.PythonPanel, set special pythonPanel to insert widget. For h14 only
----------------------------------------------------------------------------------------------------------
    Other functions:
        hqt.houdiniColors()         # list of colors in current Houdini theme
        hqt.getHouWindow()          # return main Qt widget of Houdini
        hqt.showWidget()            # Just show widget
        hqt.get_hou_style()         # return qt stylesheet for current Houdini theme
    """
    return showUi( cls, name=name, floating=floating, position=position, size=size, pane=pane, replacePyPanel=replacePyPanel, hideTitleMenu=hideTitleMenu, dialog=dialog,useThisPanel=useThisPanel)


def anyQtWindowsAreOpen():
    return any(w.isVisible() for w in QApplication.topLevelWidgets())

def exec_(app, *args):
    IntegratedEventLoop(app, args).exec_()

def execSynchronously(application, *args):
    exec_(application, *args)
    hou.ui.waitUntil(lambda: not anyQtWindowsAreOpen())

class IntegratedEventLoop(object):
    def __init__(self, application, dialogs):
        self.application = application
        self.dialogs = dialogs
        self.event_loop = QEventLoop()

    def exec_(self):
        hou.ui.addEventLoopCallback(self.processEvents)

    def processEvents(self):
        if not anyQtWindowsAreOpen():
            hou.ui.removeEventLoopCallback(self.processEvents)

        self.event_loop.processEvents()
        self.application.sendPostedEvents(None, 0)

################################### Search application
def getApp():
    qApp = QApplication.instance()
    if qApp is None:
        qApp = QApplication(['houdini'])
    return qApp

################################## Get main application in 13
def application():
    return main.hqt.getApp()

###################################### CLEAR
def clearUi(name):
    if name:
        for w in application().topLevelWidgets():
            if w.objectName() == name:
                try:
                    w.close()
                except:
                    pass

############################################################
############  METHODS FOR HOU 14 ###########################
############################################################

def getHouWindow():
    return hou.qt.mainWindow()


def showUi(cls,  name=None, floating=False, position=(),
            size=(), pane=None, replacePyPanel=False,
            hideTitleMenu=True, dialog=False, useThisPanel=None, args=None, kwargs=None):
    """
    open qt ui in houdini
    """
    if not inspect.isclass(cls):
        raise Exception('Object should be class, not instance')
    if dialog:
        h = getHouWindow()
        dial = cls(h, *(args or []), **(kwargs or {}))
        dial.show()

        return dial

    panFile = createPanelFile(cls, name)
    panFile = os.path.normpath(panFile).replace('\\', '/')
    hou.pypanel.installFile(panFile)
    pypan = hou.pypanel.interfacesInFile(panFile)[0]

    menu = installedInterfaces()
    menu.append(pypan.name())
    menu = [x for x in menu if not x == '__separator__']
    new = []
    for m in menu:
        if not m in new:
            new.append(m)

    hou.pypanel.setMenuInterfaces(tuple(new))

    if pane is None:
        pane =  max(0,len(hou.ui.curDesktop().panes())-1)
    if useThisPanel:
        python_panel = useThisPanel
    else:
        python_panel = None

        if floating:
            python_panel = hou.ui.curDesktop().createFloatingPaneTab(hou.paneTabType.PythonPanel, position, size)
        else:
            if replacePyPanel:
                for p in hou.ui.curDesktop().panes():
                    for t in p.tabs():
                        if t.type() == hou.paneTabType.PythonPanel:
                            python_panel = t.setType(hou.paneTabType.PythonPanel)
                if not python_panel:
                    python_panel = hou.ui.curDesktop().panes()[pane].createTab(hou.paneTabType.PythonPanel)
            else:
                python_panel = hou.ui.curDesktop().panes()[pane].createTab(hou.paneTabType.PythonPanel)

    python_panel.setIsCurrentTab()
    if hideTitleMenu:
        python_panel.showToolbar(0)
    else:
        python_panel.showToolbar(1)
        python_panel.expandToolbar(0)
    if hou.applicationVersion()[0] < 15:
        python_panel.setInterface(pypan)
    else:
        python_panel.setActiveInterface(pypan)

    QTimer.singleShot(2000, lambda x=panFile:delPanFile(x))


def showWidget(widget, tool=False):
    """
    Just show widget
    """
    if inspect.isclass(widget): #object not created
        widget = widget()
    widget.setParent(getHouWindow())
    if tool:
        widget.setWindowFlags(Qt.Tool)
    else:
        widget.setWindowFlags(Qt.Window)
    widget.show()
    return widget

def delPanFile(path):
    try:
        os.remove(path)
    except:
        pass

def installedInterfaces():
    res = []
    menu = hou.pypanel.menuInterfaces()
    for i in  menu:
        try:
            hou.pypanel.setMenuInterfaces((i,))
            res.append(i)
        except:
            pass
    return res

def createPanelFile(cls, name=None):
    """
    quick save python panel file
    """
    main.__dict__[cls.__name__] = cls
    if not name:
        name = cls.__name__
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<pythonPanelDocument>
   <interface name="{0}" label="{1}" icon="MISC_python">
    <script><![CDATA[main = __import__('__main__')
def createInterface():
    w = main.__dict__['{0}']()
    w.setStyleSheet('')
    w.setStyleSheet( main.__dict__['hqt'].get_hou_style() )
    return w
]]></script>
  </interface>
</pythonPanelDocument>'''.format(cls.__name__, name)
    tmp = tempfile.NamedTemporaryFile(delete = False, suffix='.pypanel')
    tmp.write(xml.encode())
    tmp.close()
    return tmp.name

class houdiniMenu(QMenu):
    def __init__(self):
        super(houdiniMenu, self).__init__(getHouWindow())
        self.par = getHouWindow()

    def addItem(self, name, callback, icon=None):
        if not isinstance(name, str):
            return False
        if not hasattr(callback, '__call__'):
            return False
        act = QAction(name, self.par)
        act.triggered.connect(callback)
        if icon:
            if isinstance(icon, str):
                if os.path.exists(icon):
                    try:
                        icon = QIcon(icon)
                        act.setIcon(icon)
                    except:
                        print('Error create icon:', icon)
                else:
                    try:
                        icon = hou.ui.createQtIcon(icon)
                        act.setIcon(icon)
                    except:
                        print('Icon not found:', icon)
            elif isinstance(icon, QIcon):
                act.setIcon(icon)
        self.addAction(act)

    def show(self, *args, **kwargs):
        if hasattr(self, 'exec'):
            return getattr(self, 'exec')(QCursor.pos())
        else:
            return self.exec_(QCursor.pos())

############################################################
############  RESOURCES  ###################################
############################################################

# import hqt
# s = hqt.get_hou_style('Houdini Dark')
# w.setStyleSheet(s)


def get_hou_style(theme=None):
    try:
        return hou.ui.qtStyleSheet()
    except AttributeError:
        return ''
