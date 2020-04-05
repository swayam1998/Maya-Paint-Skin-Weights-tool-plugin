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
    
    def __init__(self, parent = maya_main_window()):
        super(PaintSkinWeightsTool, self).__init__(parent)
        
        self.setWindowTitle("Paint Skin Weight Tool")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(300)
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        self.populate_treeWdg()
                
    def create_widgets(self):
        self.treeWdg = QtWidgets.QTreeWidget()
        self.treeWdg.setHeaderHidden(True)
    
    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2,2,2,2)
        main_layout.setSpacing(2)
        main_layout.addWidget(self.treeWdg)
    
    def create_connections(self):
        self.treeWdg.itemSelectionChanged.connect(self.select_items)
    
    def populate_treeWdg(self):
        self.joint_node_names = cmds.ls(type="joint")                               #find a better way to list items
        self.top_level_object_names = cmds.ls(assemblies=True)                      #like cmds.ls(type= "joint" and assemblies="True")
        
        self.treeWdg.clear()
        
        for name in list(set(self.top_level_object_names) & set(self.joint_node_names)):
            item = self.create_item(name)
            self.treeWdg.addTopLevelItem(item)
    
    def create_item(self, name):
        item = QtWidgets.QTreeWidgetItem([name])
        self.add_item_children(item)
        
        return item
    
    def add_item_children(self, item):
        children = cmds.listRelatives(item.text(0), children=True)
        if children:
            for child in children:
                child_item = self.create_item(child)
                item.addChild(child_item)
                
    def select_items(self):
        items = self.treeWdg.selectedItems()
        names = []
        for item in items:
            names.append(item.text(0))
        
        cmds.select(names, replace=True)
    
    
if __name__ == "__main__":
    try:
        PaintSkinWeightsTool.close()
        PaintSkinWeightsTool.deleteLater()
    except:
        pass
    paint_skin_weights_tool = PaintSkinWeightsTool()
    paint_skin_weights_tool.show()
        