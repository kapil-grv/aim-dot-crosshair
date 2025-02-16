# main.py
import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon

class DotOverlay(QtWidgets.QWidget):
    def __init__(self, parent=None, dotDiameter=5, dotColor="#00FFFF", shape="Circle", imagePath=None):
        super().__init__(parent)
        self.dotDiameter = dotDiameter
        self.dotColor = dotColor
        self.shape = shape
        self.imagePath = imagePath
        self.resize(dotDiameter, dotDiameter)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.WindowTransparentForInput |
            QtCore.Qt.Tool  # Prevents taskbar icon
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.centerOnScreen()

    def centerOnScreen(self):
        screen_rect = QtWidgets.QApplication.primaryScreen().geometry()
        self.move(screen_rect.center() - self.rect().center())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        color = QtGui.QColor(self.dotColor)
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.NoPen)
        
        if self.imagePath:
            try:
                pixmap = QtGui.QPixmap(self.imagePath)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        self.dotDiameter, 
                        self.dotDiameter,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation
                    )
                    painter.drawPixmap(0, 0, pixmap)
                else:
                    self._drawFallbackShape(painter)
            except Exception as e:
                print(f"Error loading image: {e}")
                self._drawFallbackShape(painter)
        else:
            self._drawFallbackShape(painter)

    def _drawFallbackShape(self, painter):
        if self.shape == "Circle":
            painter.drawEllipse(0, 0, self.dotDiameter, self.dotDiameter)
        else:  # Default to square if shape is invalid
            painter.drawRect(0, 0, self.dotDiameter, self.dotDiameter)

    def updateDot(self, diameter, color, shape, imagePath=None):
        self.dotDiameter = diameter
        self.dotColor = color
        self.shape = shape
        self.imagePath = imagePath
        self.resize(diameter, diameter)
        self.centerOnScreen()
        self.update()

class ControlPanel(QtWidgets.QWidget):
    def __init__(self, overlay, trayIcon):
        super().__init__()
        self.overlay = overlay
        self.trayIcon = trayIcon
        self.initUI()
        self.loadSettings()
    
    def initUI(self):
        self.setWindowTitle("Aim Dot Controls")
        self.setGeometry(100, 100, 350, 300)
        self.setStyleSheet(self._getStyleSheet())
        
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self._setupWidgets(layout)
        
        shortcutLabel = QtWidgets.QLabel("Shortcut: Press 'Ctrl+H' to show/hide crosshair")
        shortcutLabel.setStyleSheet("color: #888; font-style: italic; padding: 10px; border-radius: 3px;")
        layout.addWidget(shortcutLabel)

        # Create PayPal label with icon and text, matching the theme
        paypal_html = '''
        <a href="https://www.paypal.com/paypalme/kapilgrv" style="text-decoration:none; color: #888;">
            Support me on PayPal - @kapilgrv
        </a>
        '''

        paypalLabel = QtWidgets.QLabel(paypal_html)
        paypalLabel.setOpenExternalLinks(True)  # Makes the link clickable
        paypalLabel.setStyleSheet("font-style: italic; padding: 10px; border-radius: 3px; text-align: centre;")
        layout.addWidget(paypalLabel)
        self.setLayout(layout)
        
        self.hideShowShortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("Ctrl+H"), self)
        self.hideShowShortcut.activated.connect(self.toggleOverlay)

    def _setupWidgets(self, layout):
        # Title
        title = QtWidgets.QLabel("Aim Dot Customizer")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px; border-radius: 3px;")
        layout.addWidget(title, alignment=QtCore.Qt.AlignCenter)
        
        # Size control
        sizeGroup = QtWidgets.QGroupBox("Size")
        sizeLayout = QtWidgets.QVBoxLayout()
        
        self.sizeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sizeSlider.setMinimum(3)
        self.sizeSlider.setMaximum(100)
        self.sizeSlider.setValue(self.overlay.dotDiameter)
        self.sizeSlider.valueChanged.connect(self.updateOverlay)
        
        self.sizeLabel = QtWidgets.QLabel(f"Size: {self.sizeSlider.value()}")
        self.sizeSlider.valueChanged.connect(
            lambda v: self.sizeLabel.setText(f"Size: {v}"))
        
        sizeLayout.addWidget(self.sizeLabel)
        sizeLayout.addWidget(self.sizeSlider)
        sizeGroup.setLayout(sizeLayout)
        layout.addWidget(sizeGroup)
        
        # Color control
        colorGroup = QtWidgets.QGroupBox("Color")
        colorLayout = QtWidgets.QVBoxLayout()
        
        self.colorPicker = QtWidgets.QPushButton("Choose Color")
        self.colorPicker.clicked.connect(self.pickColor)
        self.currentColorLabel = QtWidgets.QLabel(f"Current Color: {self.overlay.dotColor}")
        
        colorLayout.addWidget(self.currentColorLabel)
        colorLayout.addWidget(self.colorPicker)
        colorGroup.setLayout(colorLayout)
        layout.addWidget(colorGroup)
        
        # Shape control
        shapeGroup = QtWidgets.QGroupBox("Shape")
        shapeLayout = QtWidgets.QVBoxLayout()
        
        self.shapeSelector = QtWidgets.QComboBox()
        self.shapeSelector.addItems(["Circle", "Square", "Custom Image"])
        self.shapeSelector.currentTextChanged.connect(self.updateShape)
        
        self.imageUploadBtn = QtWidgets.QPushButton("Upload Image/SVG")
        self.imageUploadBtn.clicked.connect(self.uploadImage)
        self.imageUploadBtn.setVisible(False)
        
        self.currentImageLabel = QtWidgets.QLabel()
        self.currentImageLabel.setVisible(False)
        
        shapeLayout.addWidget(self.shapeSelector)
        shapeLayout.addWidget(self.imageUploadBtn)
        shapeLayout.addWidget(self.currentImageLabel)
        shapeGroup.setLayout(shapeLayout)
        layout.addWidget(shapeGroup)
        
        # Minimize button
        self.hideButton = QtWidgets.QPushButton("Minimize to Tray")
        self.hideButton.clicked.connect(self.minimizeToTray)
        layout.addWidget(self.hideButton)

    def _getStyleSheet(self):
        return """
            QWidget {
                background-color: #FFFFFF; /* Light, neutral background */
                color: #333333;            /* Dark text for high contrast */
                font-size: 14px;
                font-family: 'Segoe UI', sans-serif;
            }
            
            QGroupBox {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                margin-top: 10px;
                padding: 10px;
                background-color: #FFFFFF;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
                color: #333333;
            }
            
            QPushButton {
                background-color: #F7F7F7;
                padding: 10px 15px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                color: #333333;
                font-weight: bold;
                transition: background-color 0.2s ease;
            }
            
            QPushButton:hover {
                background-color: #E8E8E8;
            }
            
            QPushButton:pressed {
                background-color: #DADADA;
            }
            
            QComboBox {
                background-color: #F7F7F7;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                color: #333333;
            }
            
            QComboBox:hover {
                border: 1px solid #AAAAAA;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: url(resources/down_arrow.png);
                width: 12px;
                height: 12px;
            }
            
            QSlider::groove:horizontal {
                height: 6px;
                background: #E0E0E0;
                border-radius: 3px;
            }
            
            QSlider::handle:horizontal {
                background: #CCCCCC;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
                border: 1px solid #CCCCCC;
            }
            
            QSlider::handle:horizontal:hover {
                background: #BBBBBB;
            }
            
            QSlider::handle:horizontal:pressed {
                background: #AAAAAA;
            }
        """

    def updateOverlay(self):
        shape = self.shapeSelector.currentText()
        imagePath = None
        if shape == "Custom Image":
            imagePath = self.overlay.imagePath
        self.overlay.updateDot(
            self.sizeSlider.value(),
            self.overlay.dotColor,
            shape,
            imagePath
        )

    def updateShape(self, shape):
        self.imageUploadBtn.setVisible(shape == "Custom Image")
        self.currentImageLabel.setVisible(shape == "Custom Image")
        self.updateOverlay()

    def pickColor(self):
        color = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(self.overlay.dotColor),
            self,
            "Choose Crosshair Color"
        )
        if color.isValid():
            self.overlay.updateDot(
                self.overlay.dotDiameter,
                color.name(),
                self.overlay.shape
            )
            self.currentColorLabel.setText(f"Current Color: {color.name()}")

    def uploadImage(self):
        filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Image or SVG",
            "",
            "Images (*.png *.jpg *.bmp *.svg)"
        )
        if filePath:
            self.overlay.updateDot(
                self.overlay.dotDiameter,
                self.overlay.dotColor,
                "Custom Image",
                filePath
            )
            self.currentImageLabel.setText(f"Image: {os.path.basename(filePath)}")
            self.currentImageLabel.setVisible(True)

    def minimizeToTray(self):
        self.hide()
        if hasattr(self, 'parent') and self.parent():
            self.parent().hide()  # Hide the main window
        self.trayIcon.showMessage(
            "Aim Dot",
            "Application minimized to tray",
            QtWidgets.QSystemTrayIcon.Information,
            2000
        )

    def toggleOverlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def loadSettings(self):
        settings = QtCore.QSettings("Aim Dot", "Settings")
        
        size = settings.value("size", 5, type=int)
        color = settings.value("color", "#00FFFF")
        shape = settings.value("shape", "Circle")
        imagePath = settings.value("imagePath", None)
        
        self.sizeSlider.setValue(size)
        self.currentColorLabel.setText(f"Current Color: {color}")
        self.shapeSelector.setCurrentText(shape)
        
        if imagePath and os.path.exists(imagePath):
            self.currentImageLabel.setText(f"Image: {os.path.basename(imagePath)}")
            self.currentImageLabel.setVisible(shape == "Custom Image")
        
        self.overlay.updateDot(size, color, shape, imagePath)

    def saveSettings(self):
        settings = QtCore.QSettings("Aim Dot", "Settings")
        settings.setValue("size", self.overlay.dotDiameter)
        settings.setValue("color", self.overlay.dotColor)
        settings.setValue("shape", self.overlay.shape)
        settings.setValue("imagePath", self.overlay.imagePath)

    def closeEvent(self, event):
        self.saveSettings()
        event.ignore()  # Prevent window from closing
        self.minimizeToTray()

class SystemTrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon_path, parent=None):
        super().__init__(parent)
        self.setIcon(self._loadIcon(icon_path))
        self.setToolTip("Aim Dot")
        self._setupMenu(parent)
        self.show()
        
        # Connect activated signal
        self.activated.connect(self._handleActivated)

    def _loadIcon(self, icon_path):
        icon = QtGui.QIcon(icon_path)
        if icon.isNull():
            print("Warning: Using fallback icon")
            pixmap = QtGui.QPixmap(32, 32)
            pixmap.fill(QtGui.QColor("#00FFFF"))
            return QtGui.QIcon(pixmap)
        return icon

    def _setupMenu(self, parent):
        self.menu = QtWidgets.QMenu(parent)
        
        self.showAction = self.menu.addAction("Show Controls")
        self.showAction.triggered.connect(parent.showNormal)
        
        self.toggleAction = self.menu.addAction("Toggle Crosshair")
        self.toggleAction.triggered.connect(
            lambda: parent.findChild(ControlPanel).toggleOverlay())
        
        self.menu.addSeparator()
        
        self.exitAction = self.menu.addAction("Exit")
        self.exitAction.triggered.connect(self._quit_application)
        
        self.setContextMenu(self.menu)

    def _handleActivated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            control_panel = self.parent().findChild(ControlPanel)
            if control_panel and not control_panel.isVisible():
                control_panel.show()

    def _quit_application(self):
        control_panel = self.parent().findChild(ControlPanel)
        if control_panel:
            control_panel.saveSettings()
        QtWidgets.QApplication.quit()

def create_resources():
    """Create necessary resource files if they don't exist."""
    resources_dir = "resources"
    if not os.path.exists(resources_dir):
        os.makedirs(resources_dir)
    
    # Create default icon if it doesn't exist
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))

    icon_path = os.path.join(base_path, "resources", "icon.png")
    if not os.path.exists(icon_path):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtGui.QColor("#00FFFF"))
        pixmap.save(icon_path)
    
    # Create down arrow icon for combo box
    arrow_path = os.path.join(resources_dir, "down_arrow.png")
    if not os.path.exists(arrow_path):
        pixmap = QtGui.QPixmap(12, 12)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setPen(QtGui.QPen(QtGui.QColor("white"), 2))
        painter.drawLine(2, 4, 6, 8)
        painter.drawLine(6, 8, 10, 4)
        painter.end()
        pixmap.save(arrow_path)
    
    return icon_path

def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Prevent app from closing when windows are closed
    
    # Set application-wide attributes
    app.setApplicationName("Aim Dot")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Aim Dot")
    
    # Create necessary resource files
    icon_path = create_resources()
    # Set the application icon for the taskbar
    app.setWindowIcon(QIcon(icon_path))
    
    # Create main window
    main_window = QtWidgets.QMainWindow()
    main_window.setWindowTitle("Aim Dot")
    
    # Setup system tray
    tray_icon = SystemTrayApp(icon_path, main_window)
    
    # Create overlay and control panel
    overlay = DotOverlay(dotDiameter=5)
    control_panel = ControlPanel(overlay, tray_icon)
    
    # Set control panel as central widget
    main_window.setCentralWidget(control_panel)
    
    # Show the UI
    overlay.show()
    control_panel.show()
    main_window.show()  # Show window on startup
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())