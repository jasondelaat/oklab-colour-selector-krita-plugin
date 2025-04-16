"""Displays a slice of the gamut containing a single hue with
lightness increasing as you move up and chroma increasing as you move
right.

This view resembles the common triangular colour selector but with
each triangle skewed to account for the difference in perceptual
brightness of the hue at its most vivid intensity.

"""

import math

from krita import *

from .selector_common import *
from .util import *

class HueEffect(QGraphicsEffect):
    def __init__(self, parent):
        super().__init__(parent)
        data = []
        for y in range(10):
            for x in range(255):
                hue = 2 * (x/255) * math.pi
                a = 0.085*math.cos(hue)
                b = 0.085*math.sin(hue)
                lab = Lab(0.5, a, b)
                rgb, _ = oklab_to_srgb(lab)
                c = QColor(rgb[0], rgb[1], rgb[2]).toHsl()
                hue = c.hslHueF()
                c.setHslF(hue, 1, 0.5)
                c = c.toRgb()
                data.append(c.red())
                data.append(c.green())
                data.append(c.blue())
                data.append(255)

        im = QImage(bytes(data), 255, 10, QImage.Format_RGBA8888)
        self.pixmap = QPixmap.fromImage(im)
        self.arrow = Krita.instance().icon('docker_collapse_a').pixmap(16, 16)
        self.arrow = self.arrow.transformed(QTransform(1, 0, 0, -1, 0, 16))
        
    def draw(self, painter):
        width = self.parent().width()
        val = self.parent().value()
        painter.drawPixmap(QRectF(10, -5, width-20, 10), self.pixmap, QRectF(0, 0, 255, 10))
        painter.drawPixmap(QPoint(2 + int(val*(width-20)/1000), 0), self.arrow)
        #self.drawSource(painter)


class OKLabHuePlane(SelectorSurface):
    def __init__(self, parent, display_size):
        super().__init__(parent, display_size)
        self.hue = 0
        self.calculateColours()

    def modifyHue(self, value):
        self.hue = value
        self.calculateColours()
        self.updateForegroundColour()

    def calculateColours(self):
        i_size = self.image_size
        red_green = math.cos(self.hue)
        blue_yellow = math.sin(self.hue)
        self.rgb_data = []
        for y in range(i_size):
            for x in range(i_size):
                lightness = 1 - (y / i_size)
                chroma = lerp(0, 0.35, x / i_size)
                lab = Lab(lightness, red_green*chroma, blue_yellow*chroma)
                rgb, clipped = oklab_to_srgb(lab)
                if clipped:
                  self.rgb_data.extend([0, 0, 0, 0])
                else:
                  self.rgb_data.extend(rgb)
                  self.rgb_data.append(255)
        self.update_image()

    def updateToForeGroundColour(self):
        lab = self.foregroundColorToLab()
        if not lab:
            return

        hue = math.atan2(lab.b, lab.a)
        d_size = self.display_size
        ch = math.sqrt(lab.a*lab.a + lab.b*lab.b)
        self.parent().setSlider(hue)
        self.position = (int(d_size*(ch/0.35)), int(d_size - d_size*lab.L))
        self.indicator.move(*self.position)
        self.hue = hue
        self.calculateColours()

class OKLabHuePlaneSelector(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.hue = Slider(self, 'Hue:', 0, self.modifyHue)
        self.hue.slider.setGraphicsEffect(HueEffect(self.hue.slider))
        self.plane = OKLabHuePlane(self, 256)
        layout.addWidget(self.hue)
        layout.addWidget(self.plane)

    def modifyHue(self, value):
        self.hue.disconnect()
        self.plane.modifyHue(lerp(0, 6.28, value/1000))
        self.hue.valueChanged.connect(self.modifyHue)

    def updateToForeGroundColour(self):
        self.hue.disconnect()
        self.plane.updateToForeGroundColour()
        self.hue.valueChanged.connect(self.modifyHue)

    def setSlider(self, value):
        self.hue.setValue(int(value*1000/6.28))
        
