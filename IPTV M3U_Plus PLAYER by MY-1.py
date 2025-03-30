import sys
import os
from os import path
import time
import requests
import subprocess
import configparser
import re
import json
import html
from lxml import etree, html
from datetime import datetime
from dateutil import parser, tz
import xml.etree.ElementTree as ET
from PyQt5.QtGui import QIcon, QFont, QImage, QPixmap, QColor
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QObject, pyqtSignal, 
    QRunnable, pyqtSlot, QThreadPool, QModelIndex, QAbstractItemModel, QVariant
)
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QLabel, QPushButton,
    QListWidget, QWidget, QFileDialog, QCheckBox, QSizePolicy, QHBoxLayout,
    QDialog, QFormLayout, QDialogButtonBox, QTabWidget, QListWidgetItem,
    QSpinBox, QMenu, QAction, QTextEdit, QGridLayout, QMessageBox, QListView,
    QTreeWidget, QTreeWidgetItem, QTreeView, QAction, QMenu, QComboBox
)

from AccountManager import AccountManager
from CustomPyQtWidgets import MovieInfoBox, SeriesInfoBox
from Threadpools import FetchDataWorker, SearchWorker, EPGWorker, MovieInfoFetcher, SeriesInfoFetcher, ImageFetcher

CUSTOM_USER_AGENT = (
    "Connection: Keep-Alive User-Agent: okhttp/5.0.0-alpha.2 "
    "Accept-Encoding: gzip, deflate"
)

is_windows  = sys.platform.startswith('win')
is_mac      = sys.platform.startswith('darwin')
is_linux    = sys.platform.startswith('linux')

class IPTVPlayerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPTV Player V3.5")
        self.resize(1300, 900)

        self.user_data_file = 'userdata.ini'

        self.path_to_window_icon    = path.abspath(path.join(path.dirname(__file__), 'Images/TV_icon.ico'))
        self.path_to_no_img         = path.abspath(path.join(path.dirname(__file__), 'Images/no_image.jpg'))
        self.path_to_loading_img    = path.abspath(path.join(path.dirname(__file__), 'Images/loading-icon.png'))
        self.path_to_404_img        = path.abspath(path.join(path.dirname(__file__), 'Images/404_not_found.png'))

        self.path_to_home_icon      = path.abspath(path.join(path.dirname(__file__), 'Images/home_tab_icon.ico'))
        self.path_to_live_icon      = path.abspath(path.join(path.dirname(__file__), 'Images/tv_tab_icon.ico'))
        self.path_to_movies_icon    = path.abspath(path.join(path.dirname(__file__), 'Images/movies_tab_icon.ico'))
        self.path_to_series_icon    = path.abspath(path.join(path.dirname(__file__), 'Images/series_tab_icon.ico'))
        self.path_to_favorites_icon = path.abspath(path.join(path.dirname(__file__), 'Images/favorite_tab_icon.ico'))
        self.path_to_info_icon      = path.abspath(path.join(path.dirname(__file__), 'Images/info_tab_icon.ico'))
        self.path_to_settings_icon  = path.abspath(path.join(path.dirname(__file__), 'Images/settings_tab_icon.ico'))

        self.path_to_search_icon    = path.abspath(path.join(path.dirname(__file__), 'Images/search_bar_icon.ico'))
        self.path_to_sorting_icon   = path.abspath(path.join(path.dirname(__file__), 'Images/sorting_icon.ico'))
        self.path_to_clear_btn_icon = path.abspath(path.join(path.dirname(__file__), 'Images/clear_button_icon.ico'))
        self.path_to_go_back_icon   = path.abspath(path.join(path.dirname(__file__), 'Images/go_back_icon.ico'))

        self.path_to_account_icon       = path.abspath(path.join(path.dirname(__file__), 'Images/account_manager_icon.ico'))
        self.path_to_mediaplayer_icon   = path.abspath(path.join(path.dirname(__file__), 'Images/film_camera_icon.ico'))

        self.setWindowIcon(QIcon(self.path_to_window_icon))

        self.default_font_size      = 10
        self.go_back_text           = " Go back"
        self.all_categories_text    = " All"

        #navigation level indicates in what list level we are
        #LIVE and VOD have no navigation levels.
        #Series has 0: Series, 1: Seasons, 2: Episodes
        self.series_navigation_level = 0
        self.finished_fetching_series_info = False

        #Make history list index a list in order to achieve pass by reference
        self.streaming_search_history_list      = []
        self.streaming_search_history_list_idx  = [0]
        self.category_search_history_list       = []
        self.category_search_history_list_idx   = [0]
        self.max_search_history_size            = 30

        #Previous clicked item for preventing loading the same item multiple times
        self.prev_clicked_category_item = {
            'LIVE': 0,
            'Movies': 0,
            'Series': 0
        }
        self.prev_clicked_streaming_item        = 0
        self.prev_double_clicked_streaming_item = 0

        self.categories_per_stream_type = {}
        self.entries_per_stream_type = {
            'LIVE': [],
            'Movies': [],
            'Series': []
        }

        #Loaded data used for search algorithm
        self.currently_loaded_categories = {
            'LIVE': [],
            'Movies': [],
            'Series': []
        }
        self.currently_loaded_streams = {
            'LIVE': [],
            'Movies': [],
            'Series': [],
            'Seasons': [],
            'Episodes': []
        }

        #Credentials
        self.server     = ""
        self.username   = ""
        self.password   = ""

        #Create threadpool
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(1)

        self.external_player_command = self.load_external_player_command()

        self.initIcons()

        self.initTabWidget()

        self.initIPTVinfo()

        self.initCategoryListWidgets()
        self.initEntryListWidgets()
        self.initInfoBoxes()

        self.initSearchBars()

        # self.initHomeTab()
        # self.initFavoritesTab()

        self.initSettingsTab()

        self.initProgressBar()        

        #Load default sorting setting
        self.loadDefaultSortingOrder()

        #Add widgets to tabs
        self.live_tab_layout.addWidget(self.category_search_bar_live, 0, 0)
        self.live_tab_layout.addWidget(self.streaming_search_bar_live, 0, 1)
        self.live_tab_layout.addWidget(self.category_list_live, 1, 0)
        self.live_tab_layout.addWidget(self.streaming_list_live, 1, 1)
        self.live_tab_layout.addWidget(self.live_EPG_info_box, 0, 2, 2, 1)

        self.movies_tab_layout.addWidget(self.category_search_bar_movies, 0, 0)
        self.movies_tab_layout.addWidget(self.streaming_search_bar_movies, 0, 1)
        self.movies_tab_layout.addWidget(self.category_list_movies, 1, 0)
        self.movies_tab_layout.addWidget(self.streaming_list_movies, 1, 1)
        self.movies_tab_layout.addWidget(self.movies_info_box, 0, 2, 2, 1)

        self.series_tab_layout.addWidget(self.category_search_bar_series, 0, 0)
        self.series_tab_layout.addWidget(self.streaming_search_bar_series, 0, 1)
        self.series_tab_layout.addWidget(self.category_list_series, 1, 0)
        self.series_tab_layout.addWidget(self.streaming_list_series, 1, 1)
        self.series_tab_layout.addWidget(self.series_info_box, 0, 2, 2, 1)
        
        self.info_tab_layout.addWidget(self.iptv_info_text)

        #Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        #Add everything to the main_layout
        main_layout.addWidget(self.tab_widget)
        main_layout.addWidget(self.progress_bar)

    def initIcons(self):
        #Set tab icon size to 24x24
        self.tab_icon_size = QSize(24, 24)

        #Create tab icons
        self.home_icon      = QIcon(self.path_to_home_icon)
        self.live_icon      = QIcon(self.path_to_live_icon)
        self.movies_icon    = QIcon(self.path_to_movies_icon)
        self.series_icon    = QIcon(self.path_to_series_icon)
        self.favorites_icon = QIcon(self.path_to_favorites_icon)
        self.info_icon      = QIcon(self.path_to_info_icon)
        self.settings_icon  = QIcon(self.path_to_settings_icon)

        #Create settings buttons icons
        self.account_manager_icon   = QIcon(self.path_to_account_icon)
        self.mediaplayer_icon       = QIcon(self.path_to_mediaplayer_icon)

        #Create misc icons
        self.search_icon    = QIcon(self.path_to_search_icon)
        self.sorting_icon   = QIcon(self.path_to_sorting_icon)
        self.clear_btn_icon = QIcon(self.path_to_clear_btn_icon)
        self.go_back_icon   = QIcon(self.path_to_go_back_icon)

    def initTabWidget(self):
        #Create tab widget
        self.tab_widget = QTabWidget()

        #Create tabs
        home_tab        = QWidget()
        live_tab        = QWidget()
        movies_tab      = QWidget()
        series_tab      = QWidget()
        favorites_tab   = QWidget()
        info_tab        = QWidget()
        settings_tab    = QWidget()

        #Create layouts for tabs
        self.home_tab_layout        = QVBoxLayout(home_tab)
        self.live_tab_layout        = QGridLayout(live_tab)
        self.movies_tab_layout      = QGridLayout(movies_tab)
        self.series_tab_layout      = QGridLayout(series_tab)
        self.favorites_tab_layout   = QGridLayout(favorites_tab)
        self.info_tab_layout        = QVBoxLayout(info_tab)
        self.settings_layout        = QGridLayout(settings_tab)

        #Add created tabs to tab widget with their names
        # self.tab_widget.addTab(home_tab,        self.home_icon,         "Home")
        self.tab_widget.addTab(live_tab,        self.live_icon,         "LIVE")
        self.tab_widget.addTab(movies_tab,      self.movies_icon,       "Movies")
        self.tab_widget.addTab(series_tab,      self.series_icon,       "Series")
        # self.tab_widget.addTab(favorites_tab,   self.favorites_icon,    "Favorites")
        self.tab_widget.addTab(info_tab,        self.info_icon,         "Info")
        self.tab_widget.addTab(settings_tab,    self.settings_icon,     "Settings")

    def initSearchBars(self):
        #Initialize search bars for category lists
        self.category_search_bar_live = QLineEdit()
        self.category_search_bar_live.setPlaceholderText("Search Live TV Categories...")
        self.configSearchBar(self.category_search_bar_live, 'category', 'LIVE', self.category_list_widgets, self.category_search_history_list, self.category_search_history_list_idx)

        self.category_search_bar_movies = QLineEdit()
        self.category_search_bar_movies.setPlaceholderText("Search Movies Categories...")
        self.configSearchBar(self.category_search_bar_movies, 'category', 'Movies', self.category_list_widgets, self.category_search_history_list, self.category_search_history_list_idx)

        self.category_search_bar_series = QLineEdit()
        self.category_search_bar_series.setPlaceholderText("Search Series Categories...")
        self.configSearchBar(self.category_search_bar_series, 'category', 'Series', self.category_list_widgets, self.category_search_history_list, self.category_search_history_list_idx)

        #Initialize search bars for streaming content lists
        self.streaming_search_bar_live = QLineEdit()
        self.streaming_search_bar_live.setPlaceholderText("Search Live TV Channels...")
        self.configSearchBar(self.streaming_search_bar_live, 'streaming', 'LIVE', self.streaming_list_widgets, self.streaming_search_history_list, self.streaming_search_history_list_idx)

        self.streaming_search_bar_movies = QLineEdit()
        self.streaming_search_bar_movies.setPlaceholderText("Search Movies...")
        self.configSearchBar(self.streaming_search_bar_movies, 'streaming', 'Movies', self.streaming_list_widgets, self.streaming_search_history_list, self.streaming_search_history_list_idx)

        self.streaming_search_bar_series = QLineEdit()
        self.streaming_search_bar_series.setPlaceholderText("Search Series...")
        self.configSearchBar(self.streaming_search_bar_series, 'streaming', 'Series', self.streaming_list_widgets, self.streaming_search_history_list, self.streaming_search_history_list_idx)

    def configSearchBar(self, search_bar, list_content_type, stream_type, list_widgets, search_history_list, search_history_list_idx):
        #Create sorting actions
        sort_a_z        = QAction("A-Z", self)
        sort_z_a        = QAction("Z-A", self)
        sort_disabled   = QAction("Sorting disabled", self)

        #Add search icon
        search_bar.addAction(self.search_icon, QLineEdit.LeadingPosition)

        #Create sorting action menu
        sorting_menu = QMenu()
        sorting_menu.setTitle("Set sorting order:")
        sorting_menu.addActions([sort_a_z, sort_z_a, sort_disabled])

        #Create sorting button
        sort_action = QAction(self.sorting_icon, "sort", self)
        sort_action.setMenu(sorting_menu)
        search_bar.addAction(sort_action, QLineEdit.TrailingPosition)

        #Connect functions to sorting actions
        sort_a_z.triggered.connect(lambda e: self.sortList(e, search_bar, list_content_type, stream_type, list_widgets, True, 0))
        sort_z_a.triggered.connect(lambda e: self.sortList(e, search_bar, list_content_type, stream_type, list_widgets, True, 1))
        sort_disabled.triggered.connect(lambda e: self.sortList(e, search_bar, list_content_type, stream_type, list_widgets, False, 0))

        #Create clear search button
        clear_action = QAction(self.clear_btn_icon, "clear", self)
        search_bar.addAction(clear_action, QLineEdit.TrailingPosition)

        #Connect function to clear search action
        clear_action.triggered.connect(lambda e: self.clearSearch(e, search_bar, list_content_type, stream_type, list_widgets, search_history_list_idx))

        #Connect function to process search bar key presses
        search_bar.keyPressEvent = lambda e: self.SearchBarKeyPressed(e, 
            search_bar, list_content_type, stream_type, list_widgets, search_history_list, search_history_list_idx)

    def clearSearch(self, e, search_bar, list_content_type, stream_type, list_widgets, history_list_idx):
        #Clear search bar
        search_bar.clear()

        #Reset list history index to -1
        history_list_idx[0] = -1

        #Search for nothing so list will be reset
        self.search_in_list(list_content_type, stream_type, "")

    def sortList(self, e, search_bar, list_content_type, stream_type, list_widgets, sorting_enabled, sort_order):
        #Get list
        list_widget = list_widgets[stream_type]

        #Enable or disable sorting
        list_widget.setSortingEnabled(sorting_enabled)

        #When sorting is enabled, set sort order, 0: A-Z, 1: Z-A
        if sorting_enabled:
            list_widget.sortItems(sort_order)
        else:
            #When sorting is disabled, reload list manually with current search bar text
            self.search_in_list(list_content_type, stream_type, search_bar.text())

    def initIPTVinfo(self):
        self.iptv_info_text = QTextEdit()
        self.iptv_info_text.setReadOnly(True)

        default_font = QFont()
        default_font.setPointSize(self.default_font_size)

        self.iptv_info_text.setFont(default_font)

    def initCategoryListWidgets(self):
        #Create lists for categories
        self.category_list_live     = QListWidget()
        self.category_list_movies   = QListWidget()
        self.category_list_series   = QListWidget()

        #Enable sorting
        self.category_list_live.setSortingEnabled(True)
        self.category_list_movies.setSortingEnabled(True)
        self.category_list_series.setSortingEnabled(True)

        #Connect functions to category list events
        self.category_list_live.itemClicked.connect(self.category_item_clicked)
        self.category_list_movies.itemClicked.connect(self.category_item_clicked)
        self.category_list_series.itemClicked.connect(self.category_item_clicked)

        #Put category lists in list
        self.category_list_widgets = {
            'LIVE': self.category_list_live,
            'Movies': self.category_list_movies,
            'Series': self.category_list_series,
        }

        #Configure visuals of the lists
        standard_icon_size = QSize(24, 24)
        for list_widget in [self.category_list_live, self.category_list_movies, self.category_list_series]:
            list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            list_widget.setIconSize(standard_icon_size)
            list_widget.setStyleSheet("""
                QListWidget::item {
                    padding-top: 5px;
                    padding-bottom: 5px;
                }
            """)

    def initEntryListWidgets(self):
        #Create lists for channels
        self.streaming_list_live      = QListWidget()
        self.streaming_list_movies    = QListWidget()
        self.streaming_list_series    = QListWidget()

        #Enable sorting
        self.streaming_list_live.setSortingEnabled(True)
        self.streaming_list_movies.setSortingEnabled(True)
        self.streaming_list_series.setSortingEnabled(True)

        #Set that lists load items in batches to prevent screen freezing
        self.streaming_list_live.setLayoutMode(QListView.Batched)
        self.streaming_list_movies.setLayoutMode(QListView.Batched)
        self.streaming_list_series.setLayoutMode(QListView.Batched)

        self.streaming_list_live.setBatchSize(2000)
        self.streaming_list_movies.setBatchSize(2000)
        self.streaming_list_series.setBatchSize(2000)

        #Connect functions to entry list events
        self.streaming_list_live.itemDoubleClicked.connect(self.streaming_item_double_clicked)
        self.streaming_list_movies.itemDoubleClicked.connect(self.streaming_item_double_clicked)
        self.streaming_list_series.itemDoubleClicked.connect(self.streaming_item_double_clicked)

        self.streaming_list_live.itemClicked.connect(self.streaming_item_clicked)
        self.streaming_list_movies.itemClicked.connect(self.streaming_item_clicked)
        self.streaming_list_series.itemClicked.connect(self.streaming_item_clicked)

        #Put entry lists in list
        self.streaming_list_widgets = {
            'LIVE': self.streaming_list_live,
            'Movies': self.streaming_list_movies,
            'Series': self.streaming_list_series,
        }

        #Configure visuals of the lists
        standard_icon_size = QSize(24, 24)
        for list_widget in [self.streaming_list_live, self.streaming_list_movies, self.streaming_list_series]:
            list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            list_widget.setIconSize(standard_icon_size)
            list_widget.setStyleSheet("""
                QListWidget::item {
                    padding-top: 5px;
                    padding-bottom: 5px;
                }
            """)

    def initInfoBoxes(self):
        #Create LIVE TV info box
        self.live_EPG_info_box          = QWidget()
        self.live_EPG_info_box_layout   = QVBoxLayout(self.live_EPG_info_box)

        #Create Live TV Channel name label
        self.EPG_box_label = QLabel("Select channel to view Live TV info")
        self.EPG_box_label.setFont(QFont('Arial', 14))

        #Create entry info window
        self.live_EPG_info = QTreeWidget()
        self.live_EPG_info.setColumnCount(2)
        self.live_EPG_info.setHeaderLabels(["Date", "From", "To", "Name"])

        #Set column widths of EPG info window
        self.live_EPG_info.setColumnWidth(0, 120)
        self.live_EPG_info.setColumnWidth(1, 50)
        self.live_EPG_info.setColumnWidth(2, 50)

        #Add TV channel label and EPG data to info box
        self.live_EPG_info_box_layout.addWidget(self.EPG_box_label)
        self.live_EPG_info_box_layout.addWidget(self.live_EPG_info)

        #Create Movies and Series info box
        self.movies_info_box = MovieInfoBox(self)
        self.series_info_box = SeriesInfoBox(self)

    def initHomeTab(self):
        #Create lists to show previously watched content
        self.live_history_list      = QListWidget()
        self.movie_history_list     = QListWidget()
        self.series_history_list    = QListWidget()

        #Set that items are viewed from left to right
        self.live_history_list.setFlow(QListView.LeftToRight)
        self.movie_history_list.setFlow(QListView.LeftToRight)
        self.series_history_list.setFlow(QListView.LeftToRight)

        #Create labels for lists
        self.live_history_lbl   = QLabel("Previously watched TV")
        self.movie_history_lbl  = QLabel("Previously watched movies")
        self.series_history_lbl = QLabel("Previously watched series")

        #Set fonts
        self.live_history_lbl.setFont(QFont('Arial', 14, QFont.Bold))
        self.movie_history_lbl.setFont(QFont('Arial', 14, QFont.Bold))
        self.series_history_lbl.setFont(QFont('Arial', 14, QFont.Bold))

        #Add widgets to home tab
        self.home_tab_layout.addWidget(self.live_history_lbl)
        self.home_tab_layout.addWidget(self.live_history_list)
        self.home_tab_layout.addWidget(self.movie_history_lbl)
        self.home_tab_layout.addWidget(self.movie_history_list)
        self.home_tab_layout.addWidget(self.series_history_lbl)
        self.home_tab_layout.addWidget(self.series_history_list)

    def initFavoritesTab(self):
        #TODO add favorties tab functionality
        pass

    def loadDefaultSortingOrder(self):
        sorting_order = ""

        config = configparser.ConfigParser()
        config.read(self.user_data_file)

        if 'Sorting order' in config:
            # self.external_player_command = config['ExternalPlayer'].get('Command', '')
            sorting_order = config['Sorting order'].get('Order', '')

        if not sorting_order:
            #Set default order to A-Z
            self.default_sorting_order_box.setCurrentText("A-Z")
            self.setAllSortingOrder("A-Z")
        else:
            self.default_sorting_order_box.setCurrentText(sorting_order)
            self.setAllSortingOrder(sorting_order)

    def setAllSortingOrder(self, sorting_order):
        match sorting_order:
            case "A-Z":
                self.category_list_live.setSortingEnabled(True)
                self.category_list_movies.setSortingEnabled(True)
                self.category_list_series.setSortingEnabled(True)

                self.streaming_list_live.setSortingEnabled(True)
                self.streaming_list_movies.setSortingEnabled(True)
                self.streaming_list_series.setSortingEnabled(True)

                self.category_list_live.sortItems(0)
                self.category_list_movies.sortItems(0)
                self.category_list_series.sortItems(0)

                self.streaming_list_live.sortItems(0)
                self.streaming_list_movies.sortItems(0)
                self.streaming_list_series.sortItems(0)

            case "Z-A":
                self.category_list_live.setSortingEnabled(True)
                self.category_list_movies.setSortingEnabled(True)
                self.category_list_series.setSortingEnabled(True)

                self.streaming_list_live.setSortingEnabled(True)
                self.streaming_list_movies.setSortingEnabled(True)
                self.streaming_list_series.setSortingEnabled(True)

                self.category_list_live.sortItems(1)
                self.category_list_movies.sortItems(1)
                self.category_list_series.sortItems(1)

                self.streaming_list_live.sortItems(1)
                self.streaming_list_movies.sortItems(1)
                self.streaming_list_series.sortItems(1)

            case _:
                self.category_list_live.setSortingEnabled(False)
                self.category_list_movies.setSortingEnabled(False)
                self.category_list_series.setSortingEnabled(False)

                self.streaming_list_live.setSortingEnabled(False)
                self.streaming_list_movies.setSortingEnabled(False)
                self.streaming_list_series.setSortingEnabled(False)

    def setDefaultSortingOrder(self, e, combobox):
        sorting_order = combobox.currentText()

        self.setAllSortingOrder(sorting_order)

        config = configparser.ConfigParser()
        config.read(self.user_data_file)

        config['Sorting order'] = {'Order': sorting_order}

        with open(self.user_data_file, 'w') as config_file:
            config.write(config_file)

    def initSettingsTab(self):
        #Create items in settings tab
        self.settings_layout.setSpacing(20)
        self.settings_layout.setAlignment(Qt.AlignTop)

        self.address_book_button = QPushButton("IPTV accounts")
        self.address_book_button.setIcon(self.account_manager_icon)
        self.address_book_button.setToolTip("Manage IPTV accounts")
        self.address_book_button.clicked.connect(self.open_address_book)

        self.choose_player_button = QPushButton("Choose Media Player")
        self.choose_player_button.setIcon(self.mediaplayer_icon)
        self.choose_player_button.setToolTip("Set the Media Player used for watching content, use e.g. VLC or SMPlayer")
        self.choose_player_button.clicked.connect(self.choose_external_player)

        self.keep_on_top_checkbox = QCheckBox("Keep on top")
        self.keep_on_top_checkbox.setToolTip("Keep the application on top of all windows")
        self.keep_on_top_checkbox.stateChanged.connect(self.toggle_keep_on_top)

        self.default_sorting_order_box = QComboBox()
        self.default_sorting_order_box.addItems(["A-Z", "Z-A", "Sorting disabled"])
        self.default_sorting_order_box.currentTextChanged.connect(lambda e: self.setDefaultSortingOrder(e, self.default_sorting_order_box))

        self.cache_on_startup_checkbox = QCheckBox("Startup with cached data")
        self.cache_on_startup_checkbox.setToolTip("Loads the cached IPTV data on startup to reduce startup time.\nNote that the cached data only changes if you manually reload it once in a while.")
        self.cache_on_startup_checkbox.stateChanged.connect(self.toggle_cache_on_startup)

        self.reload_data_btn = QPushButton("Reload data")
        self.reload_data_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.reload_data_btn.setToolTip("Click this to manually reload the IPTV data.\nNote that this only has effect if \'Startup with cached data\' is checked.")

        #Add widgets to settings tab layout
        self.settings_layout.addWidget(self.address_book_button,            0, 0)
        self.settings_layout.addWidget(self.choose_player_button,           0, 1)
        self.settings_layout.addWidget(self.keep_on_top_checkbox,           1, 0)
        self.settings_layout.addWidget(QLabel("Default sorting order: "),   2, 0)
        self.settings_layout.addWidget(self.default_sorting_order_box,      2, 1)
        # self.settings_layout.addWidget(self.cache_on_startup_checkbox,  2, 0)
        # self.settings_layout.addWidget(self.reload_data_btn,            3, 0)

    def initProgressBar(self):
        #Create progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setTextVisible(True)

        #Animate progress bar
        self.playlist_progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.playlist_progress_animation.setDuration(1000)  # longer duration for smoother animation
        self.playlist_progress_animation.setEasingCurve(QEasingCurve.InOutQuad)

    def load_data_startup(self):
        # Load playlist on startup if enabled
        config = configparser.ConfigParser()
        config.read(self.user_data_file)

        #If startup credentials is in user data file
        if 'Startup credentials' in config:
            #Get selected account used for startup
            selected_startup_account = config['Startup credentials']['startup_credentials']

            #Check if account credentials are in user data file
            if 'Credentials' in config and selected_startup_account in config['Credentials']:
                data = config['Credentials'][selected_startup_account]

                if data.startswith('manual|'):
                    _, server, username, password = data.split('|')

                    self.server     = server
                    self.username   = username
                    self.password   = password

                    self.login()

                elif data.startswith('m3u_plus|'):
                    _, m3u_url = data.split('|', 1)

                    #Get credentials from M3U plus url and check if valid
                    if self.extract_credentials_from_m3u_plus_url(m3u_url):
                        self.login()

    def toggle_keep_on_top(self, state):
        if state == Qt.Checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def toggle_cache_on_startup(self, state):
        if state == Qt.Checked:
            print("checked")
        else:
            print("unchecked")

    def open_m3u_plus_dialog(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'M3u_plus Login', 'Enter m3u_plus URL:')
        if ok and text:
            m3u_plus_url = text.strip()
            self.extract_credentials_from_m3u_plus_url(m3u_plus_url)
            self.login()

    def update_font_size(self, value):
        self.default_font_size = value
        for tab_name, list_widget in self.streaming_list_widgets.items():
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                font = item.font()
                font.setPointSize(value)
                item.setFont(font)

        font = QFont()
        font.setPointSize(value)
        self.iptv_info_text.setFont(font)

    def extract_credentials_from_m3u_plus_url(self, url):
        try:
            pattern = r'(http[s]?://[^/]+)/get\.php\?username=([^&]*)&password=([^&]*)&type=(m3u_plus|m3u|&output=m3u8)'
            match = re.match(pattern, url)
            if match:
                self.server     = match.group(1)
                self.username   = match.group(2)
                self.password   = match.group(3)

                return True
            else:
                self.animate_progress(0, 100, "Invalid m3u_plus or m3u URL")

                dlg = QMessageBox(self)
                dlg.setWindowTitle("Error!")
                dlg.setText("M3U plus URL is invalid!\nPlease enter valid URL")
                dlg.exec()

                return False
        except Exception as e:
            print(f"Error extracting credentials: {e}")
            self.animate_progress(0, 100, "Error extracting credentials")

            return False

    def set_progress_text(self, text):
        self.progress_bar.setFormat(text)
        QtWidgets.qApp.processEvents()
        # QtWidgets.qApp.sendPostedEvents()

    def set_progress_bar(self, val, text):
        self.progress_bar.setFormat(text)
        self.progress_bar.setValue(val)
        QtWidgets.qApp.processEvents()

    def animate_progress(self, start, end, text):
        self.playlist_progress_animation.stop()
        self.playlist_progress_animation.setStartValue(start)
        self.playlist_progress_animation.setEndValue(end)
        self.set_progress_text(text)
        self.playlist_progress_animation.start()
        QtWidgets.qApp.processEvents()

    def login(self):
        # When logging into another server, reset the progress bar
        self.set_progress_bar(0, "Logging in...")

        #Clear lists
        for tab_name, list_widget in self.streaming_list_widgets.items():
            list_widget.clear()

        for tab_name, list_widget in self.category_list_widgets.items():
            list_widget.clear()

        #Check if login credentials are not empty
        if not self.server or not self.username or not self.password:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("Please fill in all fields to login!")
            dlg.exec()

            return

        #Start IPTV data fetch thread
        self.fetch_data_thread()

        self.set_progress_bar(0, "Going to fetch data...")

    def fetch_data_thread(self):
        dataWorker = FetchDataWorker(self.server, self.username, self.password, self)
        dataWorker.signals.finished.connect(self.process_data)
        dataWorker.signals.error.connect(self.on_fetch_data_error)
        dataWorker.signals.progress_bar.connect(self.animate_progress)
        self.threadpool.start(dataWorker)

    def process_data(self, iptv_info, categories_per_stream_type, entries_per_stream_type):
        self.categories_per_stream_type = categories_per_stream_type
        self.entries_per_stream_type    = entries_per_stream_type

        self.set_progress_bar(0, "Processing received data...")

        #Process IPTV info
        user_info   = iptv_info.get("user_info", {})
        server_info = iptv_info.get("server_info", {})

        hostname    = server_info.get("url", "Unknown")
        port        = server_info.get("port", "Unknown")
        if hostname == "Unknown" or port == "Unknown":
            host = "Unknown"
        else:
            host = f"http://{hostname}:{port}"

        username            = user_info.get("username", "Unknown")
        password            = user_info.get("password", "Unknown")
        max_connections     = user_info.get("max_connections", "Unknown")
        active_connections  = user_info.get("active_cons", "Unknown")
        status              = user_info.get("status", "Unknown")
        expire_timestamp    = user_info.get("exp_date", "Unknown")
        expiry = (
            datetime.fromtimestamp(int(expire_timestamp)).strftime("%B %d, %Y")
            if expire_timestamp else "Unknown"
        )

        if user_info.get("is_trial") == "1":
            trial = "Yes"
        else:
            trial = "No"

        created_at_timestamp = user_info.get("created_at", "Unknown")
        created_at = (
            datetime.fromtimestamp(int(created_at_timestamp)).strftime("%B %d, %Y")
            if created_at_timestamp and created_at_timestamp.isdigit() else "Unknown"
        )

        timezone = server_info.get("timezone", "Unknown")

        formatted_data = (
            f"Host: {host}\n"
            f"Username: {username}\n"
            f"Password: {password}\n"
            f"Max Connections: {max_connections}\n"
            f"Active Connections: {active_connections}\n"
            f"Timezone: {timezone}\n"
            f"Trial: {trial}\n"
            f"Status: {status}\n"
            f"Created At: {created_at}\n"
            f"Expiry: {expiry}\n"
        )

        #Set formatted data to iptv info tab
        self.iptv_info_text.setText(formatted_data)
        QtWidgets.qApp.processEvents()

        #Process categories and entries
        for stream_type in self.entries_per_stream_type.keys():
            self.streaming_list_widgets[stream_type].clear()
            self.category_list_widgets[stream_type].clear()
            # self.category_list_widgets[stream_type].addItem(self.all_categories_text)
            self.categories_per_stream_type[stream_type].append({'category_name': self.all_categories_text})

            # self.currently_loaded_streams[stream_type] = self.entries_per_stream_type[stream_type]
            #Fill currently loaded streams with current stream data
            for entry in self.entries_per_stream_type[stream_type]:
                self.currently_loaded_streams[stream_type].append(entry)

            #Fill currently loaded categories with current category data
            for entry in self.categories_per_stream_type[stream_type]:
                self.currently_loaded_categories[stream_type].append(entry)

            #Add categories in category list
            num_of_categories = len(self.categories_per_stream_type[stream_type])
            prev_perc = 0
            for idx, category_item in enumerate(self.categories_per_stream_type[stream_type]):
                item = QListWidgetItem(category_item['category_name'])
                item.setData(Qt.UserRole, category_item)
                # item.setIcon(channel_icon)

                self.category_list_widgets[stream_type].addItem(item)

                perc = (idx * 100) / num_of_categories
                if (perc - prev_perc) > 10:
                    prev_perc = perc
                    self.set_progress_bar(int(perc), f"Loading {stream_type} categories: {idx} of {num_of_categories}")
                    QtWidgets.qApp.processEvents()

            #Add streams in streaming list
            num_of_entries = len(self.entries_per_stream_type[stream_type])
            prev_perc = 0
            for idx, entry in enumerate(self.entries_per_stream_type[stream_type]):
                item = QListWidgetItem(entry['name'])
                item.setData(Qt.UserRole, entry)
                # item.setIcon(channel_icon)

                self.streaming_list_widgets[stream_type].addItem(item)

                perc = (idx * 100) / num_of_entries
                if (perc - prev_perc) > 10:
                    prev_perc = perc
                    self.set_progress_bar(int(perc), f"Loading {stream_type} streams: {idx} of {num_of_entries}")
                    QtWidgets.qApp.processEvents()


        self.set_progress_bar(100, f"Finished loading")
        QtWidgets.qApp.processEvents()

    def on_fetch_data_error(self, error_msg):
        print(f"Error occurred while fetching data: {error_msg}")
        self.set_progress_bar(100, "Failed fetching data")

    def fetch_vod_info(self, vod_id):
        movie_info_fetcher = MovieInfoFetcher(self.server, self.username, self.password, vod_id)
        movie_info_fetcher.signals.finished.connect(self.process_vod_info)
        movie_info_fetcher.signals.error.connect(self.on_fetch_data_error)
        self.threadpool.start(movie_info_fetcher)

    def process_vod_info(self, vod_info, vod_data):
        #Get movie image url
        movie_img_url = vod_info.get('movie_image', 0)

        #Fetch movie image
        self.fetch_image(movie_img_url, 'Movies')

        #If vod data is valid
        if vod_data:
            #Get movie name from vod_info, otherwise try name from vod_data
            movie_name = vod_info.get('name', vod_data.get('name', 'No name Available...'))

            #If movie name is an empty string
            if not movie_name:
                movie_name = vod_data.get('name', 'No name Available...')

                #Check again if movie name is an empty string
                if not movie_name:
                    movie_name = 'No name Available...'
        else:
            #Get movie name from vod info
            movie_name = vod_info.get('name', 'No name Available...')

        #Set movie info box texts
        self.movies_info_box.name.setText(f"{movie_name}")
        self.movies_info_box.release_date.setText(f"Release date: {vod_info.get('releasedate', '??-??-????')}")
        self.movies_info_box.country.setText(f"Country: {vod_info.get('country', '?')}")
        self.movies_info_box.genre.setText(f"Genre: {vod_info.get('genre', '?')}")
        self.movies_info_box.duration.setText(f"Duration: {vod_info.get('duration', '??:??:??')}")
        self.movies_info_box.rating.setText(f"Rating: {vod_info.get('rating', '?')}")
        self.movies_info_box.director.setText(f"Director: {vod_info.get('director', 'director: ?')}")
        self.movies_info_box.cast.setText(f"Cast: {vod_info.get('actors', 'actors: ?')}")
        self.movies_info_box.description.setText(f"Description: {vod_info.get('description', '?')}")
        self.movies_info_box.trailer.setText(f"Trailer: {vod_info.get('youtube_trailer', '?')}")
        self.movies_info_box.tmdb.setText(f"TMBD: {vod_info.get('tmdb_id', '?')}")

        #Update progress bar
        if not vod_info:
            print(f"VOD info was empty: {vod_info}")
            self.set_progress_bar(100, "Failed loading Movie info")
        else:
            self.set_progress_bar(100, "Loaded Movie info")

    def fetch_series_info(self, series_id, is_show_request):
        series_info_fetcher = SeriesInfoFetcher(self.server, self.username, self.password, series_id, is_show_request)
        series_info_fetcher.signals.finished.connect(self.process_series_info)
        series_info_fetcher.signals.error.connect(self.on_fetch_data_error)
        self.threadpool.start(series_info_fetcher)

    def process_series_info(self, series_info_data, is_show_request):
        #If no series info data available
        if not series_info_data:
            self.animate_progress(0, 100, "Failed fetching series info")
            return

        #Check if fetch request came from show_seasons()
        if is_show_request:
            #Clear series list
            self.streaming_list_widgets['Series'].clear()

            #Reset scrollbar position to top
            self.streaming_list_widgets['Series'].scrollToTop()

            #Add go back item
            go_back_item = QListWidgetItem(self.go_back_text)
            go_back_item.setIcon(self.go_back_icon)
            self.streaming_list_widgets['Series'].addItem(go_back_item)

            #Save currently loaded series data for search funcitonality
            self.currently_loaded_streams['Seasons'] = series_info_data['episodes']

            #Go through each season in the series info data.
            #Note that 'episodes' is called, as this is the name given in the data. 
            #When you look at the data you can see these are actually seasons.
            for season in series_info_data['episodes'].keys():
                #Create season item
                item = QListWidgetItem(f"Season {season}")

                #Set season data to item
                item.setData(Qt.UserRole, series_info_data['episodes'][season])
                # item.setIcon(channel_icon)

                #Add season item to series list
                self.streaming_list_widgets['Series'].addItem(item)

            self.animate_progress(0, 100, "Loading finished")

        #Otherwise request came from single click to show only series info
        else:
            #Get series information data
            series_info = series_info_data['info']

            #Get movie image url
            series_img_url = series_info.get('cover', 0)

            #Fetch Series image
            self.fetch_image(series_img_url, 'Series')

            #Get series name
            series_name = series_info.get('name', 'No name Available...')
            if not series_name:
                #If series name is empty set replacement
                series_name = 'No name Available...'

            seasons = ""
            for key in series_info_data['episodes'].keys():
                # print(f"season: {key}")
                seasons += f"{key}, "

            #Get strings from series info
            release_date    = series_info.get('releaseDate', '????-??-??')
            genre           = series_info.get('genre', '?')
            duration        = series_info.get('episode_run_time', '?')
            rating          = series_info.get('rating', '?')
            director        = series_info.get('director', '?')
            cast            = series_info.get('cast', '?')
            plot            = series_info.get('plot', '?')
            trailer         = series_info.get('youtube_trailer', '?')
            tmdb            = series_info.get('tmdb', '?')

            #Set series info box texts
            self.series_info_box.name.setText(f"{series_name}")
            self.series_info_box.release_date.setText(f"Release date: {release_date if release_date else '????-??-??'}")
            self.series_info_box.genre.setText(f"Genre: {genre if genre else '?'}")
            self.series_info_box.num_seasons.setText(f"Seasons: {seasons}")
            self.series_info_box.duration.setText(f"Episode duration: {duration if (duration and duration != '0') else '?'} min")
            self.series_info_box.rating.setText(f"Rating: {rating if (rating and rating != '0') else '?'}")
            self.series_info_box.director.setText(f"Director: {director if director else '?'}")
            self.series_info_box.cast.setText(f"Cast: {cast if cast else '?'}")
            self.series_info_box.description.setText(f"Description: {plot if plot else '?'}")
            self.series_info_box.trailer.setText(f"Trailer: {trailer if trailer else '?'}")
            self.series_info_box.tmdb.setText(f"TMDB: {tmdb if (tmdb and tmdb != '0') else '?'}")

            #Update progress bar
            if not series_info:
                # print(f"Series info was empty: {series_info}")
                self.set_progress_bar(100, "Failed loading Series info")
            else:
                self.set_progress_bar(100, "Loaded Series info")

    def fetch_image(self, img_url, stream_type):
        image_fetcher = ImageFetcher(img_url, stream_type, self)
        image_fetcher.signals.finished.connect(self.process_image_data)
        image_fetcher.signals.error.connect(self.on_fetch_data_error)
        self.threadpool.start(image_fetcher)

    def process_image_data(self, image, stream_type):
        try:
            if stream_type == 'Series':
                #Set series image
                self.series_info_box.cover.setPixmap(image.scaledToWidth(self.series_info_box.maxCoverWidth))
            elif stream_type == 'Movies':
                #Set movie image
                self.movies_info_box.cover.setPixmap(image.scaledToWidth(self.movies_info_box.maxCoverWidth))
            elif stream_type == 'Live':
                pass
        except Exception as e:
            print(f"Failed processing image: {e}")

    def category_item_clicked(self, clicked_item):
        try:
            sender = self.sender()
            stream_type = {
                self.category_list_live: 'LIVE',
                self.category_list_movies: 'Movies',
                self.category_list_series: 'Series'
            }.get(sender)

            if not stream_type:
                return

            selected_item = sender.currentItem()
            if not selected_item:
                return

            #Check if the item is already selected
            if selected_item == self.prev_clicked_category_item[stream_type]:
                return

            #Save to previous clicked
            self.prev_clicked_category_item[stream_type] = selected_item

            selected_item_text = selected_item.text()
            selected_item_data = selected_item.data(Qt.UserRole)

            if selected_item_text != self.all_categories_text:
                category_id = selected_item_data['category_id']

            self.set_progress_bar(0, "Loading items")

            if stream_type == 'Series':
                #Reset navigation level
                self.series_navigation_level = 0

            #Clear items in list
            self.streaming_list_widgets[stream_type].clear()
            self.currently_loaded_streams[stream_type].clear()

            #Reset scrollbar position to top
            self.streaming_list_widgets[stream_type].scrollToTop()

            for entry in self.entries_per_stream_type[stream_type]:
                # print(entry)
                if selected_item_text == self.all_categories_text:
                    item = QListWidgetItem(entry['name'])
                    item.setData(Qt.UserRole, entry)

                    self.currently_loaded_streams[stream_type].append(entry)
                    self.streaming_list_widgets[stream_type].addItem(item)

                elif entry['category_id'] == category_id:
                    item = QListWidgetItem(entry['name'])
                    item.setData(Qt.UserRole, entry)

                    self.currently_loaded_streams[stream_type].append(entry)
                    self.streaming_list_widgets[stream_type].addItem(item)

            self.animate_progress(0, 100, "Loading finished")

        except Exception as e:
            print(f"Failed: {e}")

    def startEPGWorker(self, stream_id):
        #Create EPG thread worker that will fetch EPG data
        epg_worker = EPGWorker(self.server, self.username, self.password, stream_id)

        #Connect functions to signals
        epg_worker.signals.finished.connect(self.ProcessEPGData)
        epg_worker.signals.error.connect(self.onEPGFetchError)

        #Start EPG thread
        self.threadpool.start(epg_worker)

    def onEPGFetchError(self, error_msg):
        print(f"Failed fetching EPG data: {error_msg}")
        self.set_progress_bar(100, "Failed loading EPG data")

    def ProcessEPGData(self, epg_data):
        try:
            #Clear EPG data
            self.live_EPG_info.clear()

            #Check if EPG data is empty
            if not epg_data:
                item = QTreeWidgetItem(["??-??-????", "??:??", "??:??", "No EPG Data Available..."])

                self.live_EPG_info.addTopLevelItem(item)

                self.set_progress_bar(100, "No EPG data")
                return

            #Get current time
            current_timestamp = time.mktime(datetime.now().timetuple())

            items = []

            #Loop through EPG data
            for epg_entry in epg_data:
                #Get EPG data
                start_timestamp = epg_entry['start_time']
                stop_timestamp  = epg_entry['stop_time']
                program_name    = epg_entry['program_name']
                description     = epg_entry['description']
                date            = epg_entry['date']

                #Convert timestamps to string in correct format
                start_time = start_timestamp.strftime("%H:%M")
                stop_time = stop_timestamp.strftime("%H:%M")

                #Convert stop time to unix timebase so it can be used for calculating
                unix_stop_time = time.mktime(stop_timestamp.timetuple())

                #Compute time difference
                time_diff = unix_stop_time - current_timestamp

                if time_diff >= 0:
                    #Create EPG item
                    item    = QTreeWidgetItem([date, start_time, stop_time, program_name])
                    label   = QLabel(description)
                    label.setWordWrap(True)
                    desc    = QTreeWidgetItem()
                    item.addChild(desc)

                    #Add label widget to description. This way it is word wrapped correctly
                    self.live_EPG_info.setItemWidget(desc, 3, label)

                    #Append item to list
                    items.append(item)

            #Add all items to EPG treeview
            self.live_EPG_info.addTopLevelItems(items)

            #Update progress bar
            self.set_progress_bar(100, "Loaded EPG data")

        except Exception as e:
            print(f"Failed processing EPG: {e}")

    def streaming_item_clicked(self, clicked_item):
        try:
            #Clear threadpool
            # self.threadpool.clear()

            #Check if clicked item is valid
            if not clicked_item:
                return

            #Check if clicked item is already selected
            if (clicked_item == self.prev_clicked_streaming_item):
                return

            #Save to previous item
            self.prev_clicked_streaming_item = clicked_item

            #Get clicked item data
            clicked_item_text = clicked_item.text()
            clicked_item_data = clicked_item.data(Qt.UserRole)

            #Get stream type
            try:
                stream_type = clicked_item_data['stream_type']
            except:
                stream_type = ''

            # print(f"single click stream type {stream_type}")

            #Skip when back button or already loaded series info
            if clicked_item.text() == self.go_back_text or (stream_type == 'series' and self.series_navigation_level > 0):
                return

            #Show EPG data if live tv clicked
            if stream_type == 'live':
                self.set_progress_bar(0, "Loading EPG data")

                #Set TV channel name in info window
                self.EPG_box_label.setText(f"{clicked_item_data['name']}")

                #Clear EPG data
                self.live_EPG_info.clear()
                item = QTreeWidgetItem(["...", "...", "...", "Loading EPG Data..."])
                self.live_EPG_info.addTopLevelItem(item)

                self.startEPGWorker(clicked_item_data['stream_id'])

            #Show movie info if movie clicked
            elif stream_type == 'movie':
                self.set_progress_bar(0, "Loading Movie info")

                #Set loading image
                self.movies_info_box.cover.setPixmap(QPixmap(self.path_to_loading_img).scaledToWidth(self.series_info_box.maxCoverWidth))

                #Set movie info box texts
                self.movies_info_box.name.setText(f"{clicked_item_data['name']}")
                self.movies_info_box.release_date.setText(f"Release date: ...")
                self.movies_info_box.country.setText(f"Country: ...")
                self.movies_info_box.genre.setText(f"Genre: ...")
                self.movies_info_box.duration.setText(f"Duration: ...")
                self.movies_info_box.rating.setText(f"Rating: ...")
                self.movies_info_box.director.setText(f"Director: ...")
                self.movies_info_box.cast.setText(f"Cast: ...")
                self.movies_info_box.description.setText(f"Description: ...")
                self.movies_info_box.trailer.setText(f"Trailer: ...")
                self.movies_info_box.tmdb.setText(f"TMBD: ...")

                #Get vod info and vod data
                self.fetch_vod_info(clicked_item_data['stream_id'])

            #Show series info if series clicked
            elif stream_type == 'series':
                self.set_progress_bar(0, "Loading Series info")

                #Set loading image
                self.series_info_box.cover.setPixmap(QPixmap(self.path_to_loading_img).scaledToWidth(self.series_info_box.maxCoverWidth))

                #Set series info box texts
                self.series_info_box.name.setText(f"{clicked_item_data['name']}")
                self.series_info_box.release_date.setText(f"Release date: ...")
                self.series_info_box.genre.setText(f"Genre: ...")
                self.series_info_box.num_seasons.setText(f"Seasons: ...")
                self.series_info_box.duration.setText(f"Episode duration: ... min")
                self.series_info_box.rating.setText(f"Rating: ...")
                self.series_info_box.director.setText(f"Director: ...")
                self.series_info_box.cast.setText(f"Cast: ...")
                self.series_info_box.description.setText(f"Description: ...")
                self.series_info_box.trailer.setText(f"Trailer: ...")
                self.series_info_box.tmdb.setText(f"TMDB: ...")

                #Fetch series info data
                self.fetch_series_info(clicked_item_data['series_id'], False)

        except Exception as e:
            print(f"Failed item single click: {e}")

    def streaming_item_double_clicked(self, clicked_item):
        try:
            #Check if clicked item is valid
            if not clicked_item:
                return

            #Get clicked item data
            clicked_item_text = clicked_item.text()
            clicked_item_data = clicked_item.data(Qt.UserRole)

            try:
                stream_type = clicked_item_data['stream_type']
            except:
                stream_type = ''

            #Prevent loading the same series navigation levels multiple times
            if stream_type == 'series' and self.series_navigation_level < 2 and clicked_item == self.prev_double_clicked_streaming_item:
                return

            #Save to previous double clicked item
            self.prev_double_clicked_streaming_item = clicked_item

            #Have different action depending on the navigation level
            match self.series_navigation_level:
                case 0: #Highest level, either LIVE, VOD or series
                    if clicked_item_text == self.go_back_text:
                        return

                    if stream_type == 'live' or stream_type == 'movie':
                        self.play_item(clicked_item_data['url'])

                    elif stream_type == 'series':
                        self.series_navigation_level = 1
                        self.show_seasons(clicked_item_data)

                case 1: #Series seasons
                    if clicked_item_text == self.go_back_text:
                        self.series_navigation_level = 0
                        self.go_back_to_level(self.series_navigation_level)
                        
                    else:
                        self.series_navigation_level = 2
                        self.show_episodes(clicked_item_data)

                case 2: #Series episodes
                    if clicked_item_text == self.go_back_text:
                        self.series_navigation_level = 1
                        self.go_back_to_level(self.series_navigation_level)
                        
                    else:
                        #Play episode
                        self.play_item(clicked_item_data['url'])

        except Exception as e:
            print(f"failed item double click: {e}")

    def go_back_to_level(self, series_navigation_level):
        self.set_progress_bar(0, "Loading items")

        #Clear series list widget
        self.streaming_list_widgets['Series'].clear()

        #Reset scrollbar position to top
        self.streaming_list_widgets['Series'].scrollToTop()

        if series_navigation_level == 0:    #From seasons back to series list
            for entry in self.currently_loaded_streams['Series']:
                item = QListWidgetItem(entry['name'])
                item.setData(Qt.UserRole, entry)

                self.streaming_list_widgets['Series'].addItem(item)

        elif series_navigation_level == 1:  #From episodes back to seasons list
            #Add go back item
            go_back_item = QListWidgetItem(self.go_back_text)
            go_back_item.setIcon(self.go_back_icon)
            self.streaming_list_widgets['Series'].addItem(go_back_item)

            for season in self.currently_loaded_streams['Seasons'].keys():
                item = QListWidgetItem(f"Season {season}")
                item.setData(Qt.UserRole, self.currently_loaded_streams['Seasons'][season])

                self.streaming_list_widgets['Series'].addItem(item)

        self.animate_progress(0, 100, "Loading finished")

    def show_seasons(self, seasons_data):
        self.set_progress_bar(0, "Loading items")

        #Fetch series info data
        self.fetch_series_info(seasons_data['series_id'], True)

    def show_episodes(self, episodes_data):
        self.set_progress_bar(0, "Loading items")

        #Clear series list
        self.streaming_list_widgets['Series'].clear()

        #Reset scrollbar position to top
        self.streaming_list_widgets['Series'].scrollToTop()

        #Add go back item
        go_back_item = QListWidgetItem(self.go_back_text)
        go_back_item.setIcon(self.go_back_icon)
        self.streaming_list_widgets['Series'].addItem(go_back_item)

        #Clear episodes list so it can be filled again
        self.currently_loaded_streams['Episodes'].clear()

        #Show episodes in list
        for episode in episodes_data:
            #Create episode item
            item = QListWidgetItem(f"{episode['title']}")

            #Make playable url
            container_extension = episode['container_extension']
            episode_id          = episode['id']
            playable_url = f"{self.server}/series/{self.username}/{self.password}/{episode_id}.{container_extension}"

            #Add new 'url' key to episode data
            episode['url'] = playable_url

            #Set data to the episode item
            item.setData(Qt.UserRole, episode)

            #Append episode data to the currently loaded list for search functionality
            self.currently_loaded_streams['Episodes'].append(episode)

            #Add episode item to series list
            self.streaming_list_widgets['Series'].addItem(item)

        self.animate_progress(0, 100, "Loading finished")

    def play_item(self, url):
        if not url:
            self.animate_progress(0, 100, "Stream URL not found")

            #Create warning message box to indicate error
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setWindowTitle("Invalid stream URL")
            error_dialog.setText("Invalid stream URL!\nPlease try again.")

            #Set only OK button
            error_dialog.setStandardButtons(QMessageBox.Ok)

            #Show error dialog
            error_dialog.exec_()
            return

        if self.external_player_command:
            try:
                # print(f"Going to play: {url}")
                self.animate_progress(0, 100, "Loading player for streaming")

                user_agent_argument = f":http-user-agent=Lavf53.32.100"
                # command = [self.external_player_command, stream_url, user_agent_argument]
 
                if is_linux:
                    # Ensure the external player command is executable
                    if not os.access(self.external_player_command, os.X_OK):
                        self.animate_progress(0, 100, "Selected player is not executable")
                        return

                subprocess.Popen([self.external_player_command, url, user_agent_argument])
                # subprocess.Popen([self.external_player_command, url])
            except:
                self.animate_progress(0, 100, "Failed playing stream")
        else:
            #Create warning message box to indicate error
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Warning)
            error_dialog.setWindowTitle("No Media Player")
            error_dialog.setText("No media player configured!\nPlease configure a media player.")

            #Set only OK button
            error_dialog.setStandardButtons(QMessageBox.Ok)

            #Show error dialog
            error_dialog.exec_()

    def choose_external_player(self):
        #Open file dialog box in order to select media player program
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if sys.platform.startswith('win'):
            file_dialog.setNameFilter("Executable files (*.exe *.bat)")
        else:
            file_dialog.setNameFilter("Executable files (*)")

        file_dialog.setWindowTitle("Select External Media Player")

        if file_dialog.exec_():
            file_paths = file_dialog.selectedFiles()

            if len(file_paths) > 0:
                self.external_player_command = file_paths[0]

                self.save_external_player_command()

                self.animate_progress(0, 100, "Selected external media player")

    def SearchBarKeyPressed(self, e, search_bar, list_content_type, stream_type, list_widgets, history_list, history_list_idx):
        search_history_size = len(history_list)
        text = search_bar.text()

        match e.key():
            case Qt.Key_Return:
                list_widgets[stream_type].clear()
                
                history_list_idx[0] = 0

                if text:
                    history_list.insert(0, text)

                    if search_history_size >= self.max_search_history_size:
                        history_list.pop(-1)

                self.search_in_list(list_content_type, stream_type, text)

            case Qt.Key_Up:
                #Check if list is empty
                if not history_list:
                    return

                history_list_idx[0] += 1
                if history_list_idx[0] >= search_history_size:
                    history_list_idx[0] = search_history_size - 1

                search_bar.setText(history_list[history_list_idx[0]])

            case Qt.Key_Down:
                #Check if list is empty
                if not history_list:
                    return

                history_list_idx[0] -= 1
                if history_list_idx[0] < 0:
                    history_list_idx[0] = -1
                    search_bar.clear()
                else:
                    search_bar.setText(history_list[history_list_idx[0]])

            case Qt.Key_Left:
                search_bar.cursorBackward(False, 1)

            case Qt.Key_Right:
                search_bar.cursorForward(False, 1)

            case Qt.Key_Backspace:
                search_bar.backspace()

            case Qt.Key_Delete:
                if search_bar.cursorPosition() < len(text):
                    search_bar.cursorForward(False, 1)
                    search_bar.backspace()

            case Qt.Key_Home:
                if search_bar.cursorPosition() != 0:
                    search_bar.setCursorPosition(0)

            case Qt.Key_End:
                if search_bar.cursorPosition() != len(text):
                    search_bar.setCursorPosition(len(text))

            case _:
                search_bar.insert(e.text())
                # e.accept()

    def search_in_list(self, list_content_type, stream_type, text):
        try:
            self.set_progress_bar(0, f"Loading search results...")

            #If searching in category list
            if list_content_type == 'category':
                self.category_list_widgets[stream_type].clear()

                for entry in self.currently_loaded_categories[stream_type]:
                    if text.lower() in entry.get('category_name', '').lower():
                        item = QListWidgetItem(entry['category_name'])
                        item.setData(Qt.UserRole, entry)

                        self.category_list_widgets[stream_type].addItem(item)

                #Check if no search results found
                num_of_items = self.category_list_widgets[stream_type].count()
                if not num_of_items:
                    self.category_list_widgets[stream_type].addItem("No search results found...")

            #If searching in streaming content list
            elif list_content_type == 'streaming':
                self.streaming_list_widgets[stream_type].clear()

                match self.series_navigation_level:
                    case 0: #LIVE/VOD/Series
                        for entry in self.currently_loaded_streams[stream_type]:
                            if text.lower() in entry['name'].lower():
                                item = QListWidgetItem(entry['name'])
                                item.setData(Qt.UserRole, entry)

                                self.streaming_list_widgets[stream_type].addItem(item)
                    case 1: #Seasons
                        self.streaming_list_widgets[stream_type].addItem(self.go_back_text)

                        for season in self.currently_loaded_streams['Seasons'].keys():
                            if text.lower() in f"season {season}":
                                item = QListWidgetItem(f"Season {season}")
                                item.setData(Qt.UserRole, self.currently_loaded_streams['Seasons'][season])

                                self.streaming_list_widgets[stream_type].addItem(item)
                    case 2: #Episodes
                        self.streaming_list_widgets[stream_type].addItem(self.go_back_text)

                        for episode in self.currently_loaded_streams['Episodes']:
                            if text.lower() in episode['title'].lower():
                                item = QListWidgetItem(episode['title'])
                                item.setData(Qt.UserRole, episode)

                                self.streaming_list_widgets[stream_type].addItem(item)

                #Check if no search results found
                num_of_items = self.streaming_list_widgets[stream_type].count()
                if not (num_of_items - (self.series_navigation_level > 0)):
                    self.streaming_list_widgets[stream_type].addItem("No search results found...")

            self.set_progress_bar(100, f"Loaded search results")
        except Exception as e:
            print(f"search in list failed: {e}")

    def load_external_player_command(self):
        external_player_command = ""

        config = configparser.ConfigParser()
        config.read(self.user_data_file)

        if 'ExternalPlayer' in config:
            # self.external_player_command = config['ExternalPlayer'].get('Command', '')
            external_player_command = config['ExternalPlayer'].get('Command', '')

        return external_player_command

    def save_external_player_command(self):
        config = configparser.ConfigParser()
        config.read(self.user_data_file)

        config['ExternalPlayer'] = {'Command': self.external_player_command}

        with open(self.user_data_file, 'w') as config_file:
            config.write(config_file)

    def open_address_book(self):
        dialog = AccountManager(self)
        dialog.exec_()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    player = IPTVPlayerApp()
    player.show()
    # player.showMaximized()
    QtWidgets.qApp.processEvents()
    player.load_data_startup()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
