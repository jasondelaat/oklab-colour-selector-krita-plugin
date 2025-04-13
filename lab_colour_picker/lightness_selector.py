"""Displays a 'slice' of the gamut for a given lightness level
controlled via slider.

This view distorts the visible OKLab gamut. The distance from the
center of the circle indicates /saturation/ rather than /chroma/
meaning, for a given lightness level, some hues are more stretched out
while others are more compressed.

"""
import math

from krita import *

from .b_tree import *
from .oklab import *
from .selector_common import *
from .util import *

class LightnessDisplay(SelectorSurface):
    def __init__(self, parent, display_size):
        super().__init__(parent, display_size)
        self.lightness = 0.5
        self.chromas = None
        self.calculateMaxChromas()
        self.calculateColours()

    def calculateColours(self):
        """Recalculates the colour of every pixel on the colour circle
        based on the current lightness level.

        """
        i_size = self.image_size
        self.rgb_data = []
        for y in range(i_size):
          for x in range(i_size):
            metrics = SelectorSurface.pixel_metrics.get(x, {}).get(y)
            if metrics:
              (length, hue, cos, sin) = metrics
              ((h_low, c_low), (h_high, c_high)) = search(self.chromas, hue)
              delta = h_high - h_low
              c = lerp(c_low, c_high, (hue - h_low) / delta) if delta > 0 else c_low
              cx = lerp(0, c*cos, length)
              cy = lerp(0, c*sin, length)
              lab = Lab(self.lightness, cx, cy)
              rgb, clipped = oklab_to_srgb(lab)
              if clipped:
                self.rgb_data.extend([0, 0, 0, 0])
              else:
                self.rgb_data.extend(rgb)
                self.rgb_data.append(255)
            else:
              self.rgb_data.extend([0, 0, 0, 0])
              
        self.update_image()

    def modifyLightness(self, value):
        self.lightness = value
        self.calculateMaxChromas()
        self.calculateColours()
        self.updateForegroundColour()

    def calculateMaxChromas(self):
        """The colour selector displays saturation rather than
        absolute chroma. To do that we need to know the maximum chroma
        for each hue at the given level of lightness. It quickly
        becomes very costly to calculate the max chroma for every
        individual pixel. 

        This function calculates the max chroma for a selection of
        hues and stores them in a 2-3 search tree to be used by
        'calculateColours' to speed up the process.

        """
        del(self.chromas)
        self.chromas = Tree()

        for deg in range(0, 360, 2):
            hue = (deg - 180)*math.pi/180
            cos = math.cos(hue)
            sin = math.sin(hue)
            (low, high) = (0, 0.57)
            clipped = True

            # This is just a binary search to find the max chroma the
            # only extra detail being we want to make sure we end with
            # a chroma value that is actually inside the gamut or we
            # end up with grays on the edge of the circle.
            while abs(high - low) > 0.001 or clipped: # todo: might not need this much precision.
                ch = (low + high) / 2
                lab = Lab(self.lightness, ch*cos, ch*sin)
                rgb, clipped = oklab_to_srgb(lab)
                if clipped:
                    high = ch
                else:
                    low = ch
            self.chromas = insert(self.chromas, hue, ch)

    def updateToForeGroundColour(self):
        """When changing from another view to this one, sets the
        lightness level and moves the indicator circle to the current
        foreground colour.

        """
        lab = self.foregroundColorToLab()
        if not lab:
            return
        
        hue = math.atan2(lab.b, lab.a)
        ((hue_low, chroma_low), (hue_high, chroma_high)) = search(self.chromas, hue)
        hue_delta = hue_high - hue_low
        chroma_delta = chroma_high - chroma_low
        half_size = self.display_size / 2
        max_ch = lerp(chroma_low, chroma_high, (hue - hue_low) / hue_delta) if hue_delta > 0 else low
        ch = math.sqrt(lab.a*lab.a + lab.b*lab.b)
        self.position = (
          int(half_size + ch * math.cos(hue) * half_size / max_ch),
          int(half_size - ch * math.sin(hue) * half_size / max_ch)
        )
        self.indicator.move(*self.position)
        self.lightness = lab.L
        self.parent().setSlider(lab.L)
        self.calculateMaxChromas()
        self.calculateColours()

class LightnessSelector(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.lightness = Slider(self, 'Lightness: ', 500, self.modifyLightness)
        self.display = LightnessDisplay(self, 256)

        layout.addWidget(self.lightness)
        layout.addWidget(self.display)

    def setSlider(self, value):
        self.lightness.setValue(int(value*1000))

    def updateToForeGroundColour(self):
        self.lightness.disconnect()
        self.display.updateToForeGroundColour()
        self.lightness.valueChanged.connect(self.modifyLightness)
        
    def modifyLightness(self, value):
        self.lightness.slider.disconnect()
        self.display.modifyLightness(value/1000)
        self.lightness.slider.valueChanged.connect(self.modifyLightness)
