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

class MovieInfoBox(QScrollArea):
    def __init__(self):
        super().__init__()

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignTop)

        self.widget = QWidget()

        self.layout = QGridLayout(self.widget)
        self.layout.setAlignment(Qt.AlignTop)

        self.width = self.width()
        print(self.width)

        self.maxCoverWidth = 200

        self.cover          = QLabel()
        self.cover_img      = QPixmap('Images/no_image.jpg')
        self.cover.setAlignment(Qt.AlignTop)
        self.cover.setPixmap(self.cover_img.scaledToWidth(self.maxCoverWidth))
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
        self.trailer        = QLabel("https://youtube.com")
        self.imdb           = QLabel("https://www.themoviedb.org/movie/11852")

        self.trailer.mousePressEvent    = self.TrailerClicked
        self.imdb.mousePressEvent       = self.ImdbClicked

        self.name.setFont(QFont('Arial', 14, QFont.Bold))

        self.name.setWordWrap(True)
        self.release_date.setWordWrap(True)
        self.country.setWordWrap(True)
        self.genre.setWordWrap(True)
        self.duration.setWordWrap(True)
        self.rating.setWordWrap(True)
        self.director.setWordWrap(True)
        self.cast.setWordWrap(True)
        self.description.setWordWrap(True)
        self.trailer.setWordWrap(True)
        self.imdb.setWordWrap(True)

        self.layout.addWidget(self.name,            0, 0, 1, 2)
        self.layout.addWidget(self.cover,           1, 0, 10, 1)
        self.layout.addWidget(self.release_date,    1, 1)
        self.layout.addWidget(self.country,         2, 1)
        self.layout.addWidget(self.genre,           3, 1)
        self.layout.addWidget(self.duration,        4, 1)
        self.layout.addWidget(self.rating,          5, 1)
        self.layout.addWidget(self.director,        6, 1)
        self.layout.addWidget(self.cast,            7, 1)
        self.layout.addWidget(self.description,     8, 1)
        self.layout.addWidget(self.trailer,         9, 1)
        self.layout.addWidget(self.imdb,            10, 1)

        self.setWidget(self.widget)

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

class SeriesInfoBox(QScrollArea):
    def __init__(self):
        super().__init__()

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setAlignment(Qt.AlignTop)

        self.widget = QWidget()

        self.layout = QGridLayout(self.widget)
        self.layout.setAlignment(Qt.AlignTop)

        self.width = self.width()
        print(self.width)

        self.maxCoverWidth = 200

        self.cover          = QLabel()
        self.cover_img      = QPixmap('Images/no_image.jpg')
        self.cover.setAlignment(Qt.AlignTop)
        self.cover.setPixmap(self.cover_img.scaledToWidth(self.maxCoverWidth))
        self.cover.setFixedWidth(self.maxCoverWidth)

        self.name           = QLabel("Ice Age")
        self.release_date   = QLabel("2000")
        self.country        = QLabel("English")
        self.genre          = QLabel("Fun")
        self.num_seasons    = QLabel("6")
        self.duration       = QLabel("1h40m")
        self.rating         = QLabel("9.0")
        self.director       = QLabel("Dave Grohl")
        self.cast           = QLabel("Josh Peck")
        self.description    = QLabel("Amazing movie about Ice Age time!")
        self.trailer        = QLabel("https://youtube.com")
        self.imdb           = QLabel("https://www.themoviedb.org/movie/11852")

        self.trailer.mousePressEvent    = self.TrailerClicked
        self.imdb.mousePressEvent       = self.ImdbClicked

        self.name.setFont(QFont('Arial', 14, QFont.Bold))

        self.name.setWordWrap(True)
        self.release_date.setWordWrap(True)
        self.country.setWordWrap(True)
        self.genre.setWordWrap(True)
        self.num_seasons.setWordWrap(True)
        self.duration.setWordWrap(True)
        self.rating.setWordWrap(True)
        self.director.setWordWrap(True)
        self.cast.setWordWrap(True)
        self.description.setWordWrap(True)
        self.trailer.setWordWrap(True)
        self.imdb.setWordWrap(True)

        self.layout.addWidget(self.name,            0, 0, 1, 2)
        self.layout.addWidget(self.cover,           1, 0, 11, 1)
        self.layout.addWidget(self.release_date,    1, 1)
        self.layout.addWidget(self.country,         2, 1)
        self.layout.addWidget(self.genre,           3, 1)
        self.layout.addWidget(self.num_seasons,     4, 1)
        self.layout.addWidget(self.duration,        5, 1)
        self.layout.addWidget(self.rating,          6, 1)
        self.layout.addWidget(self.director,        7, 1)
        self.layout.addWidget(self.cast,            8, 1)
        self.layout.addWidget(self.description,     9, 1)
        self.layout.addWidget(self.trailer,         10, 1)
        self.layout.addWidget(self.imdb,            11, 1)

        self.setWidget(self.widget)

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


