# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'D:\Dropbox\Dropbox\pw_prefs\RnD\tools\pw_scriptEditor\widgets\themeEditor.ui'
#
# Created: Mon Mar 16 10:29:58 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!


from vendor.Qt.QtCore import QMetaObject, QSize, Qt
from vendor.Qt.QtWidgets import QApplication, QComboBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QSizePolicy, QSpacerItem, QSpinBox, QSplitter, QVBoxLayout, QWidget, QFormLayout, QCheckBox

class Ui_themeEditor(object):
    def setupUi(self, themeEditor):
        themeEditor.setObjectName("themeEditor")
        themeEditor.resize(724, 461)
        self.verticalLayout_3 = QVBoxLayout(themeEditor)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.splitter = QSplitter(themeEditor)
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.widget = QWidget(self.splitter)
        self.widget.setObjectName("widget")
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.colors_lwd = QListWidget(self.widget)
        self.colors_lwd.setObjectName("colors_lwd")
        
        self.horizontalLayout_font = QHBoxLayout()
        self.horizontalLayout_font.setObjectName("horizontalLayout_font")
        self.choose_font_btn = QPushButton(self.widget)
        self.choose_font_btn.setObjectName("choose_font_btn")
        self.horizontalLayout_font.addWidget(self.choose_font_btn)

        self.font_name_label = QLabel(self.widget)
        self.font_name_label.setObjectName("font_name_label")
        self.horizontalLayout_font.addWidget(self.font_name_label)
        spacerItemFont = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_font.addItem(spacerItemFont)
        self.verticalLayout_2.addLayout(self.horizontalLayout_font)

        self.verticalLayout_2.addWidget(self.colors_lwd)
        
        self.formLayout = QFormLayout()
        self.formLayout.setObjectName("formLayout")
        
        self.label = QLabel(self.widget)
        self.label.setObjectName("label")
        self.textSize_spb = QSpinBox(self.widget)
        self.textSize_spb.setMinimum(6)
        self.textSize_spb.setMaximum(25)
        self.textSize_spb.setProperty("value", 10)
        self.textSize_spb.setObjectName("textSize_spb")
        self.formLayout.addRow(self.label, self.textSize_spb)
        
        self.label_outlineSize = QLabel(self.widget)
        self.label_outlineSize.setObjectName("label_outlineSize")
        self.outlineSize_spb = QSpinBox(self.widget)
        self.outlineSize_spb.setMinimum(6)
        self.outlineSize_spb.setMaximum(30)
        self.outlineSize_spb.setProperty("value", 10)
        self.outlineSize_spb.setObjectName("outlineSize_spb")
        self.formLayout.addRow(self.label_outlineSize, self.outlineSize_spb)
        
        self.label_outputSize = QLabel(self.widget)
        self.label_outputSize.setObjectName("label_outputSize")
        self.outputSize_spb = QSpinBox(self.widget)
        self.outputSize_spb.setMinimum(6)
        self.outputSize_spb.setMaximum(25)
        self.outputSize_spb.setProperty("value", 10)
        self.outputSize_spb.setObjectName("outputSize_spb")
        self.formLayout.addRow(self.label_outputSize, self.outputSize_spb)
        
        self.label_tabSize = QLabel(self.widget)
        self.label_tabSize.setObjectName("label_tabSize")
        self.tabSize_spb = QSpinBox(self.widget)
        self.tabSize_spb.setMinimum(6)
        self.tabSize_spb.setMaximum(30)
        self.tabSize_spb.setProperty("value", 10)
        self.tabSize_spb.setObjectName("tabSize_spb")
        self.formLayout.addRow(self.label_tabSize, self.tabSize_spb)
        
        self.label_radius = QLabel(self.widget)
        self.label_radius.setObjectName("label_radius")
        self.tabRadius_spb = QSpinBox(self.widget)
        self.tabRadius_spb.setMinimum(0)
        self.tabRadius_spb.setMaximum(50)
        self.tabRadius_spb.setProperty("value", 12)
        self.tabRadius_spb.setObjectName("tabRadius_spb")
        self.formLayout.addRow(self.label_radius, self.tabRadius_spb)
        
        self.menuFont_cb = QCheckBox(self.widget)
        self.menuFont_cb.setObjectName("menuFont_cb")
        self.formLayout.addRow("", self.menuFont_cb)
        
        self.horizontalLayout_formContainer = QHBoxLayout()
        self.horizontalLayout_formContainer.addLayout(self.formLayout)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_formContainer.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout_formContainer)
        
        self.layoutWidget = QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.themeList_cbb = QComboBox(self.layoutWidget)
        self.themeList_cbb.setObjectName("themeList_cbb")
        self.horizontalLayout.addWidget(self.themeList_cbb)
        self.save_btn = QPushButton(self.layoutWidget)
        self.save_btn.setMaximumSize(QSize(60, 16777215))
        self.save_btn.setObjectName("save_btn")
        self.horizontalLayout.addWidget(self.save_btn)
        self.del_btn = QPushButton(self.layoutWidget)
        self.del_btn.setMaximumSize(QSize(60, 16777215))
        self.del_btn.setObjectName("del_btn")
        self.horizontalLayout.addWidget(self.del_btn)
        self.horizontalLayout.setStretch(0, 1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.preview_ly = QVBoxLayout()
        self.preview_ly.setObjectName("preview_ly")
        self.verticalLayout.addLayout(self.preview_ly)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout_3.addWidget(self.splitter)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.apply_btn = QPushButton(themeEditor)
        self.apply_btn.setObjectName("apply_btn")
        self.horizontalLayout_2.addWidget(self.apply_btn)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.verticalLayout_3.setStretch(0, 1)

        self.retranslateUi(themeEditor)
        QMetaObject.connectSlotsByName(themeEditor)

    def retranslateUi(self, themeEditor):
        themeEditor.setWindowTitle(QApplication.translate("themeEditor", "Code Theme Editor", None))
        self.label_radius.setText(QApplication.translate("themeEditor", "Tab border radius", None))
        self.label.setText(QApplication.translate("themeEditor", "Completer text size", None))
        self.label_outlineSize.setText(QApplication.translate("themeEditor", "Outline text size", None))
        self.label_outputSize.setText(QApplication.translate("themeEditor", "Output text size", None))
        self.label_tabSize.setText(QApplication.translate("themeEditor", "Tab label text size", None))
        self.menuFont_cb.setText(QApplication.translate("themeEditor", "Menus and status bar use theme font", None))
        self.save_btn.setText(QApplication.translate("themeEditor", "Save", None))
        self.del_btn.setText(QApplication.translate("themeEditor", "Del", None))
        self.apply_btn.setText(QApplication.translate("themeEditor", "Save", None))
        self.choose_font_btn.setText(QApplication.translate("themeEditor", "Choose Font", None))
        self.font_name_label.setText(QApplication.translate("themeEditor", "Default", None))

