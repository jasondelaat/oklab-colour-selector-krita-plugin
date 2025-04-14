"""Contains widgets used by different colour picker views/classes.

Indicator: The little circle which indicates which colour is currently
    selected.

Slider: Basically just a regular slider but with the ability to set
    the label, default value and valueChanged action in the constructor.

SelectorSurface: The actual thing you click on to pick a colour. This
    class is created by the 'makeSurface' function which precalculates and
    stores some data about the pixels on the surface so it can simply be
    looked up instead of having to recalculate it every time the surface
    updates.

"""
import math

from krita import *

from .oklab import *

class Indicator(QWidget):
    """Really just a static image of two concentric circles, one white and one black. """

    # --------------------------------------------------------------------------------
    #
    # Note:
    # I'm sure there's a better way to do this. Probably an existing
    # icon or other image built-in to Krita that I could use but I
    # couldn't find it. And for some reason I couldn't get the plug-in
    # to load an image from the plug-in directory so this abomination
    # is what I came up with. It does the job for now.
    #
    # --------------------------------------------------------------------------------
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


class Slider(QWidget):
    def __init__(self, parent, label, value, action):
        super().__init__(parent)
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.slider = QSlider(1, self)
        self.slider.setRange(0, 1000)
        self.slider.setValue(value)
        self.slider.valueChanged.connect(action)
        self.valueChanged = self.slider.valueChanged

        layout.addWidget(QLabel(label, self))
        layout.addWidget(self.slider)

    def setValue(self, value):
        return self.slider.setValue(value)

    def value(self):
        return self.slider.value()

    def disconnect(self):
        self.slider.disconnect()

def makeSurface(size):
    """Creates a new 'Surface' class to build colour selectors on top
    of. The surface is a QLabel which displays a square image of
    'size'X'size' pixels.

    The main purpose of this function is to pre-cacluate useful data
    for each pixel in the image to save on processing time during
    update.

    The data calculated are:
        - the distance of the pixel from the center of the image
        - the hue angle of the pixel (from the center)
        - the cosine and sine of the hue angle.

    """
    metrics = {}
    for y in range(size):
        ay = size/2 - y
        for x in range(size):
            ax = x - size/2
            hue = math.atan2(ay, ax)
            length = math.sqrt(ax*ax + ay*ay)
            if length <= size/2:
                col = metrics.get(x, {})
                col[y] = (2*length/size, hue, math.cos(hue), math.sin(hue))
                metrics[x] = col

    
    class Surface(QLabel):
        def __init__(self, parent, display_size):
            super().__init__(parent)
            self.position = (display_size//2, display_size//2)
            self.indicator = Indicator(self)
            self.image_size = size
            self.display_size = display_size

            self.indicator.move(*self.position)
            
        # Derived classes *must* define self.rgb_data before calling this method.
        def update_image(self):
            i_size = self.image_size
            d_size = self.display_size
            self.image = QImage(bytes(self.rgb_data), i_size, i_size, QImage.Format_RGBA8888).scaled(d_size, d_size)
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
            colour_picker = win.qwindow().findChild(QDockWidget, 'lab_colour_picker')
            colour_picker.foreground = selected_colour
            view.setForeGroundColor(selected_colour)
            self.indicator.move(self.position[0]-6, self.position[1]-6)

        def mouseMoveEvent(self, ev):
            self.position = (ev.x(), ev.y())
            self.updateForegroundColour()

        def mousePressEvent(self, ev):
            self.position = (ev.x(), ev.y())
            self.updateForegroundColour()

        def foregroundColorToLab(self):
            fg = Krita.instance().activeWindow().activeView().foregroundColor()
            #if not win:
            #    return

            #view = win.activeView()
            #if not view:
            #    return

            #fg = view.foregroundColor()
            #if not fg:
            #    return

            comp = fg.components()
            rgb = RGB(comp[2], comp[1], comp[0])
            return srgb_to_oklab(rgb)

    Surface.pixel_metrics = metrics
    return Surface

SelectorSurface = makeSurface(150)
