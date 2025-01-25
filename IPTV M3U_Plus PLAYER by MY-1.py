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
from PyQt5.QtGui import QIcon, QFont, QImage, QPixmap
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QObject, pyqtSignal, QRunnable, pyqtSlot, QThreadPool
)
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QLabel, QPushButton,
    QListWidget, QWidget, QFileDialog, QCheckBox, QSizePolicy, QHBoxLayout,
    QDialog, QFormLayout, QDialogButtonBox, QTabWidget, QListWidgetItem,
    QSpinBox, QMenu, QAction, QTextEdit, QGridLayout, QMessageBox, QListView
)

import threading

CUSTOM_USER_AGENT = (
    "Connection: Keep-Alive User-Agent: okhttp/5.0.0-alpha.2 "
    "Accept-Encoding: gzip, deflate"
)

def normalize_channel_name(name):
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\b(hd|sd|channel|tv)\b', '', name)
    name = name.strip()
    return name

class FetchDataWorkerSignals(QObject):
    finished        = pyqtSignal(dict, dict, dict)
    error           = pyqtSignal(str)
    progress_bar    = pyqtSignal(int, int, str)

class FetchDataWorker(QRunnable):
    def __init__(self, server, username, password, http_method):
        super().__init__()
        self.server = server
        self.username = username
        self.password = password
        # self.http_method = http_method
        self.signals = FetchDataWorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            categories_per_stream_type = {
                'LIVE': [],
                'Movies': [],
                'Series': []
            }
            entries_per_stream_type = {
                'LIVE': [],
                'Movies': [],
                'Series': []
            }

            headers = {'User-Agent': CUSTOM_USER_AGENT}
            params = {
                'username': self.username,
                'password': self.password,
                'action': ''
            }

            host_url = f"{self.server}/player_api.php"

            print("Going to receive data")

            #Get IPTV info
            self.signals.progress_bar.emit(0, 5, "Fetching IPTV info")
            try:
                iptv_info_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
                # iptv_info_resp.raise_for_status()
                iptv_info_data = iptv_info_resp.json()
            except Exception as e:
                print(f"failed fetching IPTV data: {e}")

            #Load cached data
            print("Loading cached data")
            cached_data = {}

            cache_path = path.join(path.dirname(path.abspath(__file__)), "all_cached_data.json")
            #Check if cache file exists
            if path.isfile(cache_path):
                print("cache file is there")
                with open("all_cached_data.json", 'r') as cache_file:
                    cached_data = json.load(cache_file)

            categories_per_stream_type['LIVE'] = cached_data['LIVE categories']
            categories_per_stream_type['Movies'] = cached_data['Movies categories']
            categories_per_stream_type['Series'] = cached_data['Series categories']
            entries_per_stream_type['LIVE'] = cached_data['LIVE']
            entries_per_stream_type['Movies'] = cached_data['Movies']
            entries_per_stream_type['Series'] = cached_data['Series']

            #Uncomment this
            # #Get all category data
            # print("Fetching categories")
            # self.signals.progress_bar.emit(5, 10, "Fetching LIVE Categories")
            # try:
            #     params['action'] = 'get_live_categories'
            #     live_category_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
            #     # print(live_category_resp.raise_for_status())

            #     categories_per_stream_type['LIVE'] = live_category_resp.json()
            # except Exception as e:
            #     print(f"failed fetching LIVE categories: {e}")

            #     if cached_data.get('LIVE categories', 0):
            #         print("Getting LIVE categories from cache")
            #         categories_per_stream_type['LIVE'] = cached_data['LIVE categories']

            # self.signals.progress_bar.emit(10, 20, "Fetching VOD Categories")
            # try:
            #     params['action'] = 'get_vod_categories'
            #     movies_category_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
            #     # print(movies_category_resp.raise_for_status())

            #     categories_per_stream_type['Movies'] = movies_category_resp.json()
            # except Exception as e:
            #     print(f"failed fetching VOD categories: {e}")

            #     if cached_data.get('Movies categories', 0):
            #         print("Getting Movies categories from cache")
            #         categories_per_stream_type['Movies'] = cached_data['Movies categories']

            # self.signals.progress_bar.emit(20, 30, "Fetching Series Categories")
            # try:
            #     params['action'] = 'get_series_categories'
            #     series_category_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
            #     # print(series_category_resp.raise_for_status())

            #     categories_per_stream_type['Series'] = series_category_resp.json()
            # except Exception as e:
            #     print(f"failed fetching Series categories: {e}")

            #     if cached_data.get('Series categories', 0):
            #         print("Getting Series categories from cache")
            #         categories_per_stream_type['Series'] = cached_data['Series categories']

            # print("Fetching streaming data")
            # #Get all streaming data
            # self.signals.progress_bar.emit(30, 40, "Fetching LIVE Streaming data")
            # try:
            #     params['action'] = 'get_live_streams'
            #     live_streams_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
            #     # print(live_streams_resp.raise_for_status())

            #     entries_per_stream_type['LIVE'] = live_streams_resp.json()
            # except Exception as e:
            #     print(f"failed fetching LIVE streams: {e}")

            #     if cached_data.get('LIVE', 0):
            #         print("Getting LIVE streams from cache")
            #         entries_per_stream_type['LIVE'] = cached_data['LIVE']

            # self.signals.progress_bar.emit(40, 60, "Fetching VOD Streaming data")
            # try:
            #     params['action'] = 'get_vod_streams'
            #     movies_streams_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
            #     # print(movies_streams_resp.raise_for_status())

            #     entries_per_stream_type['Movies'] = movies_streams_resp.json()
            # except Exception as e:
            #     print(f"failed fetching VOD streams: {e}")

            #     if cached_data.get('Movies', 0):
            #         print("Getting Movies streams from cache")
            #         entries_per_stream_type['Movies'] = cached_data['Movies']

            # self.signals.progress_bar.emit(60, 80, "Fetching Series Streaming data")
            # try:
            #     params['action'] = 'get_series'
            #     series_streams_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
            #     # print(series_streams_resp.raise_for_status())

            #     entries_per_stream_type['Series'] = series_streams_resp.json()
            # except Exception as e:
            #     print(f"failed fetching Series streams: {e}")

            #     if cached_data.get('Series', 0):
            #         print("Getting Series streams from cache")
            #         entries_per_stream_type['Series'] = cached_data['Series']

            # all_cached_data = json.dumps({
            #         'LIVE categories': categories_per_stream_type['LIVE'],
            #         'Movies categories': categories_per_stream_type['Movies'],
            #         'Series categories': categories_per_stream_type['Series'],
            #         'LIVE': entries_per_stream_type['LIVE'],
            #         'Movies': entries_per_stream_type['Movies'],
            #         'Series': entries_per_stream_type['Series']
            #     }, 
            #     indent=4)

            # with open("all_cached_data.json", 'w') as cache_file:
            #     cache_file.write(all_cached_data)

            #TODO Fetch EPG data

            # self.set_progress_bar(100, "Finished loading data")
            self.signals.progress_bar.emit(80, 100, "Finished Fetching data")

            print("setting url in streaming data")
            #Make streaming URL in each entry except for the series
            for tab_name in entries_per_stream_type.keys():
                for idx, entry in enumerate(entries_per_stream_type[tab_name]):
                    stream_type         = entry.get('stream_type', 'series')
                    stream_id           = entry.get("stream_id")
                    container_extension = entry.get("container_extension", "m3u8")
                    if stream_id:
                        entries_per_stream_type[tab_name][idx]["url"] = f"{self.server}/{stream_type}/{self.username}/{self.password}/{stream_id}.{container_extension}"
                    else:
                        entries_per_stream_type[tab_name][idx]["url"] = None

                    if stream_type == 'series':
                        entries_per_stream_type[tab_name][idx]["stream_type"] = stream_type

            # for entry in entries_per_stream_type['Movies']:
            #     if (entry['name'].find("Sonic") >= 0):
            #         print(f"Movie name: {entry['name']}")

            #         cat_id = entry['category_id']
            #         for category in categories_per_stream_type['Movies']:
            #             if category['category_id'] == cat_id:
            #                 print(f"Category name: {category['category_name']}")

            self.signals.finished.emit(iptv_info_data, categories_per_stream_type, entries_per_stream_type)

            print("finished")

        except Exception as e:
            print(f"Exception! {e}")
            self.signals.error.emit(str(e))

class SearchWorkerSignals(QObject):
    list_widget = pyqtSignal(list, str)
    error = pyqtSignal(str)

class SearchWorker(QRunnable):
    def __init__(self, stream_type, currently_loaded_entries, list_widgets, text):
        super().__init__()
        self.stream_type = stream_type
        self.currently_loaded_entries = currently_loaded_entries[0]
        self.list_widgets = list_widgets[0]
        self.text = text

        self.signals = SearchWorkerSignals()

        # self.setAutoDelete(True)

    @pyqtSlot()
    def run(self):
        try:
            self.list_widgets[self.stream_type].clear()
            print("starting searching through entries")

            for entry in self.currently_loaded_entries[self.stream_type]:
                if self.text.lower() in entry['name'].lower():
                    item = QListWidgetItem(entry['name'])
                    item.setData(Qt.UserRole, entry)

                    self.list_widgets[self.stream_type].addItem(item)

                    print(entry['name'])

            self.signals.list_widget.emit([self.list_widgets[self.stream_type]], self.stream_type)
        except Exception as e:
            print(f"failed search worker: {e}")

class EPGWorkerSignals(QObject):
    finished = pyqtSignal(dict, dict)
    error = pyqtSignal(str)

class EPGWorker(QRunnable):
    def __init__(self, server, username, password, http_method):
        super().__init__()
        self.server = server
        self.username = username
        self.password = password
        self.http_method = http_method
        self.signals = EPGWorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            cache_file = 'epg_cache1.xml'
            cache_valid = False
            if os.path.exists(cache_file):
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < 3600:  
                    cache_valid = True

            if cache_valid:
                with open(cache_file, 'rb') as f:
                    epg_xml_data = f.read()
            else:
                epg_url = f"{self.server}/xmltv.php?username={self.username}&password={self.password}"
                headers = {'User-Agent': CUSTOM_USER_AGENT}
                if self.http_method == 'POST':
                    response = requests.post(epg_url, headers=headers, timeout=10)
                else:
                    print("requesting EPG")
                    response = requests.get(epg_url, headers=headers, timeout=10)
                response.raise_for_status()
                epg_xml_data = response.content
                with open(cache_file, 'wb') as f:
                    f.write(epg_xml_data)

            print("going to parse epg_data")
            epg_data, channel_id_to_names = self.parse_epg_data(epg_xml_data)
            print("Finished parsing epg data")
            self.signals.finished.emit(epg_data, channel_id_to_names)
        except Exception as e:
            self.signals.error.emit(str(e))

    def parse_epg_data(self, epg_xml_data):
        epg_dict = {}
        channel_id_to_names = {}
        try:
            epg_tree = ET.fromstring(epg_xml_data)
            for channel in epg_tree.findall('channel'):
                channel_id = channel.get('id')
                if channel_id:
                    channel_id = channel_id.strip().lower()
                    display_names = []
                    for display_name_elem in channel.findall('display-name'):
                        if display_name_elem.text:
                            display_name = display_name_elem.text.strip()
                            normalized_name = normalize_channel_name(display_name)
                            display_names.append(normalized_name)
                    channel_id_to_names[channel_id] = display_names

            for programme in epg_tree.findall('programme'):
                channel_id = programme.get('channel')
                if channel_id:
                    channel_id = channel_id.strip().lower()
                start_time = programme.get('start')
                stop_time = programme.get('stop')
                title_elem = programme.find('title')
                description_elem = programme.find('desc')

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''
                description = description_elem.text.strip() if description_elem is not None and description_elem.text else ''

                epg_entry = {
                    'start_time': start_time,
                    'stop_time': stop_time,
                    'title': title,
                    'description': description
                }

                if channel_id not in epg_dict:
                    epg_dict[channel_id] = []
                epg_dict[channel_id].append(epg_entry)

            return epg_dict, channel_id_to_names

        except Exception as e:
            print(f"Error parsing EPG data: {e}")
            return {}, {}

class AddressBookDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Address Book")
        self.setMinimumSize(400, 300)
        self.parent = parent

        layout = QtWidgets.QVBoxLayout(self)

        startup_credential_layout = QHBoxLayout()
        self.startup_credential_label = QLabel("Startup address:")
        self.startup_credential_options = QtWidgets.QComboBox()
        self.startup_credential_options.currentTextChanged.connect(self.set_startup_credentials)
        startup_credential_layout.addWidget(self.startup_credential_label)
        startup_credential_layout.addWidget(self.startup_credential_options)
        layout.addLayout(startup_credential_layout)

        self.credentials_list = QtWidgets.QListWidget()
        layout.addWidget(self.credentials_list)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add")
        self.add_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogNewFolder))
        self.select_button = QPushButton("Select")
        self.select_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton))
        self.delete_button = QPushButton("Delete")
        self.delete_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        self.load_saved_credentials()

        self.add_button.clicked.connect(self.add_credentials)
        self.select_button.clicked.connect(self.select_credentials)
        self.delete_button.clicked.connect(self.delete_credentials)
        self.credentials_list.itemDoubleClicked.connect(self.double_click_credentials)

    def set_startup_credentials(self):
        selected_item = self.startup_credential_options.currentText()

        config = configparser.ConfigParser()
        config.read('credentials.ini')

        if 'Startup credentials' not in config:
            config['Startup credentials'] = {}

        config['Startup credentials']['startup_credentials'] = f"{selected_item}"

        with open('credentials.ini', 'w') as config_file:
            config.write(config_file)

    def load_saved_credentials(self):
        self.startup_credential_options.currentTextChanged.disconnect(self.set_startup_credentials)

        self.credentials_list.clear()
        self.startup_credential_options.clear()
        self.startup_credential_options.addItem("None")

        config = configparser.ConfigParser()
        config.read('credentials.ini')

        if 'Credentials' in config:
            for key in config['Credentials']:
                self.credentials_list.addItem(key)
                self.startup_credential_options.addItem(key)

        if 'Startup credentials' in config:
            selected_startup_credentials = config['Startup credentials']['startup_credentials']
            idx = self.startup_credential_options.findText(f"{selected_startup_credentials}")
            self.startup_credential_options.setCurrentIndex(idx)

        self.startup_credential_options.currentTextChanged.connect(self.set_startup_credentials)

    def add_credentials(self):
        dialog = AddCredentialsDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            method, name, *credentials = dialog.get_credentials()
            if name:
                config = configparser.ConfigParser()
                config.read('credentials.ini')
                if 'Credentials' not in config:
                    config['Credentials'] = {}
                if method == 'manual':
                    server, username, password = credentials
                    config['Credentials'][name] = f"manual|{server}|{username}|{password}"
                elif method == 'm3u_plus':
                    m3u_url, = credentials
                    config['Credentials'][name] = f"m3u_plus|{m3u_url}"
                with open('credentials.ini', 'w') as config_file:
                    config.write(config_file)
                self.load_saved_credentials()

    def select_credentials(self):
        selected_item = self.credentials_list.currentItem()
        if selected_item:
            name = selected_item.text()
            config = configparser.ConfigParser()
            config.read('credentials.ini')
            if 'Credentials' in config and name in config['Credentials']:
                data = config['Credentials'][name]
                if data.startswith('manual|'):
                    _, server, username, password = data.split('|')
                    self.parent.server_entry.setText(server)
                    self.parent.username_entry.setText(username)
                    self.parent.password_entry.setText(password)
                    self.parent.login()
                elif data.startswith('m3u_plus|'):
                    _, m3u_url = data.split('|', 1)
                    self.parent.extract_credentials_from_m3u_plus_url(m3u_url)
                    self.parent.login()
                self.accept()

    def double_click_credentials(self, item):
        self.select_credentials()
        self.accept()

    def delete_credentials(self):
        selected_item = self.credentials_list.currentItem()
        if selected_item:
            name = selected_item.text()
            config = configparser.ConfigParser()
            config.read('credentials.ini')
            if 'Credentials' in config and name in config['Credentials']:
                del config['Credentials'][name]
                with open('credentials.ini', 'w') as config_file:
                    config.write(config_file)
                self.load_saved_credentials()

class AddCredentialsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Credentials")
        layout = QtWidgets.QVBoxLayout(self)

        self.method_selector = QtWidgets.QComboBox()
        self.method_selector.addItems(["Manual Entry", "m3u_plus URL Entry"])
        layout.addWidget(QtWidgets.QLabel("Select Method:"))
        layout.addWidget(self.method_selector)

        self.stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.stack)

        self.manual_form = QtWidgets.QWidget()
        manual_layout = QFormLayout(self.manual_form)
        self.name_entry_manual = QLineEdit()
        self.server_entry = QLineEdit()
        self.username_entry = QLineEdit()
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        manual_layout.addRow("Name:", self.name_entry_manual)
        manual_layout.addRow("Server URL:", self.server_entry)
        manual_layout.addRow("Username:", self.username_entry)
        manual_layout.addRow("Password:", self.password_entry)

        self.m3u_form = QtWidgets.QWidget()
        m3u_layout = QFormLayout(self.m3u_form)
        self.name_entry_m3u = QLineEdit()
        self.m3u_url_entry = QLineEdit()
        m3u_layout.addRow("Name:", self.name_entry_m3u)
        m3u_layout.addRow("m3u_plus URL:", self.m3u_url_entry)

        self.stack.addWidget(self.manual_form)
        self.stack.addWidget(self.m3u_form)

        self.method_selector.currentIndexChanged.connect(self.stack.setCurrentIndex)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

    def validate_and_accept(self):
        method = self.method_selector.currentText()
        if method == "Manual Entry":
            name = self.name_entry_manual.text().strip()
            server = self.server_entry.text().strip()
            username = self.username_entry.text().strip()
            password = self.password_entry.text().strip()
            if not name or not server or not username or not password:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Please fill all fields for Manual Entry.")
                return
            self.accept()
        else:
            name = self.name_entry_m3u.text().strip()
            m3u_url = self.m3u_url_entry.text().strip()
            if not name or not m3u_url:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Please fill all fields for m3u_plus URL Entry.")
                return
            self.accept()

    def get_credentials(self):
        method = self.method_selector.currentText()
        if method == "Manual Entry":
            name = self.name_entry_manual.text().strip()
            server = self.server_entry.text().strip()
            username = self.username_entry.text().strip()
            password = self.password_entry.text().strip()
            return ('manual', name, server, username, password)
        else:
            name = self.name_entry_m3u.text().strip()
            m3u_url = self.m3u_url_entry.text().strip()
            return ('m3u_plus', name, m3u_url)

class IPTVPlayerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xtream IPTV Player by MY-1 V3.5")
        self.resize(1300, 900)

        self.default_font_size      = 10
        self.go_back_text           = " Go back"
        self.all_categories_text    = " All"

        #navigation level indicates in what list level we are
        #LIVE and VOD have no navigation levels.
        #Series has 0: Series, 1: Seasons, 2: Episodes
        self.series_navigation_level = 0
        self.series_info_data = {}

        self.search_history_list = []
        self.search_history_list_idx = 0
        self.max_search_history_size = 30

        self.categories_per_stream_type = {}
        self.entries_per_stream_type = {
            'LIVE': [],
            'Movies': [],
            'Series': []
        }

        self.currently_loaded_entries = {
            'LIVE': [],
            'Movies': [],
            'Series': [],
            'Seasons': [],
            'Episodes': []
        }

        self.server                 = ""
        self.username               = ""
        self.password               = ""
        self.login_type             = None

        self.epg_data               = {}  
        self.channel_id_to_names    = {}  
        self.epg_last_updated       = None  
        self.epg_id_mapping         = {}
        self.epg_name_map           = {}

        #Create threadpool
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(10)

        self.external_player_command = self.load_external_player_command()

        self.initIcons()

        self.initTabWidget()

        self.initSearchBars()

        self.initIPTVinfo()

        self.initEntryListWidgets()

        self.initSettingsTab()

        self.initProgressBar()        

        #Add widgets to tabs
        self.live_tab_layout.addWidget(self.search_bar_live, 0, 0, 1, 2)
        self.live_tab_layout.addWidget(self.category_list_live, 1, 0)
        self.live_tab_layout.addWidget(self.channel_list_live, 1, 1)

        self.movies_tab_layout.addWidget(self.search_bar_movies, 0, 0, 1, 2)
        self.movies_tab_layout.addWidget(self.category_list_movies, 1, 0)
        self.movies_tab_layout.addWidget(self.channel_list_movies, 1, 1)

        self.series_tab_layout.addWidget(self.search_bar_series, 0, 0, 1, 2)
        self.series_tab_layout.addWidget(self.category_list_series, 1, 0)
        self.series_tab_layout.addWidget(self.channel_list_series, 1, 1)
        
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
        self.home_icon      = self.style().standardIcon(QtWidgets.QStyle.SP_DesktopIcon)
        self.live_icon      = self.style().standardIcon(QtWidgets.QStyle.SP_MediaVolume)
        self.movies_icon    = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        self.series_icon    = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        self.favorites_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton)
        self.info_icon      = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxInformation)
        self.settings_icon  = self.style().standardIcon(QtWidgets.QStyle.SP_DriveCDIcon)

        #Create list entry icons
        self.live_channel_icon      = self.style().standardIcon(QtWidgets.QStyle.SP_MediaVolume)
        self.movies_channel_icon    = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        self.series_channel_icon    = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)

        #Create misc icons
        self.go_back_icon           = self.style().standardIcon(QtWidgets.QStyle.SP_ArrowBack)

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
        self.home_tab_layout        = QGridLayout(home_tab)
        self.live_tab_layout        = QGridLayout(live_tab)
        self.movies_tab_layout      = QGridLayout(movies_tab)
        self.series_tab_layout      = QGridLayout(series_tab)
        self.favorites_tab_layout   = QGridLayout(favorites_tab)
        self.info_tab_layout        = QVBoxLayout(info_tab)
        self.settings_layout        = QVBoxLayout(settings_tab)

        #Add created tabs to tab widget with their names
        self.tab_widget.addTab(home_tab,        self.home_icon,         "Home")
        self.tab_widget.addTab(live_tab,        self.live_icon,         "LIVE")
        self.tab_widget.addTab(movies_tab,      self.movies_icon,       "Movies")
        self.tab_widget.addTab(series_tab,      self.series_icon,       "Series")
        self.tab_widget.addTab(favorites_tab,   self.favorites_icon,    "Favorites")
        self.tab_widget.addTab(info_tab,        self.info_icon,         "Info")
        self.tab_widget.addTab(settings_tab,    self.settings_icon,     "Settings")

    def initSearchBars(self):
        self.search_bar_live = QLineEdit()
        self.search_bar_live.setPlaceholderText("Search Live Channels...")
        self.search_bar_live.setClearButtonEnabled(True)
        self.add_search_icon(self.search_bar_live)
        self.search_bar_live.keyPressEvent = lambda e: self.KeyPressed(e, self.search_bar_live, 'LIVE')

        self.search_bar_movies = QLineEdit()
        self.search_bar_movies.setPlaceholderText("Search Movies...")
        self.search_bar_movies.setClearButtonEnabled(True)
        self.add_search_icon(self.search_bar_movies)
        # self.search_bar_movies.textChanged.connect(lambda text: self.search_in_list('Movies', text))
        self.search_bar_movies.keyPressEvent = lambda e: self.KeyPressed(e, self.search_bar_movies, 'Movies')

        self.search_bar_series = QLineEdit()
        self.search_bar_series.setPlaceholderText("Search Series...")
        self.search_bar_series.setClearButtonEnabled(True)
        self.add_search_icon(self.search_bar_series)
        # self.search_bar_series.textChanged.connect(lambda text: self.search_in_list('Series', text))
        self.search_bar_series.keyPressEvent = lambda e: self.KeyPressed(e, self.search_bar_series, 'Series')

    def initIPTVinfo(self):
        self.iptv_info_text = QTextEdit()
        self.iptv_info_text.setReadOnly(True)

        default_font = QFont()
        default_font.setPointSize(self.default_font_size)

        self.iptv_info_text.setFont(default_font)

    def initEntryListWidgets(self):
        #Create lists for channels
        self.channel_list_live      = QListWidget()
        self.channel_list_movies    = QListWidget()
        self.channel_list_series    = QListWidget()

        #Enable sorting
        self.channel_list_live.setSortingEnabled(True)
        self.channel_list_movies.setSortingEnabled(True)
        self.channel_list_series.setSortingEnabled(True)

        #Set that lists load items in batches to prevent screen freezing
        self.channel_list_live.setLayoutMode(QListView.Batched)
        self.channel_list_movies.setLayoutMode(QListView.Batched)
        self.channel_list_series.setLayoutMode(QListView.Batched)

        self.channel_list_live.setBatchSize(2000)
        self.channel_list_movies.setBatchSize(2000)
        self.channel_list_series.setBatchSize(2000)

        #Put entry lists in list
        self.list_widgets = {
            'LIVE': self.channel_list_live,
            'Movies': self.channel_list_movies,
            'Series': self.channel_list_series,
        }

        #Create lists for categories
        self.category_list_live     = QListWidget()
        self.category_list_movies   = QListWidget()
        self.category_list_series   = QListWidget()

        #Enable sorting
        self.category_list_live.setSortingEnabled(True)
        self.category_list_movies.setSortingEnabled(True)
        self.category_list_series.setSortingEnabled(True)

        #Put category lists in list
        self.category_list_widgets = {
            'LIVE': self.category_list_live,
            'Movies': self.category_list_movies,
            'Series': self.category_list_series,
        }

        #Configure visuals of the lists
        standard_icon_size = QSize(24, 24)
        for list_widget in [self.channel_list_live, self.channel_list_movies, self.channel_list_series, self.category_list_live, self.category_list_movies, self.category_list_series]:
            list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            list_widget.setIconSize(standard_icon_size)
            list_widget.setStyleSheet("""
                QListWidget::item {
                    padding-top: 5px;
                    padding-bottom: 5px;
                }
            """)

        #Connect functions to entry and category list events
        self.channel_list_live.itemDoubleClicked.connect(self.streaming_item_double_clicked)
        self.channel_list_movies.itemDoubleClicked.connect(self.streaming_item_double_clicked)
        self.channel_list_series.itemDoubleClicked.connect(self.streaming_item_double_clicked)

        self.category_list_live.itemClicked.connect(self.category_item_clicked)
        self.category_list_movies.itemClicked.connect(self.category_item_clicked)
        self.category_list_series.itemClicked.connect(self.category_item_clicked)

    def initSettingsTab(self):
        #Create items in settings tab
        self.settings_layout.setSpacing(20)
        self.settings_layout.setAlignment(Qt.AlignTop)

        row1_layout = QHBoxLayout()
        # row1_layout.setSpacing(15)

        self.server_label = QLabel("Server URL:")
        self.server_label.setFixedWidth(100)
        self.server_entry = QLineEdit()
        self.server_entry.setPlaceholderText("Enter Server URL...")
        self.server_entry.setClearButtonEnabled(True)

        self.username_label = QLabel("Username:")
        self.username_label.setFixedWidth(100)
        self.username_entry = QLineEdit()
        self.username_entry.setPlaceholderText("Enter Username...")
        self.username_entry.setClearButtonEnabled(True)

        self.password_label = QLabel("Password:")
        self.password_label.setFixedWidth(100)
        self.password_entry = QLineEdit()
        self.password_entry.setPlaceholderText("Enter Password...")
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_entry.setClearButtonEnabled(True)

        row1_layout.addWidget(self.server_label)
        row1_layout.addWidget(self.server_entry)
        row1_layout.addWidget(self.username_label)
        row1_layout.addWidget(self.username_entry)
        row1_layout.addWidget(self.password_label)
        row1_layout.addWidget(self.password_entry)

        buttons_layout = QHBoxLayout()
        # buttons_layout.setSpacing(15)

        self.login_button = QPushButton("Login")
        self.login_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogApplyButton))
        self.login_button.clicked.connect(self.login)

        self.m3u_plus_button = QPushButton("M3u_plus")
        search_icon = QIcon.fromTheme("edit-find")
        if search_icon.isNull():
            search_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
        self.m3u_plus_button.setIcon(search_icon)
        self.m3u_plus_button.clicked.connect(self.open_m3u_plus_dialog)

        self.address_book_button = QPushButton("Address Book")
        self.address_book_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
        self.address_book_button.setToolTip("Manage Saved Credentials")
        self.address_book_button.clicked.connect(self.open_address_book)

        self.choose_player_button = QPushButton("Choose Media Player")
        self.choose_player_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.choose_player_button.clicked.connect(self.choose_external_player)

        buttons_layout.addWidget(self.login_button)
        buttons_layout.addWidget(self.m3u_plus_button)
        buttons_layout.addWidget(self.address_book_button)
        buttons_layout.addWidget(self.choose_player_button)

        checkbox_layout = QVBoxLayout()
        # checkbox_layout.setAlignment(Qt.AlignRight)
        # checkbox_layout.setSpacing(15)

        self.http_method_checkbox = QCheckBox("Use POST Method")
        self.http_method_checkbox.setToolTip("Check to use POST instead of GET for server requests")

        self.keep_on_top_checkbox = QCheckBox("Keep on top")
        self.keep_on_top_checkbox.setToolTip("Keep the application on top of all windows")
        self.keep_on_top_checkbox.stateChanged.connect(self.toggle_keep_on_top)

        self.epg_checkbox = QCheckBox("Download EPG")
        self.epg_checkbox.setToolTip("Check to download EPG data for channels")
        self.epg_checkbox.stateChanged.connect(self.on_epg_checkbox_toggled)

        self.font_size_label = QLabel("Font Size:")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        self.font_size_spinbox.setValue(10)
        self.font_size_spinbox.setToolTip("Set the font size for playlist items")
        self.font_size_spinbox.valueChanged.connect(self.update_font_size)
        self.font_size_spinbox.setFixedWidth(60)

        checkbox_layout.addWidget(self.http_method_checkbox)
        checkbox_layout.addWidget(self.keep_on_top_checkbox)
        checkbox_layout.addWidget(self.epg_checkbox)

        fontbox_layout = QHBoxLayout()
        fontbox_layout.setAlignment(Qt.AlignLeft)
        fontbox_layout.addWidget(self.font_size_label)
        fontbox_layout.addWidget(self.font_size_spinbox)
        checkbox_layout.addLayout(fontbox_layout)

        self.settings_layout.addLayout(row1_layout)
        self.settings_layout.addLayout(buttons_layout)
        self.settings_layout.addLayout(checkbox_layout)

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
        config.read('credentials.ini')

        if 'Startup credentials' in config:
            selected_startup_credentials = config['Startup credentials']['startup_credentials']

            if 'Credentials' in config and selected_startup_credentials in config['Credentials']:
                data = config['Credentials'][selected_startup_credentials]

                if data.startswith('manual|'):
                    _, server, username, password = data.split('|')
                    self.server_entry.setText(server)
                    self.username_entry.setText(username)
                    self.password_entry.setText(password)
                    self.login()

                elif data.startswith('m3u_plus|'):
                    _, m3u_url = data.split('|', 1)
                    self.extract_credentials_from_m3u_plus_url(m3u_url)
                    self.login()

    def add_search_icon(self, search_bar):
        search_icon = QIcon.fromTheme("edit-find")
        if search_icon.isNull():
            search_icon = self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogContentsView)
        search_bar.addAction(search_icon, QLineEdit.LeadingPosition)

    def toggle_keep_on_top(self, state):
        if state == Qt.Checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def get_http_method(self):
        return 'POST' if self.http_method_checkbox.isChecked() else 'GET'

    def make_request(self, method, url, params=None, timeout=10):
        headers = {'User-Agent': CUSTOM_USER_AGENT}
        if method == 'POST':
            return requests.post(url, data=params, headers=headers, timeout=timeout)
        else:
            return requests.get(url, params=params, headers=headers, timeout=timeout)

    def open_m3u_plus_dialog(self):
        text, ok = QtWidgets.QInputDialog.getText(self, 'M3u_plus Login', 'Enter m3u_plus URL:')
        if ok and text:
            m3u_plus_url = text.strip()
            self.extract_credentials_from_m3u_plus_url(m3u_plus_url)
            self.login()

    def update_font_size(self, value):
        self.default_font_size = value
        for tab_name, list_widget in self.list_widgets.items():
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
                self.server = match.group(1)
                self.username = match.group(2)
                self.password = match.group(3)
                self.server_entry.setText(self.server)
                self.username_entry.setText(self.username)
                self.password_entry.setText(self.password)
            else:
                self.animate_progress(0, 100, "Invalid m3u_plus or m3u URL")
        except Exception as e:
            print(f"Error extracting credentials: {e}")
            self.animate_progress(0, 100, "Error extracting credentials")

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

    def reset_progress_bar(self):
        self.playlist_progress_animation.stop()
        self.progress_bar.setValue(0)
        self.set_progress_text("")

    def login(self):
        # When logging into another server, reset the progress bar
        self.reset_progress_bar()
        self.epg_data = {}
        self.channel_id_to_names = {}
        self.epg_last_updated = None
        for tab_name, list_widget in self.list_widgets.items():
            list_widget.clear()

        for tab_name, list_widget in self.category_list_widgets.items():
            list_widget.clear()

        cache_file = 'epg_cache1.xml'
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception as e:
                print(f"Error deleting EPG cache: {e}")
                # self.animate_progress(0, 100, "Error deleting EPG cache")
                self.set_progress_bar(100, "Error deleting EPG cache")
                return

        self.server = self.server_entry.text().strip()
        self.username = self.username_entry.text().strip()
        self.password = self.password_entry.text().strip()

        if not self.server or not self.username or not self.password:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("Please fill in all fields to login!")
            btn = dlg.exec()

            if btn == QMessageBox.Ok:
                print("OK!")

            return

        # if not server or not username or not password:
        #     # self.animate_progress(0, 100, "Please fill all fields")
        #     self.set_progress_bar(100, "Please fill all fields")
        #     return

        # # Start loading playlist from 0 to 100
        # # self.reset_progress_bar()
        # # self.animate_progress(0, 30, "Loading playlist...")
        # self.set_progress_bar(50, "Loading playlist...")
        # self.fetch_categories_only(server, username, password)

        # #Remove this
        # self.fetch_all_data(self.server, self.username, self.password)
        self.fetch_data_thread(self.server, self.username, self.password)

    def fetch_data_thread(self, server, username, password):
        http_method = self.get_http_method()
        dataWorker = FetchDataWorker(self.server, self.username, self.password, http_method)
        dataWorker.signals.finished.connect(self.process_data)
        dataWorker.signals.error.connect(self.on_fetch_data_error)
        dataWorker.signals.progress_bar.connect(self.animate_progress)
        self.threadpool.start(dataWorker)

    def process_data(self, iptv_info, categories, entries_per_stream_type):
        self.categories_per_stream_type = categories
        self.entries_per_stream_type = entries_per_stream_type
        # print(self.entries_per_stream_type['LIVE'])

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

        self.iptv_info_text.setText(formatted_data)
        QtWidgets.qApp.processEvents()

        #Process categories and entries
        for stream_type in self.entries_per_stream_type.keys():
            self.list_widgets[stream_type].clear()
            self.category_list_widgets[stream_type].clear()
            self.category_list_widgets[stream_type].addItem(self.all_categories_text)

            # self.currently_loaded_entries[stream_type] = self.entries_per_stream_type[stream_type]
            for entry in self.entries_per_stream_type[stream_type]:
                self.currently_loaded_entries[stream_type].append(entry)

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

                self.list_widgets[stream_type].addItem(item)

                perc = (idx * 100) / num_of_entries
                if (perc - prev_perc) > 10:
                    prev_perc = perc
                    self.set_progress_bar(int(perc), f"Loading {stream_type} streams: {idx} of {num_of_entries}")
                    QtWidgets.qApp.processEvents()


        self.set_progress_bar(100, f"Finished loading")
        QtWidgets.qApp.processEvents()

    def on_fetch_data_error(self, error_msg):
        print(f"Error occurred while fetching data: {error_msg}")

    def fetch_vod_info(self, vod_id):
        return

    def fetch_series_info(self, series_id):
        return

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

            selected_item_text = selected_item.text()
            selected_item_data = selected_item.data(Qt.UserRole)

            if selected_item_text != self.all_categories_text:
                category_id = selected_item_data['category_id']

            self.set_progress_bar(0, "Loading items")

            self.series_navigation_level = 0
            self.list_widgets[stream_type].clear()
            self.currently_loaded_entries[stream_type].clear()

            for entry in self.entries_per_stream_type[stream_type]:
                # print(entry)
                if selected_item_text == self.all_categories_text:
                    item = QListWidgetItem(entry['name'])
                    item.setData(Qt.UserRole, entry)

                    self.currently_loaded_entries[stream_type].append(entry)
                    self.list_widgets[stream_type].addItem(item)

                elif entry['category_id'] == category_id:
                    item = QListWidgetItem(entry['name'])
                    item.setData(Qt.UserRole, entry)

                    self.currently_loaded_entries[stream_type].append(entry)
                    self.list_widgets[stream_type].addItem(item)

            self.animate_progress(0, 100, "Loading finished")

        except Exception as e:
            print(f"Failed: {e}")

    def streaming_item_double_clicked(self, double_clicked_item):
        try:
            sender = self.sender()

            print(double_clicked_item.text())

            selected_item = sender.currentItem()
            if not selected_item:
                return

            selected_item_text = selected_item.text()
            selected_item_data = selected_item.data(Qt.UserRole)
            print(f"name = {selected_item_text}")

            match self.series_navigation_level:
                case 0: #Highest level, either LIVE, VOD or series
                    if double_clicked_item.text() == self.go_back_text:
                        return

                    stream_type = selected_item_data['stream_type']
                    print(f"level 0: {stream_type}")

                    if stream_type == 'live' or stream_type == 'movie':
                        self.play_item(selected_item_data['url'])

                    elif stream_type == 'series':
                        self.series_navigation_level = 1
                        self.show_seasons(selected_item_data)

                case 1: #Series seasons
                    print("level 1")
                    if selected_item_text == self.go_back_text:
                        self.series_navigation_level = 0
                        self.go_back_to_level(self.series_navigation_level)
                        
                    else:
                        self.series_navigation_level = 2
                        self.show_episodes(selected_item_data)

                case 2: #Series episodes
                    print("level 2")
                    if selected_item_text == self.go_back_text:
                        self.series_navigation_level = 1
                        self.go_back_to_level(self.series_navigation_level)
                        
                    else:
                        #Play episode
                        self.play_item(selected_item_data['url'])

        except Exception as e:
            print(f"failed: {e}")

    def go_back_to_level(self, series_navigation_level):
        self.set_progress_bar(0, "Loading items")

        if series_navigation_level == 0:    #From seasons back to series list
            self.list_widgets['Series'].clear()
            # QtWidgets.qApp.processEvents()

            for entry in self.currently_loaded_entries['Series']:
                item = QListWidgetItem(entry['name'])
                item.setData(Qt.UserRole, entry)

                self.list_widgets['Series'].addItem(item)

        elif series_navigation_level == 1:  #From episodes back to seasons list
            self.list_widgets['Series'].clear()
            # QtWidgets.qApp.processEvents()

            self.list_widgets['Series'].addItem(self.go_back_text)

            for season in self.currently_loaded_entries['Seasons'].keys():
                item = QListWidgetItem(f"Season {season}")
                item.setData(Qt.UserRole, self.currently_loaded_entries['Seasons'][season])

                self.list_widgets['Series'].addItem(item)

        self.animate_progress(0, 100, "Loading finished")

    def show_seasons(self, seasons_data):
        self.set_progress_bar(0, "Loading items")

        #Fetch series info
        headers = {'User-Agent': CUSTOM_USER_AGENT}
        host_url = f"{self.server}/player_api.php"
        params = {
            'username': self.username,
            'password': self.password,
            'action': 'get_series_info',
            'series_id': seasons_data['series_id']
        }

        series_info_resp = requests.get(host_url, params=params, headers=headers, timeout=10)
        series_info_resp.raise_for_status()

        self.series_info_data = series_info_resp.json()

        #Show seasons in list
        self.list_widgets['Series'].clear()
        # QtWidgets.qApp.processEvents()

        self.list_widgets['Series'].addItem(self.go_back_text)

        self.currently_loaded_entries['Seasons'] = self.series_info_data['episodes']

        for season in self.series_info_data['episodes'].keys():
            item = QListWidgetItem(f"Season {season}")
            item.setData(Qt.UserRole, self.series_info_data['episodes'][season])
            # item.setIcon(channel_icon)

            # self.currently_loaded_entries['Seasons'].append(self.series_info_data['episodes'][season])
            self.list_widgets['Series'].addItem(item)

        self.animate_progress(0, 100, "Loading finished")

    def show_episodes(self, episodes_data):
        self.set_progress_bar(0, "Loading items")

        #Clear lists
        self.list_widgets['Series'].clear()
        # QtWidgets.qApp.processEvents()

        self.list_widgets['Series'].addItem(self.go_back_text)

        self.currently_loaded_entries['Episodes'].clear()

        #Show episodes in list
        for episode in episodes_data:
            item = QListWidgetItem(f"{episode['title']}")

            container_extension = episode['container_extension']
            episode_id          = episode['id']
            playable_url = f"{self.server}/series/{self.username}/{self.password}/{episode_id}.{container_extension}"

            episode['url'] = playable_url

            item.setData(Qt.UserRole, episode)

            self.currently_loaded_entries['Episodes'].append(episode)
            self.list_widgets['Series'].addItem(item)

        self.animate_progress(0, 100, "Loading finished")

    def play_item(self, url):
        if self.external_player_command:
            try:
                print(f"Going to play: {url}")
                self.animate_progress(0, 100, "Loading player for streaming")
                subprocess.Popen([self.external_player_command, url])
            except:
                self.animate_progress(0, 100, "Failed playing stream")
        else:
            self.animate_progress(0, 100, "No external player configured")

    def load_epg_data_async(self):
        if not self.server or not self.username or not self.password:
            # Can't load EPG if not logged in
            return
        http_method = self.get_http_method()
        epg_worker = EPGWorker(self.server, self.username, self.password, http_method)
        epg_worker.signals.finished.connect(self.on_epg_loaded)
        epg_worker.signals.error.connect(self.on_epg_error)
        self.threadpool.start(epg_worker)

    def on_epg_loaded(self, epg_data, channel_id_to_names):
        print("EPG data loaded, processing now...")
        self.epg_data = epg_data
        self.channel_id_to_names = channel_id_to_names

        name_to_id = {}
        for cid, names in channel_id_to_names.items():
            for n in names:
                if n not in name_to_id:
                    name_to_id[n] = cid
        self.epg_name_map = name_to_id

        # EPG done
        # self.animate_progress(self.progress_bar.value(), 100, "EPG data loaded")
        self.set_progress_bar(100, "EPG Data Loaded")

    def on_epg_error(self, error_message):
        print(f"Error fetching EPG data: {error_message}")
        self.animate_progress(self.progress_bar.value(), 100, "Error fetching EPG data")

    def choose_external_player(self):
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
                print("External Player selected:", self.external_player_command)

    def show_context_menu(self, position):
        sender = self.sender()
        menu = QMenu()
        sort_action = QAction("Sort Alphabetically", self)
        sort_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_ArrowUp))
        sort_action.triggered.connect(lambda: self.sort_channel_list(sender))
        menu.addAction(sort_action)
        menu.exec_(sender.viewport().mapToGlobal(position))

    def KeyPressed(self, e, search_bar, stream_type):
        search_history_size = len(self.search_history_list)
        text = search_bar.text()

        match e.key():
            case Qt.Key_Return:
                self.list_widgets[stream_type].clear()

                if text:
                    self.search_history_list.insert(0, text)
                    self.search_history_list_idx = 0

                    if search_history_size >= self.max_search_history_size:
                        self.search_history_list.pop(-1)

                self.search_in_list(stream_type, text)

            case Qt.Key_Up:
                #Check if list is empty
                if not self.search_history_list:
                    return

                self.search_history_list_idx += 1
                if self.search_history_list_idx >= search_history_size:
                    self.search_history_list_idx = search_history_size - 1

                search_bar.setText(self.search_history_list[self.search_history_list_idx])

            case Qt.Key_Down:
                #Check if list is empty
                if not self.search_history_list:
                    return

                self.search_history_list_idx -= 1
                if self.search_history_list_idx < 0:
                    self.search_history_list_idx = -1
                    search_bar.clear()
                else:
                    search_bar.setText(self.search_history_list[self.search_history_list_idx])

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

    def update_list_after_search(self, list_widget, stream_type):
        try:
            print("emitted list widget")
            # print(list_widget)

            self.list_widgets[stream_type] = list_widget[0]
        except Exception as e:
            print(f"update after search failed: {e}")

    def search_in_list(self, stream_type, text):
        try:
            self.set_progress_bar(0, f"Loading search results...")

            self.list_widgets[stream_type].clear()

            match self.series_navigation_level:
                case 0: #LIVE/VOD/Series
                    for entry in self.currently_loaded_entries[stream_type]:
                        if text.lower() in entry['name'].lower():
                            item = QListWidgetItem(entry['name'])
                            item.setData(Qt.UserRole, entry)

                            self.list_widgets[stream_type].addItem(item)
                case 1: #Seasons
                    self.list_widgets[stream_type].addItem(self.go_back_text)

                    for season in self.currently_loaded_entries['Seasons'].keys():
                        if text.lower() in f"season {season}":
                            item = QListWidgetItem(f"Season {season}")
                            item.setData(Qt.UserRole, self.currently_loaded_entries['Seasons'][season])

                            self.list_widgets[stream_type].addItem(item)
                case 2: #Episodes
                    self.list_widgets[stream_type].addItem(self.go_back_text)

                    for episode in self.currently_loaded_entries['Episodes']:
                        if text.lower() in episode['title'].lower():
                            item = QListWidgetItem(episode['title'])
                            item.setData(Qt.UserRole, episode)

                            self.list_widgets[stream_type].addItem(item)

            self.set_progress_bar(100, f"Loaded search results")
        except Exception as e:
            print(f"search in list failed: {e}")

    def get_list_widget(self, tab_name):
        return self.list_widgets.get(tab_name)

    def get_category_list_widget(self, tab_name):
        return self.category_list_widgets.get(tab_name)

    def load_external_player_command(self):
        external_player_command = ""

        config = configparser.ConfigParser()
        config.read('config.ini')
        if 'ExternalPlayer' in config:
            # self.external_player_command = config['ExternalPlayer'].get('Command', '')
            external_player_command = config['ExternalPlayer'].get('Command', '')

        return external_player_command

    def save_external_player_command(self):
        config = configparser.ConfigParser()
        config['ExternalPlayer'] = {'Command': self.external_player_command}
        with open('config.ini', 'w') as config_file:
            config.write(config_file)

    def on_epg_checkbox_toggled(self, state):
        # If EPG is checked after we already logged in and no EPG data loaded, start it now.
        if state == Qt.Checked:
            if self.login_type == 'xtream' and self.server and self.username and self.password and not self.epg_data:
                # Reset progress and load EPG
                self.reset_progress_bar()
                self.animate_progress(0, 50, "Loading EPG data...")
                self.load_epg_data_async()

    def open_address_book(self):
        dialog = AddressBookDialog(self)
        dialog.exec_()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    player = IPTVPlayerApp()
    player.show()
    QtWidgets.qApp.processEvents()
    player.load_data_startup()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
