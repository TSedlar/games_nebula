#!/usr/bin/env python
# -*- coding: utf-8; -*-

import os
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, Gdk
import gettext

from modules.set_nebula_dir import set_nebula_dir
from modules.setup_cookies import setup_cookies
from modules.pygogdownloader import Pygogdownloader
from modules_gui import tab_gogcom, tab_goglib, pygogauth

style_provider = Gtk.CssProvider()

css = b"""
.black_background {
    background: black;
}
.lighter_background {
    background: lighter(@theme_bg_color);
}
"""

style_provider.load_from_data(css)

Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

nebula_dir = set_nebula_dir()

gettext.bindtextdomain('games_nebula', nebula_dir + '/locale')
gettext.textdomain('games_nebula')
_ = gettext.gettext

CONFIG_PATH = os.getenv('HOME') + '/.config/games_nebula/'

# TODO Move to config file
tab_gogcom_enabled = False
tab_goglib_enabled = True

class GamesNebula:

    def __init__(self):

        setup_cookies()
        self.pygogdownloader = Pygogdownloader()

        if not os.path.exists(CONFIG_PATH + 'token.json'):

            response = pygogauth.PyGogAuth().run()

            if response == 0:
                self.pygogdownloader.activate_gogapi()
                self.create_main_window()
            else:
                print(_("Authorization failed"))
                # TODO Start in offline mode if possible
                sys.exit() # Temp

        else:
            self.pygogdownloader.activate_gogapi()
            self.create_main_window()

    def create_main_window(self):

        app_icon = GdkPixbuf.Pixbuf.new_from_file(nebula_dir + '/images/icon.png')

        self.main_window = Gtk.Window(
            title = "Games Nebula",
            type = Gtk.WindowType.TOPLEVEL,
            window_position = Gtk.WindowPosition.CENTER,
            icon = app_icon,
            height_request = 280
        )
        self.main_window.connect('delete-event', self.quit_app)

        self.notebook = Gtk.Notebook(
            show_tabs = True
        )
        self.notebook.set_group_name('games_nebula')

        self.main_window.add(self.notebook)
        self.add_tabs()

    def add_tabs(self):

        if tab_gogcom_enabled:
            tab_content = tab_gogcom.TabGogCom().create()
            self.create_tab(tab_content, _("GOG.COM"))

        if tab_goglib_enabled:
            tab_content = tab_goglib.TabGogLib().create()
            self.create_tab(tab_content, _("GOG LIBRARY"))

        self.main_window.show_all()

    def create_tab(self, tab_content, tab_title):

        label = Gtk.Label(label=tab_title)
        self.notebook.append_page(tab_content, label)

    def quit_app(self, window, event):

        # TODO save_config()
        Gtk.main_quit()

def main():
    app = GamesNebula()
    Gtk.main()

if __name__ == '__main__':
    sys.exit(main())
