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

        self.maxCoverWidth = 200

        self.cover          = QLabel()
        self.cover_img      = QPixmap('Images/no_image.jpg')
        self.cover.setAlignment(Qt.AlignTop)
        self.cover.setPixmap(self.cover_img.scaledToWidth(self.maxCoverWidth))
        self.cover.setFixedWidth(self.maxCoverWidth)

        self.name           = QLabel("No movie selected...")
        self.release_date   = QLabel("Release date: ??-??-????")
        self.country        = QLabel("Country: ?")
        self.genre          = QLabel("Genre: ?")
        self.duration       = QLabel("Duration: ??:??:??")
        self.rating         = QLabel("Rating: ?")
        self.director       = QLabel("Director: ?")
        self.cast           = QLabel("Cast: ?")
        self.description    = QLabel("Description: ?")
        self.trailer        = QLabel("Trailer: ?")
        self.tmdb           = QLabel("TMDB: ?")

        self.trailer.mousePressEvent    = self.TrailerClicked
        self.tmdb.mousePressEvent       = self.TmdbClicked

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
        self.tmdb.setWordWrap(True)

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
        self.layout.addWidget(self.tmdb,            10, 1)

        self.setWidget(self.widget)

    def TrailerClicked(self, e):
        #Get youtube code from text and append to url
        yt_code = self.trailer.text()[9:]
        yt_url = f"https://www.youtube.com/watch?v={yt_code}"

        #Open URL
        QDesktopServices.openUrl(QUrl(yt_url))

    def TmdbClicked(self, e):
        #Get TMDB code from text and append to url
        tmdb_code = self.tmdb.text()[6:]
        tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_code}"

        #Open URL
        QDesktopServices.openUrl(QUrl(tmdb_url))

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

        self.maxCoverWidth = 200

        self.cover          = QLabel()
        self.cover_img      = QPixmap('Images/no_image.jpg')
        self.cover.setAlignment(Qt.AlignTop)
        self.cover.setPixmap(self.cover_img.scaledToWidth(self.maxCoverWidth))
        self.cover.setFixedWidth(self.maxCoverWidth)

        self.name           = QLabel("No series selected...")
        self.release_date   = QLabel("Release date: ??-??-????")
        self.genre          = QLabel("Genre: ?")
        self.num_seasons    = QLabel("Seasons: ?")
        self.duration       = QLabel("Episode duration: ? min")
        self.rating         = QLabel("Rating: ?")
        self.director       = QLabel("Director: ?")
        self.cast           = QLabel("Cast: ?")
        self.description    = QLabel("Description: ?")
        self.trailer        = QLabel("Trailer: ?")
        self.tmdb           = QLabel("TMDB: ?")

        self.trailer.mousePressEvent    = self.TrailerClicked
        self.tmdb.mousePressEvent       = self.TmdbClicked

        self.name.setFont(QFont('Arial', 14, QFont.Bold))

        #Enable wordwrap for all labels
        self.name.setWordWrap(True)
        self.release_date.setWordWrap(True)
        self.genre.setWordWrap(True)
        self.num_seasons.setWordWrap(True)
        self.duration.setWordWrap(True)
        self.rating.setWordWrap(True)
        self.director.setWordWrap(True)
        self.cast.setWordWrap(True)
        self.description.setWordWrap(True)
        self.trailer.setWordWrap(True)
        self.tmdb.setWordWrap(True)

        #Add widgets
        self.layout.addWidget(self.name,            0, 0, 1, 2)
        self.layout.addWidget(self.cover,           1, 0, 10, 1)
        self.layout.addWidget(self.release_date,    1, 1)
        self.layout.addWidget(self.genre,           2, 1)
        self.layout.addWidget(self.num_seasons,     3, 1)
        self.layout.addWidget(self.duration,        4, 1)
        self.layout.addWidget(self.rating,          5, 1)
        self.layout.addWidget(self.director,        6, 1)
        self.layout.addWidget(self.cast,            7, 1)
        self.layout.addWidget(self.description,     8, 1)
        self.layout.addWidget(self.trailer,         9, 1)
        self.layout.addWidget(self.tmdb,            10, 1)

        #Add widget with all items to the scrollarea (self)
        self.setWidget(self.widget)

    def TrailerClicked(self, e):
        #Get youtube code from text and append to url
        yt_code = self.trailer.text()[9:]
        yt_url = f"https://www.youtube.com/watch?v={yt_code}"

        #Open URL
        QDesktopServices.openUrl(QUrl(yt_url))

    def TmdbClicked(self, e):
        #Get TMDB code from text and append to url
        tmdb_code = self.tmdb.text()[6:]
        tmdb_url = f"https://www.themoviedb.org/tv/{tmdb_code}"

        #Open URL
        QDesktopServices.openUrl(QUrl(tmdb_url))


