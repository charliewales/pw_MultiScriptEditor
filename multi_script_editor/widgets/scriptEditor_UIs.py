# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Dropbox\Dropbox\pw_prefs\RnD\tools\pw_scriptEditor\multi_script_editor\widgets\scriptEditor.ui'
#
# Created: Mon Apr 06 09:46:03 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!


from vendor.Qt.QtCore import * 
from vendor.Qt.QtWidgets import * 
from vendor.Qt.QtGui import * 

class Ui_scriptEditor(object):
    def setupUi(self, scriptEditor):
        scriptEditor.setObjectName("scriptEditor")
        scriptEditor.resize(800, 609)
        self.centralwidget = QWidget(scriptEditor)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setFrameShape(QFrame.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.frame_2.setObjectName("frame_2")
        self.verticalLayout = QVBoxLayout(self.frame_2)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QSplitter(self.frame_2)
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.verticalLayoutWidget = QWidget(self.splitter)
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.out_ly = QVBoxLayout(self.verticalLayoutWidget)
        self.out_ly.setContentsMargins(0, 0, 0, 0)
        self.out_ly.setObjectName("out_ly")
        self.verticalLayoutWidget_2 = QWidget(self.splitter)
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.in_ly = QVBoxLayout(self.verticalLayoutWidget_2)
        self.in_ly.setContentsMargins(0, 0, 0, 0)
        self.in_ly.setObjectName("in_ly")
        self.verticalLayout.addWidget(self.splitter)
        self.verticalLayout_2.addWidget(self.frame_2)
        scriptEditor.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(scriptEditor)
        self.menubar.setGeometry(QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        self.file_menu = QMenu(self.menubar)
        self.file_menu.setTearOffEnabled(True)
        self.file_menu.setObjectName("file_menu")
        self.help_menu = QMenu(self.menubar)
        self.help_menu.setTearOffEnabled(True)
        self.help_menu.setObjectName("help_menu")
        self.tools_menu = QMenu(self.menubar)
        self.tools_menu.setTearOffEnabled(True)
        self.tools_menu.setObjectName("tools_menu")
        self.options_menu = QMenu(self.menubar)
        self.options_menu.setTearOffEnabled(True)
        self.options_menu.setObjectName("options_menu")
        self.theme_menu = QMenu(self.options_menu)
        self.theme_menu.setObjectName("theme_menu")
        self.theme_menu.setTearOffEnabled(True)
        self.run_menu = QMenu(self.menubar)
        self.run_menu.setTearOffEnabled(True)
        self.run_menu.setObjectName("run_menu")
        scriptEditor.setMenuBar(self.menubar)
        self.toolBar = QToolBar(scriptEditor)
        self.toolBar.setObjectName("toolBar")
        scriptEditor.addToolBar(Qt.TopToolBarArea, self.toolBar)
        self.clearHistory_act = QAction(scriptEditor)
        self.clearHistory_act.setObjectName("clearHistory_act")
        self.dir_act = QAction(scriptEditor)
        self.dir_act.setObjectName("dir_act")
        self.help_act = QAction(scriptEditor)
        self.help_act.setObjectName("help_act")
        self.type_act = QAction(scriptEditor)
        self.type_act.setObjectName("type_act")
        self.quick_help_act = QAction(scriptEditor)
        self.quick_help_act.setObjectName("quick_help_act")
        self.save_act = QAction(scriptEditor)
        self.save_act.setObjectName("save_act")
        self.load_act = QAction(scriptEditor)
        self.load_act.setObjectName("load_act")
        self.exit_act = QAction(scriptEditor)
        self.exit_act.setObjectName("exit_act")
        self.openManual_act = QAction(scriptEditor)
        self.openManual_act.setObjectName("openManual_act")
        self.python_act = QAction(scriptEditor)
        self.python_act.setObjectName("python_act")
        self.quickHelp_act = QAction(scriptEditor)
        self.quickHelp_act.setObjectName("quickHelp_act")
        self.qt_docs_act = QAction(scriptEditor)
        self.qt_docs_act.setObjectName("qt_docs_act")
        self.qt_modules_act = QAction(scriptEditor)
        self.qt_modules_act.setObjectName("qt_modules_act")
        self.maya_cmds_act = QAction(scriptEditor)
        self.maya_cmds_act.setObjectName("maya_cmds_act")
        self.houdini_hou_act = QAction(scriptEditor)
        self.houdini_hou_act.setObjectName("houdini_hou_act")
        self.houdini_envs_act = QAction(scriptEditor)
        self.houdini_envs_act.setObjectName("houdini_envs_act")
        self.nuke_dev_guide_act = QAction(scriptEditor)
        self.nuke_dev_guide_act.setObjectName("nuke_dev_guide_act")
        self.saveSeccion_act = QAction(scriptEditor)
        self.saveSeccion_act.setObjectName("saveSeccion_act")
        self.quit_act = QAction(scriptEditor)
        self.quit_act.setObjectName("quit_act")
        self.tabToSpaces_act = QAction(scriptEditor)
        self.tabToSpaces_act.setObjectName("tabToSpaces_act")
        self.spacesToTabs_act = QAction(scriptEditor)
        self.spacesToTabs_act.setObjectName("spacesToTabs_act")
        self.settingsFile_act = QAction(scriptEditor)
        self.settingsFile_act.setObjectName("settingsFile_act")
        self.editTheme_act = QAction(scriptEditor)
        self.editTheme_act.setObjectName("editTheme_act")
        self.shortcuts_act = QAction(scriptEditor)
        self.shortcuts_act.setObjectName("shortcuts_act")
        self.donate_act = QAction(scriptEditor)
        self.donate_act.setObjectName("donate_act")
        self.about_act = QAction(scriptEditor)
        self.about_act.setObjectName("about_act")
        self.execAll_act = QAction(scriptEditor)
        self.execAll_act.setObjectName("execAll_act")
        self.execLine_act = QAction(scriptEditor)
        self.execLine_act.setObjectName("execLine_act")
        self.execSel_act = QAction(scriptEditor)
        self.execSel_act.setObjectName("execSel_act")
        self.out_wordWrap_act = QAction(scriptEditor)
        self.out_wordWrap_act.setObjectName("out_wordWrap_act")
        self.wordWrap_act = QAction(scriptEditor)
        self.wordWrap_act.setObjectName("wordWrap_act")
        self.copy_act = QAction(scriptEditor)
        self.copy_act.setObjectName("copy_act")
        self.cut_act = QAction(scriptEditor)
        self.cut_act.setObjectName("cut_act")
        self.paste_act = QAction(scriptEditor)
        self.paste_act.setObjectName("paste_act")
        self.find_act = QAction(scriptEditor)
        self.find_act.setObjectName("find_act")
        self.undo_act = QAction(scriptEditor)
        self.undo_act.setObjectName("undo_act")
        self.redo_act = QAction(scriptEditor)
        self.redo_act.setObjectName("redo_act")
        self.duplicateLine_act = QAction(scriptEditor)
        self.duplicateLine_act.setObjectName("duplicateLine_act")
        self.deleteLine_act = QAction(scriptEditor)
        self.deleteLine_act.setObjectName("deleteLine_act")
        self.printHelp_act = QAction(scriptEditor)
        self.printHelp_act.setObjectName("printHelp_act")
        self.comment_cat = QAction(scriptEditor)
        self.comment_cat.setObjectName("comment_cat")
        self.file_menu.addAction(self.load_act)
        self.file_menu.addAction(self.save_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.saveSeccion_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.quit_act)
        self.help_menu.addAction(self.donate_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.quick_help_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.openManual_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.houdini_envs_act)
        self.help_menu.addAction(self.houdini_hou_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.maya_cmds_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.nuke_dev_guide_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.qt_docs_act)
        self.help_menu.addAction(self.qt_modules_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.python_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.shortcuts_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.printHelp_act)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_act)
        self.tools_menu.addAction(self.undo_act)
        self.tools_menu.addAction(self.redo_act)
        self.tools_menu.addSeparator()
        self.tools_menu.addAction(self.copy_act)
        self.tools_menu.addAction(self.cut_act)
        self.tools_menu.addAction(self.paste_act)
        self.tools_menu.addAction(self.paste_act)
        self.tools_menu.addSeparator()
        self.tools_menu.addAction(self.deleteLine_act)
        self.tools_menu.addAction(self.duplicateLine_act)
        self.tools_menu.addSeparator()
        self.tools_menu.addAction(self.comment_cat)
        self.tools_menu.addAction(self.find_act)
        self.tools_menu.addAction(self.tabToSpaces_act)
        self.tools_menu.addSeparator()
        self.tools_menu.addAction(self.wordWrap_act)
        self.tools_menu.addAction(self.out_wordWrap_act)
        self.theme_menu.addAction(self.editTheme_act)
        self.theme_menu.addSeparator()
        self.options_menu.addAction(self.theme_menu.menuAction())
        self.options_menu.addSeparator()
        self.options_menu.addAction(self.settingsFile_act)
        self.run_menu.addAction(self.clearHistory_act)
        self.run_menu.addSeparator()
        self.run_menu.addAction(self.dir_act)
        self.run_menu.addAction(self.help_act)
        self.run_menu.addAction(self.type_act)
        self.run_menu.addSeparator()
        self.run_menu.addAction(self.execAll_act)
        self.run_menu.addAction(self.execLine_act)
        self.run_menu.addAction(self.execSel_act)
        self.menubar.addAction(self.file_menu.menuAction())
        self.menubar.addAction(self.tools_menu.menuAction())
        self.menubar.addAction(self.run_menu.menuAction())
        self.menubar.addAction(self.options_menu.menuAction())
        self.menubar.addAction(self.help_menu.menuAction())
        self.toolBar.addAction(self.execAll_act)
        self.toolBar.addAction(self.execLine_act)
        self.toolBar.addAction(self.execSel_act)
        self.toolBar.addAction(self.clearHistory_act)

        self.retranslateUi(scriptEditor)
        QMetaObject.connectSlotsByName(scriptEditor)

    def retranslateUi(self, scriptEditor):
        scriptEditor.setWindowTitle(QApplication.translate("scriptEditor", "MainWindow", None))
        self.file_menu.setTitle(QApplication.translate("scriptEditor", "File", None))
        self.help_menu.setTitle(QApplication.translate("scriptEditor", "Help", None))
        self.tools_menu.setTitle(QApplication.translate("scriptEditor", "Edit", None))
        self.options_menu.setTitle(QApplication.translate("scriptEditor", "Options", None))
        self.theme_menu.setTitle(QApplication.translate("scriptEditor", "Theme", None))
        self.run_menu.setTitle(QApplication.translate("scriptEditor", "Run", None))
        self.toolBar.setWindowTitle(QApplication.translate("scriptEditor", "toolBar", None))
        self.clearHistory_act.setText(QApplication.translate("scriptEditor", "Clear Output", None))
        self.dir_act.setText(QApplication.translate("scriptEditor", "dir()", None))
        self.help_act.setText(QApplication.translate("scriptEditor", "help()", None))
        self.type_act.setText(QApplication.translate("scriptEditor", "type()", None))
        self.maya_cmds_act.setText(QApplication.translate("scriptEditor", "Maya Commands", None))
        self.houdini_hou_act.setText(QApplication.translate("scriptEditor", "Houdini hou package", None))
        self.houdini_envs_act.setText(QApplication.translate("scriptEditor", "Houdini Env Variables", None))
        self.nuke_dev_guide_act.setText(QApplication.translate("scriptEditor", "Nuke Dev Guide", None))
        self.quick_help_act.setText(QApplication.translate("scriptEditor", "Quick Help", None))
        self.qt_docs_act.setText(QApplication.translate("scriptEditor", "Qt for Python", None))
        self.qt_modules_act.setText(QApplication.translate("scriptEditor", "Qt Modules", None))
        self.save_act.setText(QApplication.translate("scriptEditor", "Save Script", None))
        self.load_act.setText(QApplication.translate("scriptEditor", "Load Script", None))
        self.exit_act.setText(QApplication.translate("scriptEditor", "Exit", None))
        self.openManual_act.setText(QApplication.translate("scriptEditor", "GitHub", None))
        self.python_act.setText(QApplication.translate("scriptEditor", "Python documentation", None))
        self.quickHelp_act.setText(QApplication.translate("scriptEditor", "Quick Help", None))
        self.saveSeccion_act.setText(QApplication.translate("scriptEditor", "Save Session", None))
        self.tabToSpaces_act.setText(QApplication.translate("scriptEditor", "Tab to spaces", None))
        self.spacesToTabs_act.setText(QApplication.translate("scriptEditor", "Spaces to tab", None))
        self.settingsFile_act.setText(QApplication.translate("scriptEditor", "Open Settings Folder", None))
        self.editTheme_act.setText(QApplication.translate("scriptEditor", "Edit ...", None))
        self.shortcuts_act.setText(QApplication.translate("scriptEditor", "Shortcuts", None))
        self.donate_act.setText(QApplication.translate("scriptEditor", "Donate", None))
        self.deleteLine_act.setText(QApplication.translate("scriptEditor", "Delete Line", None))
        self.duplicateLine_act.setText(QApplication.translate("scriptEditor", "Duplicate Line", None))
        self.about_act.setText(QApplication.translate("scriptEditor", "About", None))
        self.quit_act.setText(QApplication.translate("scriptEditor", "Quit", None))
        self.execAll_act.setText(QApplication.translate("scriptEditor", "Execute All", None))
        self.execLine_act.setText(QApplication.translate("scriptEditor", "Execute Line", None))
        self.execSel_act.setText(QApplication.translate("scriptEditor", "Execute Selected", None))
        self.wordWrap_act.setText(QApplication.translate("scriptEditor", "Word Wrap", None))
        self.out_wordWrap_act.setText(QApplication.translate("scriptEditor", "Word Wrap (Output)", None))
        self.copy_act.setText(QApplication.translate("scriptEditor", "Copy", None))
        self.cut_act.setText(QApplication.translate("scriptEditor", "Cut", None))
        self.paste_act.setText(QApplication.translate("scriptEditor", "Paste", None))
        self.find_act.setText(QApplication.translate("scriptEditor", "Find and Replace", None))
        self.undo_act.setText(QApplication.translate("scriptEditor", "Undo", None))
        self.redo_act.setText(QApplication.translate("scriptEditor", "Redo", None))
        self.printHelp_act.setText(QApplication.translate("scriptEditor", "Help", None))
        self.comment_cat.setText(QApplication.translate("scriptEditor", "Comment", None))
