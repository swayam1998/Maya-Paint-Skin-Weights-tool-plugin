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

class PaintSkinWeightsTool(QtWidgets.QDialog):
    
    WINDOW_NAME = "Paint Skin Weight Tool"
    
    def __init__(self, parent = maya_main_window()):
        super(PaintSkinWeightsTool, self).__init__(parent)
        
        self.setWindowTitle(self.WINDOW_NAME)
        self.setWindowFlags(QtCore.Qt.WindowType.Window)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(300)
        
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
        self.influenceLbl.setStyleSheet("""QLabel { background-color : rgb(93,93,93);
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
            
        color_btn = QtWidgets.QPushButton("C", parent=self.treeWdg)
        lock_btn.clicked.connect(partial(self.lock_influence_btn, item))
        color_btn.toggled.connect(self.color_select_clicked)
        
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
    
    def color_select_clicked(self):
        print("color selected")
        
    
if __name__ == "__main__":
    try:
        paint_skin_weights_tool.close()
        paint_skin_weights_tool.deleteLater()
    except:
        pass
    paint_skin_weights_tool = PaintSkinWeightsTool()
    paint_skin_weights_tool.show()
