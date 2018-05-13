#!/usr/bin/env python
# -*- Mode: Python; coding: utf-8; -*-

import os
import sys
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib#, GObject
from gi.repository.GdkPixbuf import InterpType
import gettext

import time # TODO Temp. Remove

from modules_gui import update_gui
from modules.set_nebula_dir import set_nebula_dir
from modules.pygogdownloader import Pygogdownloader
from modules.gamesdb import GamesDB

nebula_dir = set_nebula_dir()

gettext.bindtextdomain('games_nebula', nebula_dir + '/locale')
gettext.textdomain('games_nebula')
_ = gettext.gettext

image_path_global = nebula_dir + '/images/goglib/'
CONFIG_PATH = os.getenv('HOME') + '/.config/games_nebula/'

# TODO Change to correct path
image_path_user = os.getenv('HOME') + '/.games_nebula/images/goglib/'

# TODO Move to config file
banners_scale = 0.5
dir_download = '/media/Hitachi/Distrib/Games/GOG/'
dir_install ='/home/duser/Games/GOG Games'
lang = 'en'

class TabGogLib:

    def create(self):

        self.pygogdownloader = Pygogdownloader()
        self.pygogdownloader.activate_gogapi()
        self.gamesdb = GamesDB(CONFIG_PATH)

        games_dict = self.pygogdownloader.get_games_data()
        games_list = sorted(games_dict)

        box_goglib = Gtk.Box(
                orientation = Gtk.Orientation.VERTICAL,
                homogeneous = False,
                name = 'tab_goglib',
        )

################################################################################

        box_filters = Gtk.Box(
                orientation = Gtk.Orientation.HORIZONTAL,
                homogeneous = False,
                margin_left = 10,
                margin_right = 10,
                margin_top = 10,
                margin_bottom = 10,
                spacing = 10
        )

        search_entry = Gtk.SearchEntry(
                placeholder_text = _("Search"),
                halign = Gtk.Align.FILL,
                sensitive = False # FIX
        )
        #~ search_entry.connect('search-changed', self.search_filter)

        combobox_filter_status = Gtk.ComboBoxText(
                tooltip_text = _("Status filter"),
                name = 'combobox_goglib_status',
                sensitive = False # FIX
        )

        status_list = [_("No filter"), _("Installed"), _("Unavailable")]

        for i in range(len(status_list)):
            combobox_filter_status.append_text(status_list[i])
            #~ if status_list[i] == self.status_filter:
                #~ combobox_filter_status.set_active(i)
        #~ combobox_filter_status.connect('changed', self.cb_combobox_filter_status)
        #~ combobox_filter_status.connect('button-press-event', self.cb2_comboboxes_filters)
        combobox_filter_status.set_active(0) # TODO Temp

        combobox_filter_tags1 = Gtk.ComboBoxText(
                tooltip_text = _("Tags filter 1"),
                name = 'combobox_filter_tags1',
                sensitive = False # FIX
        )
        combobox_filter_tags1.append_text(_("No filter"))
        combobox_filter_tags1.append_text(_("No tags"))
        combobox_filter_tags1.set_active(0) # TODO Temp

        img_add = Gtk.Image.new_from_icon_name("list-add", Gtk.IconSize.SMALL_TOOLBAR)
        button_filter_add = Gtk.Button(
                name = 'add',
                image = img_add,
                #~ no_show_all = True,
                tooltip_text = _("Add tags filter"),
                sensitive = False # FIX
        )
        #~ button_filter_add.connect('clicked', self.tag_filters_number_changed)

        #~ adjustment_scale_banner = Gtk.Adjustment(self.scale_level, 0.4, 1, 0.1, 0.3)
        adjustment_scale_banner = Gtk.Adjustment(banners_scale, 0.4, 1, 0.1, 0.3)
        #~ adjustment_scale_banner.connect('value-changed', self.cb_adjustment_scale_banner)
        adjustment_scale_banner.set_value(banners_scale)
        scale_banner = Gtk.Scale(
                tooltip_text = _("Scale"),
                orientation = Gtk.Orientation.HORIZONTAL,
                halign = Gtk.Align.END,
                valign = Gtk.Align.CENTER,
                width_request = 150,
                draw_value = False,
                show_fill_level = True,
                adjustment = adjustment_scale_banner,
                sensitive = False # FIX
        )

        box_filters.pack_start(search_entry, True, True, 0)
        box_filters.pack_start(combobox_filter_status, False, False, 0)
        box_filters.pack_start(combobox_filter_tags1, False, False, 0)
        box_filters.pack_start(button_filter_add, False, False, 0)
        box_filters.pack_start(scale_banner, False, False, 0)

################################################################################

        scrolled_window = Gtk.ScrolledWindow()

        flowbox = Gtk.FlowBox(
                max_children_per_line = 42,
                selection_mode = Gtk.SelectionMode.NONE,
                row_spacing = 20,
                column_spacing = 20,
                margin_left = 20,
                margin_right = 20,
                margin_top = 20,
                margin_bottom = 20
        )

        for game_name in games_list:

            is_native = self.gamesdb.is_native(game_name)
            tooltip = games_dict[game_name][1]

            game_grid = Gtk.Grid(
                    can_focus=False,
                    column_homogeneous = True,
                    sensitive = is_native
            )

            image_path_0 = image_path_global + game_name + '.jpg'
            image_path_1 = image_path_user + game_name + '.jpg'
            if os.path.exists(image_path_1):
                image_path = image_path_1
            elif os.path.exists(image_path_0):
                image_path = image_path_0
            else:
                # Download or create image
                pass

            pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)

            pixbuf = pixbuf.scale_simple(
                    518 * banners_scale,
                    240 * banners_scale,
                    InterpType.BILINEAR
            )

            game_image = Gtk.Image(
                    name = game_name,
                    tooltip_text = tooltip,
                    pixbuf = pixbuf
            )

            button_setup = Gtk.Button(
                    name = game_name,
                    label = _("Install")
            )
            button_setup.connect('clicked', self.button_setup_clicked)

            button_play = Gtk.Button(
                    name = game_name,
                    label = _("Play"),
                    sensitive = False
            )

            if not is_native:

                label_not_available = Gtk.Label(
                        label = _("Not available"),
                        tooltip_text = tooltip,
                        halign = Gtk.Align.CENTER,
                        valign = Gtk.Align.CENTER
                )

                background = Gtk.Image(
                        opacity=0.75,
                        tooltip_text = tooltip
                )

                background_ctx = background.get_style_context()
                background_ctx.add_class('black_background')

                game_grid.attach(label_not_available, 0, 0, 2, 1)
                game_grid.attach(background, 0, 0, 2, 1)

            game_grid.attach(game_image, 0, 0, 2, 1)
            game_grid.attach(button_setup, 0, 1, 1, 1)
            game_grid.attach(button_play, 1, 1, 1, 1)

            flowbox_child = Gtk.FlowBoxChild(halign=Gtk.Align.CENTER)
            flowbox_child.add(game_grid)
            flowbox.add(flowbox_child)

################################################################################

        scrolled_window.add(flowbox)

        box_goglib.pack_start(box_filters, False, False, 0)
        box_goglib.pack_start(scrolled_window, True, True, 0)

        return box_goglib

    def button_setup_clicked(self, button):

        update_gui.button(button, 'install')
        self.start_thread(self.download, (button,))

    def download(self, button):

        game_name = button.get_name()
        self.pygogdownloader.download(game_name, lang, dir_download)
        self.start_thread(self.install, (button,))

    def install(self, button):

        self._extractor_placeholder()
        GLib.idle_add(update_gui.button, button, 'install_completed')

    def start_thread(self, target_func, args):

        if args != None:
            thread = threading.Thread(target=target_func, args=args)
        else:
            thread = threading.Thread(target=target_func)

        thread.daemon = True
        thread.start()

################################################################################

    def _extractor_placeholder(self):

        print("Extracting")
        os.system('sleep 1')
        print("10%")
        os.system('sleep 1')
        print("50%")
        os.system('sleep 1')
        print("100%")
        os.system('sleep 1')
