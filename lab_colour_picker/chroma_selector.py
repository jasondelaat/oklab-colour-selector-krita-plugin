"""Similar to the LightnessSelector but rather than chroma increasing
as you move away from the center, the entire surface has uniform
chroma. Both lightness and chroma are controlled with sliders and out
of gamut colours simply become gaps in the circle.

"""
import math

from krita import *

from .selector_common import *
from .util import *

class ChromaLightnessDisplay(SelectorSurface):
    def __init__(self, parent, display_size):
        super().__init__(parent, display_size)
        self.chroma = 0.5
        self.lightness = 0.5
        self.calculateColours()

    def updateToForeGroundColour(self):
        lab = self.foregroundColorToLab()
        if not lab:
            return
        
        hue = math.atan2(lab.b, lab.a)
        ch = math.sqrt(lab.a*lab.a + lab.b*lab.b) / 0.4
        half_size = self.display_size / 2
        self.parent().setSliders(lab.L, ch)
        self.position = (
          int(half_size + 0.5 * half_size * math.cos(hue)),
          int(half_size - 0.5 * half_size * math.sin(hue))
        )
        self.indicator.move(*self.position)
        self.lightness = lab.L
        self.chroma = ch
        self.calculateColours()
    
    def calculateColours(self):
        i_size = self.image_size
        self.rgb_data = []
        for y in range(i_size):
            for x in range(i_size):
                metrics = SelectorSurface.pixel_metrics.get(x, {}).get(y)
                if metrics:
                    (c, hue, cos, sin) = metrics

                    a = 0.4 * self.chroma * cos
                    b = 0.4 * self.chroma * sin

                    lab = Lab(self.lightness, a, b)
                    rgb, clipped = oklab_to_srgb(lab)
                    if clipped:
                      self.rgb_data.extend([0, 0, 0, 0])
                    else:
                      self.rgb_data.extend(rgb)
                      self.rgb_data.append(255)
                else:
                    self.rgb_data.extend([0, 0, 0, 0])
        self.update_image()

    def modifyChroma(self, value):
        self.chroma = value
        self.calculateColours()
        self.updateForegroundColour()

    def modifyLightness(self, value):
        self.lightness = value
        self.calculateColours()
        self.updateForegroundColour()

class OKLabChromaLightnessSelector(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.lightness = Slider(self, 'Lightness:', 500, self.modifyLightness)
        self.chroma = Slider(self, 'Chroma:', 500, self.modifyChroma)
        self.display = ChromaLightnessDisplay(self, 256)

        layout.addWidget(self.lightness)
        layout.addWidget(self.chroma)
        layout.addWidget(self.display)

    def modifyLightness(self, value):
        self.lightness.disconnect()
        self.display.modifyLightness(value / 1000)
        self.lightness.valueChanged.connect(self.modifyLightness)

    def modifyChroma(self, value):
        self.chroma.disconnect()
        self.display.modifyChroma(value / 1000)
        self.chroma.valueChanged.connect(self.modifyChroma)

    def setSliders(self, lightness, chroma):
        self.lightness.setValue(int(lightness*1000))
        self.chroma.setValue(int(chroma*1000))

    def updateToForeGroundColour(self):
        self.chroma.disconnect()
        self.lightness.disconnect()
        self.display.updateToForeGroundColour()
        self.chroma.valueChanged.connect(self.modifyChroma)
        self.lightness.valueChanged.connect(self.modifyLightness)
    
