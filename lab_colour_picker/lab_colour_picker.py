from krita import *
import math
from collections import namedtuple

Lab = namedtuple('Lab', ['L', 'a', 'b'])

def oklab_to_srgb(c):
  l_ = c.L + 0.3963377774*c.a + 0.2158037573*c.b
  m_ = c.L - 0.1055613458*c.a - 0.0638541728*c.b
  s_ = c.L - 0.0894841775*c.a - 1.2914855480*c.b

  l = l_*l_*l_
  m = m_*m_*m_
  s = s_*s_*s_

  rgb = [
    4.0767416621*l - 3.3077115913*m + 0.2309699292*s,
    -1.2684380046*l + 2.6097574011*m - 0.3413193965*s,
    -0.0041960863*l - 0.7034186147*m + 1.7076147010*s
  ]
  rgb, clipped = clip(map(rgb_channel_to_srbg_channel, rgb))
  return rgb, clipped

def rgb_channel_to_srbg_channel(x):
  if x > 0.0031308:
    return (1.055) * x**(1.0/2.4) - 0.055
  else:
    return 12.92 * x

def clamp(i, low, high):
  return max(low, min(high, i))

def clip(col):
  data = []
  for c in col:
    if c < 0 or c > 1:
      return [128, 128, 128], True
    data.append(int(255*c))
  return data, False

def lerp(low, high, t):
  return low + t*(high - low)

def find_limit_start(lightness, start):
  rng = range(100) if start == 'top' else range(100, 1, -1)
  for i in rng:
    p = lerp(-0.41, 0.41, i/100)
    lab = Lab(lightness, p, p)
    rgb, clipped = oklab_to_srgb(lab)
    if not clipped:
      return i
      break
  
def inc(x):
  return x + 1

def dec(x):
  return x - 1

def calc_limit(start, pred, inc_f, lightness, axis):
  value = start
  while pred(value):
    in_gamut = False
    for i in range(100):
      if axis == 'x':
        lab = Lab(lightness, lerp(-0.41, 0.41, value/100), lerp(-0.41, 0.41, i/100))
      else:
        lab = Lab(lightness, lerp(-0.41, 0.41, i/100), lerp(-0.41, 0.41, value/100))
      rgb, clipped = oklab_to_srgb(lab)
      in_gamut = in_gamut or not clipped
    if not in_gamut:
      break
    value = inc_f(value)
  return lerp(-0.41, 0.41, value/100)

VERTICAL = 0
HORIZONTAL = 1
disc_size = 150
class Indicator(QWidget):
  def __init__(self, parent):
    super().__init__(parent)
    white_circle = Krita.instance().icon('krita_tool_ellipse').pixmap(QSize(10, 10))
    black_circle = Krita.instance().icon('krita_tool_ellipse').pixmap(QSize(12, 12))
    mask = black_circle.mask()
    black_circle.fill(QColor('black'))
    black_circle.setMask(mask)
    self.outer = QLabel(self)
    self.outer.setPixmap(black_circle)
    self.inner = QLabel(self)
    self.inner.setPixmap(white_circle)
    self.inner.move(1, 1)


class CPSlider(QWidget):
  def __init__(self, parent, label_before, label_after, value, orientation, action):
    super().__init__(parent)
    layout = QHBoxLayout() if orientation == HORIZONTAL else QVBoxLayout()
    self.setLayout(layout)
    self.slider = QSlider(orientation, self)
    self.slider.setRange(0, 1000)
    self.slider.setValue(value)
    self.slider.valueChanged.connect(action)
    self.valueChanged = self.slider.valueChanged

    layout.addWidget(QLabel(label_before, self))
    layout.addWidget(self.slider)
    layout.addWidget(QLabel(label_after, self))

  def setValue(self, value):
    return self.slider.setValue(value)

  def value(self):
    return self.slider.value()

  def disconnect(self):
    self.slider.disconnect()

class SelectorSurface(QLabel):
  def __init__(self, parent, image_size, display_size):
    super().__init__(parent)
    self.indicator = Indicator(self)
    self.position = (0, 0)
    self.image_size = image_size
    self.display_size = display_size

  # Derived classes *must* define self.rgb_data before calling this method.
  def update_image(self):
    i_size = self.image_size
    d_size = self.display_size
    self.image = QImage(bytes(self.rgb_data), i_size, i_size, QImage.Format_RGBA8888).scaled(d_size, d_size)#.rgbSwapped()
    self.pix_image = QPixmap.fromImage(self.image)
    self.setPixmap(self.pix_image)


  def updateForegroundColour(self):
    win = Krita.instance().activeWindow()
    if not win:
      return

    view = win.activeView()
    if not view:
      return

    argb = self.image.pixelColor(*self.position)
    selected_colour = ManagedColor.fromQColor(argb)
    view.setForeGroundColor(selected_colour)
    self.indicator.move(self.position[0]-6, self.position[1]-6)

  def mouseMoveEvent(self, ev):
    self.position = (ev.x(), ev.y())
    self.updateForegroundColour()

  def mousePressEvent(self, ev):
    self.position = (ev.x(), ev.y())
    self.updateForegroundColour()


class GamutDisplay(SelectorSurface):
  def __init__(self, parent, image_size, display_size):
    super().__init__(parent, image_size, display_size)
    self.lightness = 0.5
    self.calculateColours()

  def calculateColours(self):
    i_size = self.image_size
    upper_lower = find_limit_start(self.lightness, 'top')
    lower_upper = find_limit_start(self.lightness, 'bottom')
    x_lower = calc_limit(upper_lower, lambda i: i > 0, dec, self.lightness, 'x')
    x_upper = calc_limit(lower_upper, lambda i: i < 100, inc, self.lightness, 'x')
    y_lower = calc_limit(upper_lower, lambda i: i > 0, dec, self.lightness, 'y')
    y_upper = calc_limit(lower_upper, lambda i: i < 100, inc, self.lightness, 'y')

    delta_x = (x_upper - x_lower) / i_size
    delta_y = (y_upper - y_lower) / i_size

    self.rgb_data = []
    for y in range(i_size):
      for x in range(i_size):
        cx = x_lower + x*delta_x
        cy = y_lower + (i_size - y)*delta_y
        lab = Lab(self.lightness, cx, cy)
        rgb, clipped = oklab_to_srgb(lab)
        self.rgb_data.extend(rgb)
        self.rgb_data.append(255)
    self.update_image()

  def modifyLightness(self, value):
    self.lightness = value
    self.calculateColours()

class OKLabHuePlane(SelectorSurface):
  def __init__(self, parent, image_size, display_size):
    super().__init__(parent, image_size, display_size)
    self.hue = 0
    self.calculateColours()

  def modifyHue(self, value):
    self.hue = value
    self.calculateColours()

  def calculateColours(self):
    i_size = self.image_size
    red_green = math.cos(self.hue)
    blue_yellow = math.sin(self.hue)
    self.rgb_data = []
    for y in range(i_size):
      for x in range(i_size):
        lightness = 1 - (y / i_size)
        chroma = lerp(0, 0.4, x / i_size)
        lab = Lab(lightness, red_green*chroma, blue_yellow*chroma)
        rgb, clipped = oklab_to_srgb(lab)
        self.rgb_data.extend(rgb)
        self.rgb_data.append(255)
    self.update_image()

class OKLabHuePlaneSelector(QWidget):
  def __init__(self, parent):
    super().__init__(parent)
    layout = QVBoxLayout()
    self.setLayout(layout)

    self.hue = CPSlider(self, 'Hue:', '', 0, HORIZONTAL, self.modifyHue)
    self.plane = OKLabHuePlane(self, 150, 256)
    layout.addWidget(self.hue)
    layout.addWidget(self.plane)

  def modifyHue(self, value):
    self.hue.disconnect()
    self.plane.modifyHue(lerp(0, 6.28, value/1000))
    self.hue.valueChanged.connect(self.modifyHue)
    
class OKLabGamutSelector(QWidget):
  def __init__(self, parent):
    super().__init__(parent)
    layout = QVBoxLayout()
    self.setLayout(layout)

    self.lightness = CPSlider(self, 'Lightness: ', '', 500, HORIZONTAL, lambda i: self.modifyLightness(i))
    self.display = GamutDisplay(self, 150, 256)

    layout.addWidget(self.lightness)
    layout.addWidget(self.display)

  def modifyLightness(self, value):
    self.lightness.slider.disconnect()
    self.display.modifyLightness(value/1000)
    self.lightness.slider.valueChanged.connect(lambda i: self.modifyLightness(i))

class ChromaLightnessDisplay(SelectorSurface):
  def __init__(self, parent, image_size, display_size):
    super().__init__(parent, image_size, display_size)
    self.chroma = 0.5
    self.lightness = 0.5
    self.calculateColours()

  def calculateColours(self):
    i_size = self.image_size
    self.rgb_data = []
    for y in range(i_size):
      ay = y - i_size / 2
      for x in range(i_size):
        ax = x - i_size / 2
        length = math.sqrt(ax*ax + ay*ay)
        if length <= i_size / 2:
          a = self.chroma * 0.4 * ax / length if length > 0 else 0
          b = self.chroma * 0.4 * ay / length if length > 0 else 0
          lab = Lab(self.lightness, a, b)
          rgb, clipped = oklab_to_srgb(lab)
          self.rgb_data.extend(rgb)
          self.rgb_data.append(255)
        else:
          self.rgb_data.extend([128, 128, 128, 255])
    self.update_image()

  def modifyChroma(self, value):
    self.chroma = value
    self.calculateColours()

  def modifyLightness(self, value):
    self.lightness = value
    self.calculateColours()

class OKLabChromaLightnessSelector(QWidget):
  def __init__(self, parent):
    super().__init__(parent)
    layout = QVBoxLayout()
    self.setLayout(layout)

    self.lightness = CPSlider(self, 'Lightness:', '', 500, HORIZONTAL, self.modifyLightness)
    self.chroma = CPSlider(self, 'Chroma:', '', 500, HORIZONTAL, self.modifyChroma)
    self.display = ChromaLightnessDisplay(self, 150, 256)

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

class lab_colour_picker(QDockWidget):
#class lab_colour_picker(QDialog):
  def __init__(self):
    super().__init__()
    self.setWindowTitle('OKLab Colour Selector')
    self.main = QWidget(self)
    self.layout = QGridLayout()
    self.main.setLayout(self.layout)

    self.gamut = QRadioButton('Gamut', self.main)
    self.gamut.setChecked(True)
    self.gamut.toggled.connect(self.set_display)

    self.plane = QRadioButton('Hue Plane', self.main)
    self.plane.toggled.connect(self.set_display)

    self.chroma = QRadioButton('Chroma', self.main)
    self.plane.toggled.connect(self.set_display)

    self.gamut_view = OKLabGamutSelector(self.main)
    self.plane_view = OKLabHuePlaneSelector(self.main)
    self.chroma_view = OKLabChromaLightnessSelector(self.main)

    self.plane_view.setVisible(False)
    self.chroma_view.setVisible(False)

    self.current_view = self.gamut_view

    self.layout.addWidget(self.current_view, 0, 0)
    self.layout.addWidget(self.gamut, 1, 0)
    self.layout.addWidget(self.plane, 2, 0)
    self.layout.addWidget(self.chroma, 3, 0)

    self.setWidget(self.main)
    

  def set_display(self):
    if self.gamut.isChecked():
      self.layout.addWidget(self.gamut_view, 0, 0)
      self.plane_view.setVisible(False)
      self.chroma_view.setVisible(False)
      self.gamut_view.setVisible(True)
      self.current_view = self.gamut_view

    if self.plane.isChecked():
      self.layout.addWidget(self.plane_view, 0, 0)
      self.plane_view.setVisible(True)
      self.chroma_view.setVisible(False)
      self.gamut_view.setVisible(False)
      self.current_view = self.plane_view

    if self.chroma.isChecked():
      self.layout.addWidget(self.chroma_view, 0, 0)
      self.plane_view.setVisible(False)
      self.chroma_view.setVisible(True)
      self.gamut_view.setVisible(False)
      self.current_view = self.chroma_view


  def canvasChanged(self):
    pass

#lab_colour_picker().exec_()
Krita.instance().addDockWidgetFactory(DockWidgetFactory("lab_colour_picker", DockWidgetFactoryBase.DockRight, lab_colour_picker)) 
