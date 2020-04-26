from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance
from functools import partial

import maya.cmds as cmds
import maya.OpenMaya as om
import maya.OpenMayaUI as omui

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class CustomPalettePort(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CustomPalettePort, self).__init__(parent)
        
        self.create_control()
    
    def create_control(self):
        window = cmds.window()
        layout = cmds.formLayout(parent=window)
        
        column = 8
        row = 1
        cell_height = 30
        cell_width = 15
        color_palette = cmds.palettePort( dimensions=(column, row),
                                          width=(column*cell_width),
                                          height=(row*cell_height),
                                          topDown=True,
                                          colorEditable=True)
        
        self.color_palette_obj = omui.MQtUtil.findControl(color_palette)
        if self.color_palette_obj:
            self.color_palette_widget = wrapInstance(long(self.color_palette_obj), QtWidgets.QWidget)
            
            main_layout = QtWidgets.QVBoxLayout(self)
            main_layout.setObjectName("main_layout")
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.addWidget(self.color_palette_widget)
        
        cmds.deleteUI(window, window=True)
    
    def get_full_name(self):
        return omui.MQtUtil.fullName(long(self.color_palette_obj))
    
    def get_color(self):
        color = cmds.palettePort(self.get_full_name(), query=True, rgbValue=True)
        color = QtGui.QColor(color[0] * 255, color[1] * 255, color[2] * 255)
        return color

class InfluenceColorDialog(QtWidgets.QDialog):
    
    WINDOW_NAME = "Influence Color: "
    
    def __init__(self, influence, parent = maya_main_window()):
        super(InfluenceColorDialog, self).__init__(parent)
        self.setWindowTitle(self.WINDOW_NAME+influence.text(0))
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(420)
        self.influence = influence
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
    
    def create_widgets(self):
        self.toolBtn = QtWidgets.QToolButton()
        self.colorMenu = QtWidgets.QMenu(self.toolBtn)
        self.index_action = self.colorMenu.addAction('Index')
        self.rgb_action = self.colorMenu.addAction('RGB')
        
        self.toolBtn.setMenu(self.colorMenu)
        self.toolBtn.setDefaultAction(self.index_action)
        self.toolBtn.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup)
        
        self.colorPalette = CustomPalettePort()
        
        self.applyBtn = QtWidgets.QPushButton("Apply")
        self.closeBtn = QtWidgets.QPushButton("Close")
    
    def create_layout(self):
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.applyBtn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.closeBtn)
        
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.addWidget(self.toolBtn)
        self.main_layout.addWidget(self.colorPalette)
        self.main_layout.addLayout(btn_layout)
        
    def create_connections(self):
        self.index_action.triggered.connect(self.indexAction)
        self.rgb_action.triggered.connect(self.rgbAction)
        
        self.applyBtn.clicked.connect(self.applyBtnClicked)
        self.closeBtn.clicked.connect(self.closeBtnClicked)
    
    def indexAction(self):
        self.toolBtn.setDefaultAction(self.index_action)
    
    def rgbAction(self):
        self.toolBtn.setDefaultAction(self.rgb_action)
    
    def applyBtnClicked(self):        
        color = self.colorPalette.get_color()
        treeWdg = self.influence.treeWidget()
        btn = treeWdg.itemWidget(self.influence, 2)
        joint_name = self.influence.text(0)
        
        cmds.setAttr("{0}.overrideRGBColors".format(joint_name), True)
        cmds.setAttr("{0}.overrideColorRGB".format(joint_name), color.red(), color.green(), color.blue())
        
        btn.setStyleSheet("QPushButton{background-color:" + "rgb({0}, {1}, {2});".format(color.red(), color.green(), color.blue()) + "}")
        
    def closeBtnClicked(self):
        self.close()
        

class PaintSkinWeightsTool(QtWidgets.QDialog):
    
    WINDOW_NAME = "Paint Skin Weight Tool"
    
    def __init__(self, parent = maya_main_window()):
        super(PaintSkinWeightsTool, self).__init__(parent)
        
        self.setWindowTitle(self.WINDOW_NAME)
        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(460)
        
        self.lock_OFF = QtGui.QIcon(":Lock_OFF_grey.png")
        self.lock_ON  = QtGui.QIcon(":Lock_ON.png")
        self.arrow_down = QtGui.QIcon(":arrowDown.png")
        
        self.create_actions()
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        self.populate_treeWdg()
    
    def create_actions(self):
        self.lock_action = QtWidgets.QAction("Lock Selected", self)
        self.unlock_action = QtWidgets.QAction("Unlock Selected", self)
    
    def create_widgets(self):
        self.influenceLbl = QtWidgets.QLabel('Influences')
        self.influenceLbl.setStyleSheet(""" QLabel {background-color : rgb(93,93,93);
                                                    color : rgb(185,185,185); 
                                                    font-size: 14px;
                                                    padding-left: 10px;
                                                    border-radius: 2px;}""")
        
        self.treeWdg = QtWidgets.QTreeWidget()
        self.treeWdg.setHeaderHidden(True)
        self.treeWdg.setColumnCount(4)
        self.treeWdg.setTreePosition(3)
        self.treeWdg.setColumnHidden(0, True)
        self.treeWdg.setColumnWidth(1,30)
        self.treeWdg.setColumnWidth(2,30)
        self.treeWdg.setStyleSheet( """ QTreeWidget::item { border-top: 1px solid rgb(93,93,93);}
                                        QTreeWidget::item::selected {background-color: rgb(102,140,178);}
                                        QTreeWidget::branch{border-top: 1px solid rgb(93,93,93);}
                                        QTreeWidget::branch::selected{border-top: 1px solid rgb(93,93,93);
                                                                      background-color: rgb(102,140,178);}
                                        QTreeWidget::branch::open{image: url(:arrowDown.png);}
                                        QTreeWidget::branch::closed::has-children{image: url(:arrowRight.png)};""")
    
    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.influenceLbl)
        main_layout.addWidget(self.treeWdg)
    
    def create_connections(self):
        self.treeWdg.itemSelectionChanged.connect(self.select_items)
        
        self.lock_action.triggered.connect(partial(self.lock_influence_action, True))
        self.unlock_action.triggered.connect(partial(self.lock_influence_action, False))
    
    def populate_treeWdg(self):
        self.skin_clusters = cmds.ls(type="skinCluster")
        self.influence_list = []
        for skin_cluster in self.skin_clusters:
            self.influence_list.extend(list(set(cmds.skinCluster(skin_cluster, query=True, inf=True)) - set(self.influence_list)))
            
        self.top_level_object_names = cmds.ls(assemblies=True)
        self.treeWdg.clear()
        
        for name in list(set(self.top_level_object_names) & set(self.influence_list)):
            item = self.create_item(name)
            self.treeWdg.addTopLevelItem(item)
            self.treeWdg.setCurrentItem(item)
            
        if self.treeWdg.topLevelItemCount()>0:
            for item_no in range(self.treeWdg.topLevelItemCount()):
                self.add_tree_item_widgets(self.treeWdg.topLevelItem(0), 1)
    
    def create_item(self, name):
        item = QtWidgets.QTreeWidgetItem([name])
        item.setText(3, name)
        self.add_item_children(item)
        
        return item
    
    def add_item_children(self, item):
        children = cmds.listRelatives(item.text(0), children=True)
        if children:
            for child in children:
                child_item = self.create_item(child)
                item.addChild(child_item)
    
    def add_tree_item_widgets(self, item, column):
        try:
            #to accomodate effectors
            locked = cmds.getAttr(item.text(0)+'.liw')
            if locked:
                lock_btn = QtWidgets.QPushButton(icon=self.lock_ON, parent=self.treeWdg)
            else:
                lock_btn = QtWidgets.QPushButton(icon=self.lock_OFF, parent=self.treeWdg)
        except:
            lock_btn = QtWidgets.QPushButton("E", parent=self.treeWdg)
        
        lock_btn.setStyleSheet( """ QPushButton{border: 1px solid rgb(98,98,98);
                                                border-radius: 3px;
                                                background-color: rgb(93,93,93);
                                                height: 30px;}""")
                                                       
        color_btn = QtWidgets.QPushButton(parent=self.treeWdg)
        color_btn.setStyleSheet(""" QPushButton{border: 1px solid rgb(98,98,98);
                                                border-radius: 3px;
                                                background-color: Orange;}""")
        
        lock_btn.clicked.connect(partial(self.lock_influence_btn, item))          
        color_btn.clicked.connect(partial(self.color_select_clicked, item))
        
        self.treeWdg.setItemWidget(item, column, lock_btn)
        self.treeWdg.setItemWidget(item, column+1, color_btn)
        
        if item.childCount()>0:
            for child in range(item.childCount()):
                self.add_tree_item_widgets(item.child(child), column)
                
    def select_items(self):
        items = self.treeWdg.selectedItems()
        names = []
        for item in items:
            names.append(item.text(0))
        
        cmds.select(names, replace=True)
    
    def show_context_menu(self, point):
        context_menu = QtWidgets.QMenu()
        context_menu.addAction(self.lock_action)
        context_menu.addAction(self.unlock_action)

        context_menu.exec_(self.mapToGlobal(point))
        
    def lock_influence_btn(self, item):            
        btn = self.treeWdg.itemWidget(item, 1)
        try:
            # to accomodate effectors
            locked = cmds.getAttr(item.text(0)+'.liw')
            if locked:
                cmds.setAttr(item.text(0)+'.liw', False)
                btn.setIcon(self.lock_OFF)
            else:
                cmds.setAttr(item.text(0)+'.liw', True)
                btn.setIcon(self.lock_ON)
        except:
            print("effector cannot be locked/unlocked")
    
    def lock_influence_action(self, lock):
        item = self.treeWdg.currentItem()
        btn = self.treeWdg.itemWidget(item, 1)
        if lock:
            cmds.setAttr(item.text(0)+'.liw', True)
            btn.setIcon(self.lock_ON)
        else:
            cmds.setAttr(item.text(0)+'.liw', False)
            btn.setIcon(self.lock_OFF)
    
    def color_select_clicked(self, item):
        influence_color_dialog = InfluenceColorDialog(item, self)
        influence_color_dialog.show()
    
if __name__ == "__main__":
    try:
        paint_skin_weights_tool.close()
        paint_skin_weights_tool.deleteLater()
    except:
        pass
    paint_skin_weights_tool = PaintSkinWeightsTool()
    paint_skin_weights_tool.show()
