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
    QTreeWidget, QTreeWidgetItem, QTreeView
)

class AccountManager(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("IPTV accounts")
        self.setMinimumSize(400, 300)
        self.parent = parent

        # account_manager_layout = QtWidgets.QVBoxLayout(self)
        account_manager_layout = QtWidgets.QGridLayout(self)

        #Create startup account label with options widget
        self.startup_account_label = QLabel("Startup account:")

        self.startup_account_options = QtWidgets.QComboBox()
        self.startup_account_options.currentTextChanged.connect(self.set_startup_credentials)

        #Create accounts list
        self.accounts_list = QtWidgets.QListWidget()
        self.accounts_list.itemDoubleClicked.connect(self.double_click_account)

        #Create buttons for adding, selecting and deleting accounts
        self.add_button = QPushButton("Add")
        self.add_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogNewFolder))
        self.add_button.clicked.connect(self.add_account)

        self.select_button = QPushButton("Select")
        self.select_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogYesButton))
        self.select_button.clicked.connect(self.select_account)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_DialogCancelButton))
        self.delete_button.clicked.connect(self.delete_account)

        #Add widgets to layout
        account_manager_layout.addWidget(self.startup_account_label,        0, 0)
        account_manager_layout.addWidget(self.startup_account_options,      0, 1, 1, 2)
        account_manager_layout.addWidget(self.accounts_list,                1, 0, 1, 3)
        account_manager_layout.addWidget(self.add_button,                   2, 0)
        account_manager_layout.addWidget(self.select_button,                2, 1)
        account_manager_layout.addWidget(self.delete_button,                2, 2)

        #Load saved accounts from .ini file
        self.load_saved_accounts()

    def set_startup_credentials(self):
        selected_item = self.startup_account_options.currentText()

        config = configparser.ConfigParser()
        config.read(self.parent.user_data_file)

        if 'Startup credentials' not in config:
            config['Startup credentials'] = {}

        config['Startup credentials']['startup_credentials'] = f"{selected_item}"

        with open(self.parent.user_data_file, 'w') as config_file:
            config.write(config_file)

    def load_saved_accounts(self):
        self.startup_account_options.currentTextChanged.disconnect(self.set_startup_credentials)

        self.accounts_list.clear()
        self.startup_account_options.clear()
        self.startup_account_options.addItem("None")

        config = configparser.ConfigParser()
        config.read(self.parent.user_data_file)

        if 'Credentials' in config:
            for key in config['Credentials']:
                self.accounts_list.addItem(key)
                self.startup_account_options.addItem(key)

        if 'Startup credentials' in config:
            selected_startup_credentials = config['Startup credentials']['startup_credentials']
            idx = self.startup_account_options.findText(f"{selected_startup_credentials}")
            self.startup_account_options.setCurrentIndex(idx)

        self.startup_account_options.currentTextChanged.connect(self.set_startup_credentials)

    def add_account(self):
        dialog = AddAccountDialog(self)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            method, name, *credentials = dialog.get_credentials()

            if name:
                config = configparser.ConfigParser()
                config.read(self.parent.user_data_file)

                if 'Credentials' not in config:
                    config['Credentials'] = {}

                if method == 'manual':
                    server, username, password = credentials
                    config['Credentials'][name] = f"manual|{server}|{username}|{password}"

                elif method == 'm3u_plus':
                    m3u_url, = credentials
                    config['Credentials'][name] = f"m3u_plus|{m3u_url}"

                with open(self.parent.user_data_file, 'w') as config_file:
                    config.write(config_file)

                self.load_saved_accounts()

    def select_account(self):
        selected_item = self.accounts_list.currentItem()

        if selected_item:
            name = selected_item.text()

            config = configparser.ConfigParser()
            config.read(self.parent.user_data_file)

            if 'Credentials' in config and name in config['Credentials']:
                data = config['Credentials'][name]

                if data.startswith('manual|'):
                    _, server, username, password = data.split('|')
                    # self.parent.server_entry.setText(server)
                    # self.parent.username_entry.setText(username)
                    # self.parent.password_entry.setText(password)
                    self.parent.server = server
                    self.parent.username = username
                    self.parent.password = password

                    self.parent.login()

                elif data.startswith('m3u_plus|'):
                    _, m3u_url = data.split('|', 1)
                    self.parent.extract_credentials_from_m3u_plus_url(m3u_url)

                    self.parent.login()

                self.accept()

    def double_click_account(self, item):
        self.select_account()
        self.accept()

    def delete_account(self):
        selected_item = self.accounts_list.currentItem()

        if selected_item:
            name = selected_item.text()

            config = configparser.ConfigParser()
            config.read(self.parent.user_data_file)

            if 'Credentials' in config and name in config['Credentials']:
                del config['Credentials'][name]

                with open(self.parent.user_data_file, 'w') as config_file:
                    config.write(config_file)

                self.load_saved_accounts()

class AddAccountDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Credentials")
        layout = QtWidgets.QVBoxLayout(self)

        self.method_selector = QtWidgets.QComboBox()
        self.method_selector.addItems(["Manual/Xtream entry", "M3U_plus URL entry"])
        layout.addWidget(QtWidgets.QLabel("Select Method:"))
        layout.addWidget(self.method_selector)

        self.stack = QtWidgets.QStackedWidget()
        layout.addWidget(self.stack)

        self.manual_form = QtWidgets.QWidget()
        manual_layout = QFormLayout(self.manual_form)

        self.name_entry_manual  = QLineEdit()
        self.server_entry       = QLineEdit()
        self.username_entry     = QLineEdit()
        self.password_entry     = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)

        manual_layout.addRow("Name:", self.name_entry_manual)
        manual_layout.addRow("Server URL:", self.server_entry)
        manual_layout.addRow("Username:", self.username_entry)
        manual_layout.addRow("Password:", self.password_entry)

        #Set placeholder texts for xtream credentials
        self.name_entry_manual.setPlaceholderText("Custom account name")
        self.server_entry.setPlaceholderText("e.g. http://xtreamcode.ex/")
        self.username_entry.setPlaceholderText("e.g. abcde12345")
        self.password_entry.setPlaceholderText("e.g. fghij67890")

        self.m3u_form = QtWidgets.QWidget()
        m3u_layout = QFormLayout(self.m3u_form)

        self.name_entry_m3u = QLineEdit()
        self.m3u_url_entry  = QLineEdit()

        m3u_layout.addRow("Name:", self.name_entry_m3u)
        m3u_layout.addRow("m3u_plus URL:", self.m3u_url_entry)

        #Set placeholder texts for m3u credentials
        self.name_entry_m3u.setPlaceholderText("Custom account name")
        self.m3u_url_entry.setPlaceholderText("e.g. http://xtreamcode.ex/get.php?username=Mike&password=1234&type=m3u_plus&output=ts")

        self.stack.addWidget(self.manual_form)
        self.stack.addWidget(self.m3u_form)

        self.method_selector.currentIndexChanged.connect(self.stack.setCurrentIndex)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def validate_and_accept(self):
        method = self.method_selector.currentText()

        if method == "Manual Entry":
            name        = self.name_entry_manual.text().strip()
            server      = self.server_entry.text().strip()
            username    = self.username_entry.text().strip()
            password    = self.password_entry.text().strip()

            if not name or not server or not username or not password:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Please fill all fields for Manual Entry.")
                return

            self.accept()
        else:
            name    = self.name_entry_m3u.text().strip()
            m3u_url = self.m3u_url_entry.text().strip()

            if not name or not m3u_url:
                QtWidgets.QMessageBox.warning(self, "Input Error", "Please fill all fields for m3u_plus URL Entry.")
                return

            self.accept()

    def get_credentials(self):
        method = self.method_selector.currentText()

        if method == "Manual Entry":
            name        = self.name_entry_manual.text().strip()
            server      = self.server_entry.text().strip()
            username    = self.username_entry.text().strip()
            password    = self.password_entry.text().strip()

            return ('manual', name, server, username, password)
        else:
            name    = self.name_entry_m3u.text().strip()
            m3u_url = self.m3u_url_entry.text().strip()

            return ('m3u_plus', name, m3u_url)