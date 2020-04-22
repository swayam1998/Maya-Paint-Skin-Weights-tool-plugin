from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

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
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(300)
        
        self.lock_OFF = QtGui.QIcon(":Lock_OFF_grey.png")
        self.lock_ON  = QtGui.QIcon(":Lock_ON.png")
        self.arrow_down = QtGui.QIcon(":arrowDown.png")
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        self.populate_treeWdg()
                
    def create_widgets(self):
        self.treeWdg = QtWidgets.QTreeWidget()
        self.treeWdg.setHeaderHidden(True)
        self.treeWdg.setColumnCount(4)
        self.treeWdg.setTreePosition(3)
        self.treeWdg.setColumnHidden(0, True)
        self.treeWdg.setColumnWidth(1,30)
        self.treeWdg.setColumnWidth(2,30)
    
    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.treeWdg)
    
    def create_connections(self):
        self.treeWdg.itemSelectionChanged.connect(self.select_items)
    
    def populate_treeWdg(self):
        self.skin_clusters = cmds.ls(type="skinCluster")
        self.joint_node_names = []
        
        for skin_cluster in self.skin_clusters:
            self.joint_node_names.extend(list(set(cmds.skinCluster(skin_cluster, query=True, inf=True)) - set(self.joint_node_names)))
            
        self.top_level_object_names = cmds.ls(assemblies=True)
        self.treeWdg.clear()
        
        for name in list(set(self.top_level_object_names) & set(self.joint_node_names)):
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
        lock_btn = QtWidgets.QPushButton(icon=self.lock_OFF, parent=self.treeWdg)
        color_btn = QtWidgets.QPushButton("OK_2", parent=self.treeWdg)        
        lock_btn.setCheckable(True)
        color_btn.setCheckable(True)                
        lock_btn.toggled.connect(self.lock_button_clicked)
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

    def lock_button_clicked(self, checked):
        print(checked, "locked")
    
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
    