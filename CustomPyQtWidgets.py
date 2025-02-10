from PyQt5.QtGui import QIcon, QFont, QImage, QPixmap, QColor, QDesktopServices
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QObject, pyqtSignal, 
    QRunnable, pyqtSlot, QThreadPool, QModelIndex, QAbstractItemModel, QVariant, QUrl
)
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QLabel, QPushButton,
    QListWidget, QWidget, QFileDialog, QCheckBox, QSizePolicy, QHBoxLayout,
    QDialog, QFormLayout, QDialogButtonBox, QTabWidget, QListWidgetItem,
    QSpinBox, QMenu, QAction, QTextEdit, QGridLayout, QMessageBox, QListView,
    QTreeWidget, QTreeWidgetItem, QTreeView, QScrollArea
)

# class EntryInfoBox(QWidget):
class EntryInfoBox(QScrollArea):
    def __init__(self):
        super().__init__()

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        # self.setWidgetResizable(False)
        self.setAlignment(Qt.AlignTop)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.widget = QWidget()

        self.layout = QGridLayout(self.widget)
        self.layout.setAlignment(Qt.AlignTop)

        self.width = self.width()
        print(self.width)

        self.maxTextWidth = int((self.width * 3) / 5)
        # self.maxCoverWidth = int((self.width * 2) / 5)
        self.maxCoverWidth = 200

        self.cover          = QLabel()
        self.cover_img      = QPixmap('Images/no_image.jpg')

        # self.cover.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.cover.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.cover.setAlignment(Qt.AlignTop)

        self.cover.setPixmap(self.cover_img.scaledToWidth(self.maxCoverWidth))
        # self.cover.setMaximumWidth(self.maxCoverWidth)
        self.cover.setFixedWidth(self.maxCoverWidth)

        self.name           = QLabel("Ice Age")
        self.release_date   = QLabel("2000")
        self.country        = QLabel("English")
        self.genre          = QLabel("Fun")
        self.duration       = QLabel("1h40m")
        self.rating         = QLabel("9.0")
        self.director       = QLabel("Dave Grohl")
        self.cast           = QLabel("Josh Peck")
        self.description    = QLabel("Amazing movie about Ice Age time!")
        self.plot           = QLabel("They bring back the human baby")
        self.trailer        = QLabel("https://youtube.com")
        self.imdb           = QLabel("https://www.themoviedb.org/movie/11852")

        # self.release_date.setMaximumWidth(self.maxTextWidth)
        # self.country.setMaximumWidth(self.maxTextWidth)
        # self.genre.setMaximumWidth(self.maxTextWidth)
        # self.duration.setMaximumWidth(self.maxTextWidth)
        # self.rating.setMaximumWidth(self.maxTextWidth)
        # self.director.setMaximumWidth(self.maxTextWidth)
        # self.cast.setMaximumWidth(self.maxTextWidth)
        # self.description.setMaximumWidth(self.maxTextWidth)
        # self.plot.setMaximumWidth(self.maxTextWidth)
        # self.trailer.setMaximumWidth(self.maxTextWidth)
        # self.imdb.setMaximumWidth(self.maxTextWidth)

        # self.name.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.release_date.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.country.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.genre.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.duration.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.rating.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.director.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.cast.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.description.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.plot.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.trailer.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # self.imdb.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # self.name.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.release_date.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.country.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.genre.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.duration.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.rating.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.director.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.cast.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.description.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.plot.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.trailer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # self.imdb.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.trailer.mousePressEvent    = self.TrailerClicked
        self.imdb.mousePressEvent       = self.ImdbClicked

        # self.name.setFont(QFont('Roboto', 14, QFont.Bold))
        self.name.setFont(QFont('Arial', 14, QFont.Bold))

        # self.cast.setWordWrap(True)
        # self.description.setWordWrap(True)
        # self.plot.setWordWrap(True)
        self.name.setWordWrap(True)
        self.release_date.setWordWrap(True)
        self.country.setWordWrap(True)
        self.genre.setWordWrap(True)
        self.duration.setWordWrap(True)
        self.rating.setWordWrap(True)
        self.director.setWordWrap(True)
        self.cast.setWordWrap(True)
        self.description.setWordWrap(True)
        self.plot.setWordWrap(True)
        self.trailer.setWordWrap(True)
        self.imdb.setWordWrap(True)

        # self.layout.addWidget(self.name,            0, 0, 1, 2)
        # self.layout.addWidget(self.cover,           1, 0, 11, 1, Qt.AlignTop)
        # self.layout.addWidget(self.release_date,    1, 1, Qt.AlignTop)
        # self.layout.addWidget(self.country,         2, 1, Qt.AlignTop)
        # self.layout.addWidget(self.genre,           3, 1, Qt.AlignTop)
        # self.layout.addWidget(self.duration,        4, 1, Qt.AlignTop)
        # self.layout.addWidget(self.rating,          5, 1, Qt.AlignTop)
        # self.layout.addWidget(self.director,        6, 1, Qt.AlignTop)
        # self.layout.addWidget(self.cast,            7, 1, Qt.AlignTop)
        # self.layout.addWidget(self.description,     8, 1, Qt.AlignTop)
        # self.layout.addWidget(self.plot,            9, 1, Qt.AlignTop)
        # self.layout.addWidget(self.trailer,         10, 1, Qt.AlignTop)
        # self.layout.addWidget(self.imdb,            11, 1, Qt.AlignTop)

        self.layout.addWidget(self.name,            0, 0, 1, 2)
        self.layout.addWidget(self.cover,           1, 0, 11, 1)
        self.layout.addWidget(self.release_date,    1, 1)
        self.layout.addWidget(self.country,         2, 1)
        self.layout.addWidget(self.genre,           3, 1)
        self.layout.addWidget(self.duration,        4, 1)
        self.layout.addWidget(self.rating,          5, 1)
        self.layout.addWidget(self.director,        6, 1)
        self.layout.addWidget(self.cast,            7, 1)
        self.layout.addWidget(self.description,     8, 1)
        self.layout.addWidget(self.plot,            9, 1)
        self.layout.addWidget(self.trailer,         10, 1)
        self.layout.addWidget(self.imdb,            11, 1)

        self.setWidget(self.widget)

        # self.layout.setRowStretch(12, 1)

        # self.setText(movies_info_string)

    def TrailerClicked(self, e):
        QDesktopServices.openUrl(QUrl(self.trailer.text()))

    def ImdbClicked(self, e):
        QDesktopServices.openUrl(QUrl(self.imdb.text()))

    def mousePressEvent(self, e):
        # self.anchor = self.anchorAt(e.pos())
        # if self.anchor:
        #     QApplication.setOverrideCursor(Qt.PointingHandCursor)
        print(f"flags: {e.flags()}")
        print(f"type: {e.type()}")
        # if e == self.trailer:
        #     QDesktopServices.openUrl(QUrl(self.trailer.text))


    # def mouseReleaseEvent(self, e):
    #     if self.anchor:
    #         QDesktopServices.openUrl(QUrl(self.anchor))
    #         QApplication.setOverrideCursor(Qt.ArrowCursor)
    #         self.anchor = None

