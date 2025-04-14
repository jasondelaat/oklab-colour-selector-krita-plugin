"""The plugin's main Dock widget.

Contains the colour selector's different views in a stacked layout
with radio buttons for selecting between them.

"""
from krita import *

from .lightness_selector import *
from .hue_plane_selector import *
from .chroma_selector import *

class lab_colour_picker(QDockWidget):
#class lab_colour_picker(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('OKLab Colour Selector')
        self.main = QWidget(self)
        self.layout = QGridLayout()
        self.main.setLayout(self.layout)

        self.gamut = QRadioButton('Lightness', self.main)
        self.gamut.setChecked(True)
        self.gamut.toggled.connect(self.set_display)

        self.plane = QRadioButton('Hue Plane', self.main)
        self.plane.toggled.connect(self.set_display)

        self.chroma = QRadioButton('Chroma', self.main)
        self.plane.toggled.connect(self.set_display)

        self.view_stack = QStackedLayout()
        self.gamut_view = LightnessSelector(self.main)
        self.plane_view = OKLabHuePlaneSelector(self.main)
        self.chroma_view = OKLabChromaLightnessSelector(self.main)
        self.view_stack.addWidget(self.gamut_view)
        self.view_stack.addWidget(self.plane_view)
        self.view_stack.addWidget(self.chroma_view)

        self.current_view = self.gamut_view

        self.layout.addLayout(self.view_stack, 0, 0)
        self.layout.addWidget(self.gamut, 1, 0)
        self.layout.addWidget(self.plane, 2, 0)
        self.layout.addWidget(self.chroma, 3, 0)

        #self.main.show()

        self.setWidget(self.main)
        

    def set_display(self):
        if self.gamut.isChecked():
            self.view_stack.setCurrentIndex(0)
            self.current_view = self.gamut_view

        if self.plane.isChecked():
            self.view_stack.setCurrentIndex(1)
            self.current_view = self.plane_view

        if self.chroma.isChecked():
            self.view_stack.setCurrentIndex(2)
            self.current_view = self.chroma_view

        self.current_view.updateToForeGroundColour()

    def canvasChanged(self):
        pass

#lab_colour_picker().exec_()
Krita.instance().addDockWidgetFactory(DockWidgetFactory("lab_colour_picker", DockWidgetFactoryBase.DockRight, lab_colour_picker)) 
