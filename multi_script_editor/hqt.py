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
import sys, os, inspect

# import hqt to main
main = __import__('__main__')
ns = main.__dict__
if not __name__ in ns:
    exec('import {0}'.format(__name__), ns)

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *

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
        hqt.applyStyle(widget)      # apply QT stile and Houdini icon for widget
        hqt.setIcon(widget)         # set Houdini icon for widget
        hqt.getHouWindow()          # return main Qt widget of Houdini
        hqt.showWidget()            # Just show widget
        hqt.get_h14_style()         # return qt stylesheet for current Houdini theme
    """
    return showUi14( cls, name=name, floating=floating, position=position, size=size, pane=pane, replacePyPanel=replacePyPanel, hideTitleMenu=hideTitleMenu, dialog=dialog,useThisPanel=useThisPanel)


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
        #houdini style
        applyStyle(qApp)
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

##################################### STYLE
def applyStyle(widget, theme=False, h13=False):
    widget.setStyleSheet('')
    widget.setStyleSheet(qss13() if h13 else get_h14_style(theme))
    setIcon(widget)

def setIcon(widget):
    if hou.applicationVersion()[0] < 15:
        if widget.windowIcon().isNull():
            ico = QIcon(':/houdini.png')
            widget.setWindowIcon(ico)
        else:
            ico = hou.ui.createQtIcon('DESKTOP_application')
            widget.setWindowIcon(ico)

############################################################
############  METHODS FOR HOU 14 ###########################
############################################################

def getHouWindow(): # temporary method
    # check Houdini version
#    version = hou.applicationVersion()[0]
#    if 13 <= version:
#        app = QApplication.instance()
#        for w in app.topLevelWidgets():
#            if w.windowIconText():
#                return w
#    elif 13 < version < 17:
#        return hou.ui.mainQtWindow()
#    elif version > 16:
#        return hou.qt.mainWindow()
    return hou.qt.mainWindow()



houWindow = getHouWindow()

def showUi14(cls,  name=None, floating=False, position=(),
             size=(), pane=None, replacePyPanel=False,
             hideTitleMenu=True, dialog=False, useThisPanel=None, args=None, kwargs=None):
    """
    open qt ui in houdini 14
    """
    if not inspect.isclass(cls):
        raise Exception('Object should be class, not instance')
    if dialog:
        h = getHouWindow()
        dial = cls(h, *(args or []), **(kwargs or {}))
        dial.setStyleSheet('')
        dial.setStyleSheet(get_h14_style())
        res = dial.exec_()
        return (res, dial)

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
    applyStyle(widget)
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
    w.setStyleSheet( main.__dict__['hqt'].get_h14_style() )
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
        return self.exec_(QCursor.pos())

############################################################
############  RESOURCES  ###################################
############################################################
import os, re, glob

# import hqt
# s = hqt.get_h14_style('Houdini Dark')
# w.setStyleSheet(s)

def get_h14_style(theme=None):
    colors = getThemeColors(theme)
    if colors:
        style = []
        mid = sum(colors['BackColor'])/3
        gamma = qss14ImagesDark if mid < 0.5 else qss14ImagesLight
        for l in qss14().split('\n'):
            variables = re.findall('(@.*@)', l)
            if variables:
                for v in variables:
                    val = v[1:-1]
                    br = 1
                    if ':Brightness' in val:
                        name, br = val.split(':')
                        br = float(br.split('=')[-1])
                    else:
                        name = val
                    if name in colors:
                        c = ','.join([str( min(int(x*br*255),255) ) for x in colors[name]])
                    else:
                        #use default
                        print('Color not found', name)
                        c = ','.join([str( min(int(x*br*255),255) ) for x in colors['BackColor']])
                    l = l.replace(v, c)

            images = re.findall('(\$.*\$)', l)
            if images:
                for i in images:
                    img = i[1:-1]
                    if img in gamma:
                        l = l.replace(i, gamma[img])
            style.append(l)
        return  '\n'.join(style)
        # return  hou.ui.qtStyleSheet()+'\n'.join(style)

    else:
        return ''

def getCurrentColorTheme():
    pref = hou.homeHoudiniDirectory()
    uipref = os.path.join(pref, 'ui.pref')
    if os.path.exists(uipref):
        with open(uipref) as f:
            for l in f.readlines():
                if l.startswith('colors.scheme'):
                    theme = re.findall('\"(.*)\"', l)[0]
                    return theme

def getThemeColors(theme=None):
    if not theme:
        theme = getCurrentColorTheme()
    conf = os.path.join(hou.getenv('HFS'), 'houdini', 'config')
    if os.path.exists(conf):
        for uif in glob.glob1(conf, "*.hcs"):
            path = os.path.join(conf, uif)
            with open(path) as f:
                name = f.readline().split(':')[-1].strip()
                if name == theme:
                    reader = colorReader(path)
                    colors = reader.parse()
                    return colors

class houdiniColorsClass(QMainWindow):
    def __init__(self, theme=None):
        super(houdiniColorsClass, self).__init__(getHouWindow(), Qt.WindowStaysOnTopHint)
        # self.setWindowFlags()
        self.centralwidget = QWidget(self)
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.scrollArea = QScrollArea(self.centralwidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.widget = QWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_3 = QGridLayout(self.widget)

        self.verticalLayout_2.addWidget(self.widget)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.setCentralWidget(self.centralwidget)
        self.setStyleSheet(get_h14_style())
        colors = getThemeColors(theme)
        for i, name in enumerate(sorted(colors, key=lambda x:x)):
            color = colors[name]
            if not color:continue
            if len(color) != 3:
                continue
            l = QLineEdit()
            l.setMinimumWidth(200)
            l.setText(name)
            l.setReadOnly(1)
            self.verticalLayout_3.addWidget(l, i, 0)
            c = QLabel()
            c.setText(str(color))
            col = QColor()
            if (sum(color)/3) < 0.5:
                text = '#fff'
            else:
                text = '#000'
            col.setRgbF(*color)
            style = 'background-color: %s; color: %s;' % (col.name(), text)
            # print style
            c.setStyleSheet(style)
            self.verticalLayout_3.addWidget(c, i, 1)

def houdiniColors():
    show(houdiniColorsClass, name='Colors', hideTitleMenu=True)
    # showUi14(houdiniColorsClass, name='Colors', floating=False)

class colorReader(object):
    '''
    Read houdini color theme
    '''
    def __init__(self, path):
        self.lines = []
        self.colors = {}
        if os.path.exists(path):
            self.lines = open(path).readlines()
        self.preDef = dict(white=[1,1,1],
                           black=[0,0,0],
                           red=[1,0,0],
                           green=[0,1,0],
                           blue=[0,0,1])

    def parse(self):
        for l in self.lines:
            if l.startswith('//'):
                continue
            l = l.split('//')[0].strip()
            if not l:
                continue
            name, value = self.getColor(l)
            if name:
                if not name in self.colors:
                    if isinstance(value,str):
                        if value in self.colors.keys():
                            self.colors[name] = self.colors[value]
                    else:
                        self.colors[name] = value
        return self.colors

    def getColor(self, line):
        name = val = None
        if line.startswith('#define'):
            spl = line.split()[1:]
            name = spl[0]
            val = ' '.join(spl[1:])
        else:
            parts = line.split(':')
            if len(parts) == 2:
                name, val = parts
        val = self.strToColor(val)
        return name, val

    def strToColor(self, line):
        if not line:
            return None
        line = line.strip()

        if line.lower() in self.preDef:
            return self.preDef[line.lower()]

        gr = re.findall("grey\(([0-9\.]+)\)",  line ,flags=re.IGNORECASE)
        if gr:
            g = round(float(gr[0]),4)
            return [g, g, g]

        gr = re.findall("grey([0-9\.]+)",  line.strip() ,flags=re.IGNORECASE)
        if gr:
            g = round(float(gr[0])/255,4)
            return [g,g,g]

        hsv =  re.findall("HSV\s+([\d\.]*\s+[\d\.]*\s+[\d\.]*)",  line, flags=re.IGNORECASE)
        if hsv:
            h,s,v = [float(x) for x in hsv[0].split()]
            qc = QColor()
            qc.setHsv(h,min(s,1)*255,min(v,1)*255)
            return [round(qc.red()*1.0/255, 4), round(qc.green()*1.0/255, 4), round(qc.blue()*1.0/255, 4)]

        rgb = re.findall("([\d\.]*\s+[\d\.]*\s+[\d\.]*)",  line, flags=re.IGNORECASE)
        if rgb:
            return [round(float(x),4) for x in rgb[0].split()]

        hx = re.findall("#[a-zA-Z0-9]+\s*[a-zA-Z0-9]+\s*[a-zA-Z0-9]+",  line ,flags=re.IGNORECASE)
        if hx:
            qc = QColor(''.join(hx[0].split()))
            return [round(qc.red()*1.0/255, 4), round(qc.green()*1.0/255, 4), round(qc.blue()*1.0/255, 4)]

        shd = re.findall("^SHADOW([0-9_]+)",  line ,flags=re.IGNORECASE) # For some "Houdini Pro" lines
        if shd:
            if not line in self.colors:
                g = float( '0.'+shd[0].replace('_','') )
                return [g, g, g]
        return line

qss14ImagesDark = dict(
    cb_unchecked = ':/cb_unchecked_d.png',
    cb_unchecked_dis = ':/cb_unchecked_dis_d.png',
    cb_checked = ':/cb_checked_d.png',
    cb_checked_dis = ':/cb_checked_dis_d.png',
    rb_unchecked = ':/rb_unchecked_d.png',
    rb_unchecked_dis = ':/rb_unchecked_dis_d.png',
    rb_checked = ':/rb_checked_d.png',
    rb_checked_dis = ':/rb_checked_dis_d.png'
)
qss14ImagesLight = dict(
    cb_unchecked = ':/cb_unchecked_l.png',
    cb_unchecked_dis = ':/cb_unchecked_dis_l.png',
    cb_checked = ':/cb_checked_l.png',
    cb_checked_dis = ':/cb_checked_dis_l.png',
    rb_unchecked = ':/rb_unchecked_l.png',
    rb_unchecked_dis = ':/rb_unchecked_dis_l.png',
    rb_checked = ':/rb_checked_l.png',
    rb_checked_dis = ':/rb_checked_dis_l.png'
)
# houdini QSS Style
def qss13():
    '''
    custom Qt qss for houdini 13. Black theme only
    '''
    s = '''/******* QWidget ********/

QWidget
{
    color: #b1b1b1;
    background-color:#3a3a3a;
}

QWidget:disabled
{
    color: #b1b1b1;
    background-color: #252525;
}

QAbstractScrollArea,QTableView
{
 border: 1px solid #222;
}

/************** QMainWindow *************/

QMainWindow::separator
{
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161616, stop: 0.5 #151515, stop: 0.6 #212121, stop:1 #343434);
    color: white;
    padding-left: 4px;
    border: 1px solid #4c4c4c;
    spacing: 2px; 
}

QMainWindow::separator:hover
{

    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d7801a, stop:0.5 #b56c17 stop:1 #ffa02f);
    color: white;
    padding-left: 4px;
    border: 1px solid #6c6c6c;
    spacing: 3px; 
}


/************** QToolTip **************/

QToolTip
{
     border: 1px solid black;
     background-color: #000;
     padding: 1px;
     padding-left: 4px;
     padding-right: 4px;
     border-radius: 3px;
     color: white;
     opacity: 100;
}

/***************** QMenuBar *************/

QMenuBar::item
{
    background: transparent;
}

QMenuBar::item:selected
{
    background-color: #555555;
    color: #fff;
}

QMenuBar::item:pressed
{
    background: #444;
    border: 1px solid #000;
    background-color: QLinearGradient(
        x1:0, y1:0,
        x2:0, y2:1,
        stop:1 #212121,
        stop:0.4 #343434
    );
    margin-bottom:-1px;
    padding-bottom:1px;
}

/**************** QMenu **********/

QMenu
{
    border: 1px solid #000;
}

QMenu::item
{
    background-color: #3a3a3a;
    padding: 2px 20px 2px 20px;
    margin-left: 14px;
}

QMenu::item:selected
{
    color: #fff;
    background-color: #555555;
}

QMenu::separator
{
    height: 2px;
    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161616, stop: 0.5 #151515, stop: 0.6 #212121, stop:1 #343434);
    color: white;
    padding-left: 4px;
    margin-left: 20px;
    margin-right: 5px;
}



/************* QAbstractItemView ***********/

QAbstractItemView
{
    background-color: #353535;
    alternate-background-color: #323232;
    outline: 0;
    height: 20px;
}


/************ QTreeView **********/

QTreeView::item:alternate,
QListView::item:alternate  {
     background-color: #323232;
 }

QTreeView::branch:has-siblings:!adjoins-item
{
    border-image: url(:/vline.png) 0;
}
QTreeView::branch:has-siblings:adjoins-item
{
    border-image: url(:/more.png) 0;
}
QTreeView::branch:!has-children:!has-siblings:adjoins-item
{
    border-image: url(:/end.png) 0;
}

QTreeView::branch:closed:has-children:has-siblings
{
    border-image: url(:/closed.png) 0;
}

QTreeView::branch:closed:has-children:!has-siblings
{
    border-image: url(:/closed_end.png) 0;
}

QTreeView::branch:open:has-children:!has-siblings
{
    border-image: url(:/open_end.png) 0;
}

QTreeView::branch:open:has-children:has-siblings
{
    border-image: url(:/open.png) 0;
}

/********************* QListView ************/

QListView::item,
QTreeView::item 
{
    color: rgb(220,220,220);
    border-color: rgba(0,0,0,0);
    border-width: 1px;
    border-style: solid;
}

QListView::item:selected,
QTreeView::item:selected
{
    background: #605132;
    border-color: #b98620;
 }

/*************** QTableView ********/

QHeaderView::section
{
   background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #393939, stop: 1 #272727);
   color: #b1b1b1;
   border: 1px solid #191919;
   border-top-width: 0px;
   border-left-width: 0px;
   padding-left: 10px;
   padding-right: 10px;
   padding-top: 3px;
   padding-bottom: 3px;

}
QTableView {
    alternate-background-color: #2e2e2e
}

QTableView::item:selected {
    background: #605132;
    border: 1px solid #b98620;

    color: rgb(220,220,220);
 }

QTableView QTableCornerButton::section {
     background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #393939, stop: 1 #272727);
     border: 1px solid #191919;
     border-top-width: 0px;
     border-left-width: 0px;
 }

/*************** QlineEdit ************/

QLineEdit,QDateEdit,QDateTimeEdit,QSpinBox
{
    background-color: #000;
    padding: 1px;
    border-style: solid;
    border: 2px solid #2b2b2b;
    border-radius: 0;
    color:rgb(255,255,255);
    min-height: 18px;
    selection-background-color: rgb(185,134,32);
    selection-color: rgb(0,0,0);
}


/*************** QPushButton ***********/

QPushButton
{
    color: #b1b1b1;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #535353, stop: 0.1 #515151, stop: 0.5 #474747, stop: 0.9 #3d3d3d, stop: 1 #3a3a3a);
    border: 2px solid #232323;
    border-top-width: 2px;
    border-left-width: 2px;
    border-top-color:  QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #101010, stop: 1 #818181);
    border-left-color:  QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #101010, stop: 1 #818181);
    border-radius: 0;
    padding: 3px;
    font-size: 12px;
    padding-left: 10px;
    padding-right: 10px;
}


QPushButton:disabled
{
    background-color:   #424242;
    border: 2px solid #313131;
    border-top-width: 2px;
    border-left-width: 2px;
    border-top-color:  QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #151515, stop: 1 #777777);
    border-left-color:  QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #151515, stop: 1 #777777);
    color: #777;
}

QPushButton:checked
{   
    border-color: #000;
    background-color: #2d2d2d;
    color: #cacaca;
    border-width: 1px;
}

 QPushButton:hover
{   
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #606060, stop: 0.1 #585858, stop: 0.5 #545454, stop: 0.9 #3d3d3d, stop: 1 #3a3a3a);

}
QPushButton:pressed
{
    background-color: #af8021;
    color: #fff;
}
/*********** QScrollBar ***************/

QScrollBar:horizontal {
     border: 1px solid #222222;
     background: #222;
     height: 15px;
     margin: 0px 14px 0 14px;
}
QScrollBar:vertical
{
      border: 1px solid #222222;
      background: #222;
      width: 15px;
      margin: 14px 0 14px 0;
      border: 1px solid #222222;
}

QScrollBar::handle:vertical
{
    background:  QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #535353, stop: 0.1 #515151, stop: 0.5 #474747, stop: 0.9 #3d3d3d, stop: 1 #3a3a3a);
    min-height: 20px;
    border-radius: 0px;
    border: 1px solid #222222;
    border-left-width: 0px;
    border-right-width: 0px;
}
QScrollBar::handle:horizontal
{
      background:  QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #535353, stop: 0.1 #515151, stop: 0.5 #474747, stop: 0.9 #3d3d3d, stop: 1 #3a3a3a);
    min-height: 20px;
    border-radius: 0px;
    border: 1px solid #222222;
    border-top-width: 0px;
    border-bottom-width: 0px;
}


QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal 
{
      border: 1px solid #1b1b19;
      border-radius: 0px;
      background:QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #535353, stop: 0.1 #515151, stop: 0.5 #474747, stop: 0.9 #3d3d3d, stop: 1 #3a3a3a);
      width: 14px;
      subcontrol-origin: margin;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical
{
      border: 1px solid #1b1b19;
      border-radius: 1px;
      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #535353, stop: 0.1 #515151, stop: 0.5 #474747, stop: 0.9 #3d3d3d, stop: 1 #3a3a3a);
      height: 14px;
      subcontrol-origin: margin;
}
QScrollBar::add-line:horizontal:pressed, QScrollBar::sub-line:horizontal:pressed ,
QScrollBar::add-line:vertical:pressed, QScrollBar::sub-line:vertical:pressed
{
      background:  #5b5a5a;
}

QScrollBar::sub-line:vertical
{
      subcontrol-position: top;
}
QScrollBar::add-line:vertical
{
      subcontrol-position: bottom;
}

QScrollBar::sub-line:horizontal 
{
     subcontrol-position: left;
}
QScrollBar::add-line:horizontal
{
      subcontrol-position: right;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
{
      background: none;
}

QScrollBar::up-arrow:vertical
{
     border-image: url(:/arrow_up.png) 1;
}
QScrollBar::down-arrow:vertical
{
     border-image: url(:/arrow_down.png) 1;
}
QScrollBar::right-arrow:horizontal
{
     border-image: url(:/arrow_right.png) 1;
}
QScrollBar::left-arrow:horizontal
{
     border-image: url(:/arrow_left.png) 1;
}


QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
{
      background: none;
}
/********* QSlider **************/

QSlider::groove:horizontal {
    border: 1px solid #000;
    background: #000;
    height: 3px;
    border-radius: 0px;
}

QSlider::sub-page:horizontal {
    background:  #404040;
    border: 1px solid #000;
    height: 10px;
    border-radius: 0px;
}


QSlider::add-page:horizontal {
    background: #626262;
    border: 1px solid #000;
    height: 10px;
    border-radius: 0px;
}


QSlider::handle:horizontal {
background: qlineargradient(x1:0, y1:0, x2:1, y2:1,   stop:0 #696969, stop:1 #505050);
border: 1px solid #000;
width: 5px;
margin-top: -8px;
margin-bottom: -8px;
border-radius: 0px;
}

QSlider::hover
{
    background: #3f3f3f;	
}

QSlider::groove:vertical {
border: 1px solid #ffaa00;
background: #ffaa00;
width: 3px;
border-radius: 0px;
}


QSlider::add-page:vertical {
background: qlineargradient(x1: 0, y1: 0,    x2: 0, y2: 1,   stop: 0 #ffaa00, stop: 1 #ffaa00);
background:#404040;
border: 1px solid #000;
width: 8px;
border-radius: 0px;
}

QSlider::sub-page:vertical {
background: #626262;
border: 1px solid #000;
width: 8px;
border-radius: 0px;
}


QSlider::handle:vertical {
background: qlineargradient(x1:0, y1:0, x2:1, y2:1,   stop:0 #696969, stop:1 #505050);
border: 1px solid #000;
height: 5px;
margin-left: -8px;
margin-right: -8px;
border-radius: 0px;
}

/* disabled */

QSlider::sub-page:disabled, QSlider::add-page:disabled 
{
border-color: #3a3a3a;
background: #414141;
border-radius: 0px;
}
QSlider::handle:disabled {
background: #3a3a3a;
border: 1px solid #242424;

}

QSlider::disabled {
background: #3a3a3a;
}


/********* QProgressBar ***********/
QProgressBar
{
    border: 1px solid #6d6c6c;
    border-radius: 0px;
    
    text-align: center;
    background:#262626;
    color: gray;
    border-bottom: 1px #545353;
}

QProgressBar::chunk
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, 
	stop: 0 #f0d66e,
	stop: 0.09 #f0d66e,
	stop: 0.1 #ecdfa8, 
	stop: 0.7 #d9a933, 
	stop: 0.91 #b88822);

}

/************ QComboBox ************/

QComboBox
{
    selection-background-color: #ffaa00;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #515151,  stop: 0.5 #484848, stop: 1 #3d3d3d);
    border-style: solid;
    border: 1px solid #000;
    border-radius: 0;
    padding-left: 9px;
    min-height: 20px;
    font: 10pt;

}

QComboBox:hover
{
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #555555,  stop: 0.5 #4d4d4d, stop: 1 #414141);
   /* font: 14pt;*/
}

QComboBox:on
{
    background-color: #b98620;
    color:#fff;
    selection-background-color: #494949;
}

QComboBox::drop-down
{
     subcontrol-origin: padding;
     subcontrol-position: top right;
     width: 25px;
     background-color:QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #3d3d3d,  stop: 1 #282828);
     border-width: 0px;
 }

QComboBox::down-arrow
{
    image: url(:/arrow_up_down.png);
}

QComboBox QAbstractItemView
{
    background-color: #3a3a3a;
    border-radius: 0px;
    border: 1px solid #101010;
    border-top-color:  #818181;
    border-left-color: #818181;
    selection-background-color: #606060;
    padding: 2px;

}

QComboBox QAbstractItemView::item 
{
    margin-top: 3px;
}

QListView#comboListView {
    background: rgb(80, 80, 80);
    color: rgb(220, 220, 220);
    min-height: 90px;
    margin: 0 0 0 0;
}

QListView#comboListView::item {
    background-color: rgb(80, 80, 80);
}

QListView#comboListView::item:hover {
    background-color: rgb(95, 95, 95);
}


/************ QCheckBox *********/

QCheckBox::indicator:unchecked {
    background:black;
    image: url(:/cb_unchecked_d.png);
}
QCheckBox::indicator:checked {
    image: url(:/cb_checked_d.png);
}
QCheckBox::indicator:unchecked:disabled {
    background:black;
    image: url(:/cb_unchecked_dis_d.png);
}
QCheckBox::indicator:checked:disabled {
    image: url(:/cb_checked_dis_d.png);
}


/****** QRadioButton ***********/

QRadioButton::indicator:unchecked 
{
    image: url(:/rb_unchecked_d.png);
}

QRadioButton::indicator:checked 
{
    image: url(:/rb_checked_d.png);
}

QRadioButton::indicator:unchecked:disabled
{
    image: url(:/rb_unchecked_dis_d.png);
}

QRadioButton::indicator:checked:disabled
{
    image: url(:/rb_checked_dis_d.png);
}

/****** QTabWidget *************/


QTabWidget::pane  { 
    border: 1px solid #111111;
    margin-top:-1px; /* hide line under selected tab*/

}

QTabWidget::tab-bar  {
    left: 0px; /* move to the right by 5px */
}
 
QTabBar::tab  {
    border: 1px solid #111;
    border-radius: 0px;
    min-width: 15ex;
    padding-left: 3px;
    padding-right: 5px;
    padding-top: 3px;
    padding-bottom: 2px;
    background-color:QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #313131,  stop: 1 #252525);
     
}

QTabBar::tab:selected  {
    border-bottom: 0px;
    background-color:QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4b4b4b,  stop: 1 #3a3a3a)
}

 
QTabBar::tab:only-one  {
    margin: 0;
}

/************** QGroupBox *************/
 QGroupBox {
    border-left-color:QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #4b4b4b,  stop: 1 #3a3a3a);
    border-right-color:QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #111,  stop: 1 #3a3a3a);
    border-top-color:QLinearGradient( x1: 0, y1: 0, x2: 0, y2:1, stop: 0 #4b4b4b,  stop: 1 #3a3a3a);
    border-bottom-color:QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #111,  stop: 1 #3a3a3a);
    border-width: 2px; 
    border-style: solid; 
    border-radius: 0px;
    padding-top: 10px;
}
QGroupBox::title { 
    background-color: transparent;
     subcontrol-position: top left;
     padding:4 10px;
 } 


/************************ QSpinBox *******************/
/*,QDoubleSpinBox*/

QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button  {
    /*background:QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #535353, stop: 1 #3a3a3a);*/
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    /*border: 1px solid #333;*/
} 
QSpinBox::down-button, QDoubleSpinBox::down-button,  QTimeEdit::down-button{
   /* background:QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #535353, stop: 1 #3a3a3a);*/
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
   /* border: 1px solid #333;*/
}

QSpinBox::down-button,QDoubleSpinBox::down-button,  QTimeEdit::down-button,
QSpinBox::up-button, QDoubleSpinBox::up-button,QTimeEdit::up-button 
{
    color: #b1b1b1;
    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #535353, stop: 0.1 #515151, stop: 0.5 #474747, stop: 0.9 #3d3d3d, stop: 1 #3a3a3a);
    border: 2px solid #232323;
    border-top-width: 2px;
    border-left-width: 2px;
    border-top-color:  QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #101010, stop: 1 #818181);
    border-left-color:  QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #101010, stop: 1 #818181);
    border-radius: 0;

}


QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QSpinBox::down-button:pressed,
QTimeEdit::up-button:pressed ,QDoubleSpinBox::up-button:pressed , QTimeEdit::down-button:pressed 
{
    background-color: #828282;
}

QSpinBox::up-button, QDoubleSpinBox::up-button  {
    image: url(:/spin_up.png);
}

QSpinBox::down-button, QDoubleSpinBox::down-button  {
    image: url(:/spin_down.png);
}


QPlainTextEdit, QTextEdit {
    background: #000;
    color: white;
}
QTextBrowser {
    background-color:#3a3a3a;
}
QTabBar::close-button {
    image: url(:/tab_close.png);
    subcontrol-position: right;
}
QTabBar::close-button:hover {
    image: url(:/tab_close_hover.png);
}

QToolTip {
    color: #ffffff;
    background-color: #2a82da;
    border: 1px solid white;
}

 '''
    return s

# different icons for light and black themes

def qss14():
    '''
    this is fixed copy of default qss houdini\config\Styles\base.qss
    :return: new QSS style
    '''
    s = '''

QWidget
{
    font-family: "DejaVu Sans";
    font-size: 11px;
    color: rgb(@TextColor@);
	background-color: rgb(@BackColor@);
}

QDialog, QFrame, QGroupBox
{
    background: rgb(@BackColor@);
    color: rgb(@TextColor@);
}

QAbstractItemView
{
    alternate-background-color: rgb(@ListEntry2@);
    outline: 0;
    height: 20px;
}

#central_widget
{
    background: rgb(@BackColor@);
    color: rgb(@TextColor@);
}

QStatusBar
{
    background: rgb(@BackColor@);
    color: rgb(@TextColor@);
}

QTextEdit, QPlainTextEdit
{
    background: rgb(@TextboxBG@);
    color: rgb(@TextColor@);
    selection-background-color: rgb(@SelectedTextBG@);
    selection-color: rgb(@SelectedTextFG@);
}

QTextEdit#code_edit
{
    background: rgb(@ButtonGradHi@);
    font-size: 15px;
    border: none;
}

QCheckBox
{
    background: rgb(@BackColor@);
}

QCheckBox::indicator:unchecked {
    image: url($cb_unchecked$);
}
QCheckBox::indicator:checked {
    image: url($cb_checked$);
}
QCheckBox::indicator:unchecked:disabled {
    image: url($cb_unchecked_dis$);
}
QCheckBox::indicator:checked:disabled {
    image: url($cb_checked_dis$);
}

QRadioButton::indicator:unchecked
{
    image: url($rb_unchecked$);
}
QRadioButton::indicator:checked
{
    image: url($rb_checked$);
}
QRadioButton::indicator:unchecked:disabled
{
    image: url($rb_unchecked_dis$);
}
QRadioButton::indicator:checked:disabled
{
    image: url($rb_checked_dis$);
}
QCheckBox:disabled,QRadioButton:disabled {
    color: rgb(@DisabledTextColor@);
}
QSplitter::handle
{
    background-color: rgb(@BackColor:Brightness=1.2@);
    margin:2px;
}

QSplitter::handle:horizontal
{
    width: 1px;
}

QSplitter::handle:vertical
{
    height: 1px;
}

QSplitter::handle:pressed
{
    background-color: rgb(@SplitBarHighlight@);
}


QSplitter::handle:hover
{
    background-color: rgb(@SplitBarHighlight@);
}

QLineEdit,QDateEdit,QDateTimeEdit,QSpinBox
{
    border: 1px solid rgb(@TextboxBorderPrimary@);
    border-radius: 2px;
    padding: 2px 4px;
    background: rgb(@TextboxBG@);
    selection-color: rgb(@SelectedTextFG@);
    selection-background-color: rgb(@SelectedTextBG@);
}

QLineEdit:disabled,QDateEdit:disabled,QDateTimeEdit:disabled,QSpinBox:disabled
{
    border: 1px solid rgba(@TextboxBorderPrimary@, 40);
    border-radius: 2px;
    padding: 2px 4px;
    background: rgba(@TextboxBG@, 40);
    color: rgb(@DisabledTextColor@);
}

QLineEdit[invalid="true"]
{
    background: rgb(@TextboxInvalidBG@);
}

QLabel:enabled
{
    color: rgb(@TextColor@);
}

#big_text
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@BackColor@));
    font-size: 16px;
    font-weight: bold;
    padding: 10px;
    border: none;
    border-bottom: 2px solid rgb(@ToolbarBevelLight@);
    height: 20px;
    margin-left: -1px;
}

QPushButton:pressed#big_text
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonPressedGradHi@),
				stop: 1.0 rgb(@ButtonPressedGradLow@));
    color: rgb(@ButtonPressedText@);
}

QPushButton:hover#big_text
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi:Brightness=1.05@),
				stop: 1.0 rgb(@ButtonGradLow:Brightness=1.05@));
}

QPushButton
{
    border: 1px solid rgb(@BorderLight@);
    border-radius: 1px;
    padding-top: 4px;
    padding-bottom: 4px;
    padding-right: 15px;
    padding-left: 15px;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
}

QRadioButton
{
    margin: 5px;
}

QToolButton
{
    border: 1px solid rgb(@BorderLight@);
    border-radius: 0px;
    padding-top: 2px;
    padding-bottom: 2px;
    padding-right: 3px;
    padding-left: 3px;
    margin: 1px;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
}

QPushButton:hover, QToolButton:hover
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi:Brightness=1.05@),
				stop: 1.0 rgb(@ButtonGradLow:Brightness=1.05@));
}

QPushButton:pressed, QToolButton:pressed
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonPressedGradHi@),
				stop: 1.0 rgb(@ButtonPressedGradLow@));
    color: rgb(@ButtonPressedText@);
}

QPushButton:checked, QToolButton:checked
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonPressedGradHi:Brightness=0.75@),
				stop: 1.0 rgb(@ButtonPressedGradLow:Brightness=0.75@));
    color: rgb(@ButtonPressedText@);
}



QPushButton:disabled, QToolButton:disabled
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgba(@ButtonGradHi@, 40),
				stop: 1.0 rgba(@ButtonGradLow@, 40));
    color: rgb(@DisabledTextColor@);
}

QPushButton:flat:hover:!pressed, QToolButton:flat:hover:!pressed
{
      background: rgb(@ButtonGradHi@);
}

QPushButton:flat::pressed, QToolButton:flat::pressed
{
      background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonPressedGradHi@),
				stop: 1.0 rgb(@ButtonPressedGradLow@));
}


QPushButton:flat:!pressed, QToolButton:flat:!pressed
{
      border: none;
      background: rgb(@BackColor@);
}

QToolButton[transparent="true"]
{
    background: none;
    border: none;
}

QToolButton[transparent="true"]:hover
{
    background:black;
    border: outset 1px;
}

QToolButton[transparent="true"]:pressed
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonPressedGradHi@),
				stop: 1.0 rgb(@ButtonPressedGradLow@));
    color: rgb(@ButtonPressedText@);
}

QToolButton[transparent="true"]:disabled
{
    background: none;
    border: none;
}

QAbstractScrollArea,QTableView
{
 border: none;
}

QTableView
{
    alternate-background-color: rgb(@ListEntry2@);
    background: rgb(@ListEntry1@);
    selection-background-color: rgba(@ListEntrySelected@, 77);
    selection-color: rgb(@SelectedTextFG@);
    color: rgb(@ListText@);
    border: none;
}

QTableView::item
{
    border-right: 1px solid rgb(@ListBorder@);
    border-left: 0;
    border-top: 0;
    border-bottom: 0;
    outline: none;
}

QTableView::item:selected
{
    border-top: 1px solid rgb(@ListEntrySelected@);
    border-bottom: 1px solid rgb(@ListEntrySelected@);
    color: rgb(@TextColor@);
    background: rgba(@ListEntrySelected@, 77);
    outline: none;
}



QTreeView, QListView, QTableView
{
    alternate-background-color: rgb(@ListEntry2@);
    background: rgb(@ListEntry1@);
    selection-background-color: rgba(@ListEntrySelected@, 77);
    /*selection-color: rgb(@SelectedTextFG@);*/
    color: rgb(@ListText@);
    border-top: 0;
    border-bottom: 1px solid rgb(@ListBorder@);
    border-left: 1px solid rgb(@ListBorder@);
    border-right: 1px solid rgb(@ListBorder@);
}
QListView, QTableView{
    border-top: 1px solid rgb(@ListBorder@);
}
QTreeView::item, QListView::item
{
    border-right: 1px solid rgb(@ListBorder@);
    border-left: 0;
    border-top: 0;
    border-bottom: 0;
    height: 20px;
}

QTreeView::item:selected, QListView::item:selected
{
    border-top: 1px solid rgb(@ListEntrySelected@);
    border-bottom: 1px solid rgb(@ListEntrySelected@);
    color: rgb(@TextColor@);
    background: rgba(@ListEntrySelected@, 77);
    outline: none;
}

QHeaderView::section, QTableCornerButton::section
{
    border: 1px solid rgb(@ListTitleShadow@);
    border-top: 1;
    border-left: 0;
    padding: 4px;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ListTitleGradHi@),
				stop: 1.0 rgb(@ListTitleGradLow@) );
}

QTabWidget
{
    background: rgb(@BackColor@);
    border: none;
}

QTabBar
{
    background: rgb(@BackColor@);
    border: none;
}

QTabWidget
{
    background: rgb(@BackColor@);
}

QTabWidget::pane
{
    border: 1px solid rgb(@PaneTabShadow@);
    background: rgb(@BackColor@);
}

QTabWidget::tab-bar
{
    alignment: left;
    left: 1px;
    border: none;
    background: rgb(@BackColor@);
}

QTabBar::tab
{
    padding-left: 6px;
    padding-right: 6px;
    padding-top: 2px;
    padding-bottom: 2px;
    height: 18px;
    margin-top: 1px;
    margin-left: -1px;
    border: 1px solid rgb(@PaneTabInactiveHi:Brightness=0.75@);
    border-radius: 0px;
    background: rgb(@PaneTabInactiveHi@);
}

QTabBar[webbrowser="true"]::tab
{
    width: 100px;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    border-bottom-left-radius: 0px;
    border-bottom-right-radius: 0px;
}

QTabBar[webbrowser="true"]::tab:last
{
    border-color: rgb(@PaneTabInactiveLow@);
    border-radius: 0px;
    background: none;
}

QTabBar::tab:selected
{
    border: 2px solid rgb(@PaneTabInactiveLow@);
    border-bottom: 0;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@PaneTabActiveHi@),
				stop: 1.0 rgb(@BackColor@));
}

QTabBar[webbrowser="true"]::close-button
{
    subcontrol-position: right;
    image: url(:/BUTTONS/delete.svg);
    width: 8px;
    height: 8px;
    margin: 4px;
}
QTabBar::close-button
{
    subcontrol-position: right;
    image: url(:/BUTTONS/delete.svg);
    width: 8px;
    height: 8px;
    margin: 4px;
}

QTabBar::close-button:hover
{
    background: rgb(@ButtonMenuArrow@);
}

QMenu
{
    background-color: rgb(@MenuBG@);
    border-top: 1px solid rgb(@MenuHighlight@);
    border-left: 1px solid rgb(@MenuHighlight@);
    border-bottom: 1px solid rgb(@MenuShadow@);
    border-right: 1px solid rgb(@MenuShadow@);
    padding: 0px;
}

QMenu::item
{
    padding: 2px 15px 2px 20px;
    margin-left: 1px;
    margin-right: 1px;

}

QMenuBar::item
{
    background: transparent;
    padding: 4px;
}

QMenu::item:selected:!disabled
{
    background-color: rgb(@MenuSelectedBG@);
    color: rgb(@MenuTextSelected@);
}

QMenu::item:disabled
{
    color: rgb(@MenuTextDisabled@);
}

QMenu::tearoff
{
    background-color: rgb(@MenuBG@);
    border: none;
}
QMenu::tearoff:selected
{
    background-color: rgb(@MenuSelectedBG@);
}

QMenuBar
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@MenuBG@),
				stop: 1.0 rgb(@MenuBG:Brightness=0.85@));
    border: 1px solid rgb(@BorderLight@);
}
QMenuBar::item:pressed
{
    background: rgb(@MenuSelectedBG@);
    color: rgb(@MenuTextSelected@);
}

QProgressBar
{
    border-top: 1px solid rgb(@ProgressMeterTopBorder@);
    border-bottom: 1px rgb(@ProgressMeterBottomBorder@);
    border-radius: 0px;

    text-align: center;
    background: rgb(@ProgressMeterWellGradLo@);
    color: rgb(@ProgressMeterText@);
}

QProgressBar::chunk
{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
	stop:0 rgb(@ProgressMeterGradHi@),
	stop:0.07 rgb(@ProgressMeterGradLo@),
	stop:0.8 rgb(@ProgressMeterGradLo:Brightness=0.7@),
	stop:0.95 rgb(@ProgressMeterGradLo:Brightness=0.65@),
	stop:1.0 rgb(@ProgressMeterGradLo:Brightness=0.4@));
}

QScrollBar:horizontal
{
    border: 1px solid rgb(@ScrollbarUpperBorder@);
    background: rgb(@ScrollbarWell@);
    height: 15px;
    margin: 0 17px 0 17px;
}

QScrollBar::handle:horizontal
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
    min-width: 30px;
}

QScrollBar::add-line:horizontal
{
    border: 1px solid rgb(@ScrollbarUpperBorder@);

    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
    width: 15px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal
{
    border: 1px solid rgb(@ScrollbarUpperBorder@);

    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
    width: 15px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}

QScrollBar::left-arrow:horizontal
{
    width: 0;
    height: 0;
    border-top: 3px solid rgb(@ButtonGradHi@);
    border-bottom: 3px solid rgb(@ButtonGradHi@);
    border-right: 5px solid rgb(@ScrollArrow@);
}

QScrollBar::right-arrow:horizontal
{
    width: 0;
    height: 0;
    border-top: 3px solid rgb(@ButtonGradHi@);
    border-bottom: 3px solid rgb(@ButtonGradHi@);
    border-left: 5px solid rgb(@ScrollArrow@);
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal
{
    background: none;
}

QScrollBar:vertical
{
    border: 1px solid rgb(@ScrollbarUpperBorder@);
    background: rgb(@ScrollbarWell@);
    width: 15px;
    margin: 17px 0 17px 0;
}
QScrollBar:horizontal
{
    border: 1px solid rgb(@ScrollbarUpperBorder@);
}

QScrollBar::handle:vertical
{
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
    min-height: 30px;
}

QScrollBar::add-line:vertical
{
    border: 1px solid rgb(@ScrollbarUpperBorder@);

    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
    height: 15px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical
{
    border: 1px solid rgb(@ScrollbarUpperBorder@);

    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
    height: 15px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}

QScrollBar::up-arrow:vertical
{
    width: 0;
    height: 0;
    border-left: 3px solid rgba(@ButtonGradHi@, 0);
    border-right: 3px solid rgba(@ButtonGradHi@, 0);
    border-bottom: 5px solid rgb(@ScrollArrow@);
}

QScrollBar::down-arrow:vertical
{
    width: 0;
    height: 0;
    border-left: 3px solid rgba(@ButtonGradHi@, 0);
    border-right: 3px solid rgba(@ButtonGradHi@, 0);
    border-top: 5px solid rgb(@ScrollArrow@);
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical
{
    background: none;
}

QSlider
{
    height: 20px;
}

QSlider::groove::horizontal
{
    border-top: 1px solid rgb(@SliderTopBorder@);
    border-bottom: 1px solid rgb(@SliderBottomBorder@);
    border-radius: 1px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0.4 rgb(@SliderRemainingBevel@),
				stop:0.5 rgb(@SliderRemainingGroove@));
    height: 3px;
    margin: 2px 0;
}

QSlider::handle:horizontal
{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0 rgb(@ButtonGradHi@),
				stop:1 rgb(@ButtonGradLow@));
    border-top: 1px solid rgb(@SliderThumbTopBorder@);
    border-left: 1px solid rgb(@SliderThumbTopBorder@);
    border-right: 1px solid rgb(@SliderThumbBottomBorder@);
    border-bottom: 1px solid rgb(@SliderThumbBottomBorder@);
    width: 4px;
    margin: -8px 0;
    border-radius: 1px;
}

QSlider::sub-page:horizontal
{
    border-top: 1px solid rgb(@SliderTopBorder@);
    border-bottom: 1px solid rgb(@SliderBottomBorder@);
    border-radius: 1px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0.4 rgb(@SliderAdvancedBevel@),
				stop:0.5 rgb(@SliderAdvancedGroove@));
    height: 3px;
    margin: 2px 0;
}

QTreeView::branch:has-siblings:!adjoins-item
{
    border-image: url(:/vline.png) 0;
}
QTreeView::branch:has-siblings:adjoins-item
{
    border-image: url(:/more.png) 0;
}
QTreeView::branch:!has-children:!has-siblings:adjoins-item
{
    border-image: url(:/end.png) 0;
}

QTreeView::branch:closed:has-children:has-siblings
{
    border-image: url(:/closed.png) 0;
}

QTreeView::branch:closed:has-children:!has-siblings
{
    border-image: url(:/closed_end.png) 0;
}

QTreeView::branch:open:has-children:!has-siblings
{
    border-image: url(:/open_end.png) 0;
}

QTreeView::branch:open:has-children:has-siblings
{
    border-image: url(:/open.png) 0;
}

QGroupBox
{
    border: 1px solid rgb(@ToolbarBevelLight@);
    border-radius: 4px;
    padding: 7 -1 px;
    margin-top: 1ex;
    margin-bottom: 1.5ex;
}
QGroupBox::title {
    subcontrol-position: top left;
    subcontrol-origin: margin;
    padding: -6 6 -5 px;
    margin: 0 0 0 5 px;
    left: 15px;
 }


QSpinBox, QDoubleSpinBox, QTimeEdit {
 border-radius: 2px;

}

QSpinBox::up-button, QDoubleSpinBox::up-button, QTimeEdit::up-button  {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    border: 1px solid rgb(@TextboxBorderPrimary@);
    border-top-right-radius: 2px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button,  QTimeEdit::down-button{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    border: 1px solid rgb(@TextboxBorderPrimary@);
    border-bottom-right-radius: 2px;
}

QSpinBox::down-button,QDoubleSpinBox::down-button,  QTimeEdit::down-button,
QSpinBox::up-button, QDoubleSpinBox::up-button,QTimeEdit::up-button
{
    /*border: 1px solid rgb(@ButtonShadow@);
    border-radius: 0px;*/
    padding-top: 1px;
    padding-bottom: 1px;
    padding-right: 1px;
    padding-left: 1px;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));

}


QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed, QSpinBox::down-button:pressed,
QTimeEdit::up-button:pressed ,QDoubleSpinBox::up-button:pressed , QTimeEdit::down-button:pressed
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonPressedGradHi@),
				stop: 1.0 rgb(@ButtonPressedGradLow@));
    color: rgb(@ButtonPressedText@);
}

QSpinBox::up-button, QDoubleSpinBox::up-button  {
    image: url(:/spin_up.png);
}

QSpinBox::down-button, QDoubleSpinBox::down-button  {
    image: url(:/spin_down.png);
}
QComboBox
{
    border: 1px solid rgba(@ButtonShadow@, 102);
    border-radius: 1px;
    padding-top: 4px;
    padding-bottom: 4px;
    padding-right: 15px;
    padding-left: 15px;
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonGradHi@),
				stop: 1.0 rgb(@ButtonGradLow@));
}

QComboBox:hover
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonMenuArrow@),
				stop: 1.0 rgb(@ButtonGradLow@));
}

QComboBox::drop-down, QDateEdit::drop-down,QDateTimeEdit::drop-down
{
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
				stop: 0.0 rgb(@ButtonMenuArrowHi@),
				stop: 1.0 rgb(@ButtonMenuArrowLow@));
    width: 20px;
}

QComboBox::down-arrow, QDateEdit::down-arrow,QDateTimeEdit::down-arrow
{
    width: 0;
    height: 0;
    border-left: 3px solid rgba(@ButtonMenuArrowHi@, 0);
    border-right: 3px solid rgba(@ButtonMenuArrowHi@, 0);
    border-top: 5px solid rgb(@ButtonMenuArrow@);
}

QComboBox QAbstractItemView
{
    background-color: rgb(@MenuBG@);
    border-top: 1px solid rgb(@BackColor@);
    border-left: 1px solid rgb(@ButtonGradHi@);
    border-bottom: 1px solid rgb(@ButtonMenuArrowLow@);
    border-right: 1px solid rgb(@ButtonMenuArrowLow@);
    padding: 3px;
    outline: none;
    selection-background-color: rgb(@MenuSelectedBG@);
}


QComboBox QAbstractItemView:item
{
    padding: 4px 15px 4px 15px;
    selection-background-color: rgb(@MenuSelectedBG@);
    border-radius: 0px;
    color: rgb(@MenuTextSelected@);

}
QComboBox:on
{
    background-color: rgb(@ButtonPressedGradHi@);
    color: rgb(@ButtonPressedText@);
}
QToolBar {
    border: 1px solid rgb(@ProgressMeterBottomBorder@);
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0.0 rgb(@BackColor:Brightness=1.2@),
				stop:1.0 rgb(@BackColor@));
}
QToolBar::handle:horizontal {
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
				stop:0.0 rgb(@PaneTabShadow@),
				stop:0.2 rgb(@BackColor:Brightness=1.8@),
				stop:0.4 transparent
				);
  width: 10px;
}
QToolBar::handle:vertical {
  background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0.0 rgb(@PaneTabShadow@),
				stop:0.2 rgb(@BackColor:Brightness=1.8@),
				stop:0.4 transparent
				);
  height: 10px;
}
QToolBar::separator:horizontal {
  width: 2;
  margin: 2px;
  background: rgb(@BackColor:Brightness=0.8@);
}
QToolBar::separator:vertical {
  height: 2;
  margin: 2px;
  background: rgb(@BackColor:Brightness=0.8@);
}
QToolBar QToolButton {
	background: transparent;
	border: none;
	border-radius: 0px;
}
QToolBar QToolButton:hover {
	background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0.0 rgb(@BackColor:Brightness=1.3@),
				stop:1.0 rgb(@BackColor@));
}
QToolBar QToolButton:pressed {
	background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
				stop:0.0 rgb(@BackColor:Brightness=0.9@),
				stop:1.0 rgb(@BackColor:Brightness=0.6@));
}
'''
    return s

# QToolBar::handle:horizontal {
#   background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
# 				stop:0.0 rgb(@PaneTabShadow@),
# 				stop:0.2 rgb(@BackColor:Brightness=1.6@),
# 				stop:0.6 rgb(@BackColor:Brightness=1.5@),
# 				stop:0.8 rgb(@BackColor@),
# 				stop:0.9 rgb(@PaneTabShadow@)
# 				);
#   width: 10px;
# }
# QToolBar::handle:vertical {
#   background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
# 				stop:0.0 rgb(@PaneTabShadow@),
# 				stop:0.2 rgb(@BackColor:Brightness=1.6@),
# 				stop:0.6 rgb(@BackColor:Brightness=1.5@),
# 				stop:0.8 rgb(@BackColor@),
# 				stop:0.9 rgb(@PaneTabShadow@)
# 				);
#   height: 10px;
# }