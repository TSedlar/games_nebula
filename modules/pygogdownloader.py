# TODO Info about download: Part of installer - Full size of file - Downloaded (file) - Percentage (file) - Speed
#                       or: Full size (all parts) - Downloaded - Percentage - Speed
# TODO Download dlcs
# TODO Download language specific installers in separate directory
# TODO Add to db supported languages (?)
# TODO Add to db supported tags (?)

import os
import sys
import hashlib
from gogapi.base import GogObject
from gogapi import GogApi, Token, get_auth_url
import gogapi.api
from gogapi.download import Download
from urllib.request import Request as urllib_request
from urllib.request import urlopen as urllib_urlopen
import gettext

from modules.set_nebula_dir import set_nebula_dir
from modules.gamesdb import GamesDB

nebula_dir = set_nebula_dir()
gettext.bindtextdomain('games_nebula', nebula_dir + '/locale')
gettext.textdomain('games_nebula')
_ = gettext.gettext

CONFIG_PATH = os.getenv('HOME') + '/.config/games_nebula/'

class Pygogdownloader:

    def __init__(self):

        self.gamesdb = GamesDB(CONFIG_PATH)

    def activate_gogapi(self):

        token = Token.from_file(CONFIG_PATH + 'token.json')
        if token.expired():
            token.refresh()
            token.save(CONFIG_PATH + 'token.json')
        self.api = GogApi(token)

    def get_games_data(self):

        if not os.path.exists(CONFIG_PATH + '/games.db'):
            self.request_games_data()

        games_data = self.gamesdb.get_games_data()

        return games_data

    def get_ids_list(self):

        if not os.path.exists(CONFIG_PATH + '/games.db'):
            ids_list = self.request_ids_list()
        else:
            ids_list = self.gamesdb.get_ids()

        return ids_list

    def request_ids_list(self):

        temp_dict = self.api.web_user_games()
        ids_list = temp_dict['owned']

        return ids_list

    def request_games_data(self):

        def is_native(prod):

            for i in range(len(prod.installers)):
                installer = prod.installers[i]
                if installer.os == 'linux':
                    return True

            return False

        ids_list = self.get_ids_list()
        games_list = []

        for game_id in ids_list:

            prod = self.api.product(game_id)
            prod.update_galaxy(expand=True)

            # Second condition to filter movies and some other non-game content
            if (prod.type == 'game') and (len(prod.installers) > 0):

                name = prod.slug
                title = prod.title
                native = str(is_native(prod))
                logo = 'https:' + ''.join(prod.image_logo.split('_glx_logo'))
                icon = 'https:' + prod.image_icon
                dlcs = prod.dlcs

                print(title)

                dlcs_str = ''
                if len(dlcs) > 0:
                    for i in range(len(dlcs)):
                        if i != (len(dlcs) - 1):
                            dlcs_str += str(dlcs[i].id) + '; '
                        else:
                            dlcs_str += str(dlcs[i].id)

                games_list.append((name, game_id, title, native, logo, icon, dlcs_str))

        self.gamesdb.write(games_list)

    def write_md5_to_file(self, file_path, md5):

        f = open(file_path + '.md5', 'w')
        f.write(md5)
        f.close()

    def recalculate_md5(self, file_path):

        md5 = hashlib.md5()
        f = open(file_path, 'rb')
        chunk_size = 4096

        while True:

            chunk = f.read(chunk_size)

            if not chunk:
                break

            md5.update(chunk)

        return md5.hexdigest()

    def download(self, game_name, lang, dest_dir):

        if dest_dir[-1] != '/':
            dest_dir += '/'

        games_data = self.get_games_data()
        game_id = games_data[game_name][0]
        prod = self.api.product(game_id)
        prod.update_galaxy(expand=True)

        installer_id_linux_en = -1
        installer_id_linux_lang = -1
        installer_id_windows = 0
        for i in range(len(prod.installers)):
            installer = prod.installers[i]
            if installer.os == 'windows':
                if installer.language == lang: installer_id_windows = i
            elif installer.os == 'linux':
                if installer.language == 'en': installer_id_linux_en = i
                elif installer.language == lang: installer_id_linux_lang = i

        if installer_id_linux_lang != -1:
            installer_id = installer_id_linux_lang
        elif installer_id_linux_en != -1:
            installer_id = installer_id_linux_en
            lang = 'en'
        else:
            installer_id = installer_id_windows
            if installer_id_windows == 0: lang = 'en'

        for fileobj in prod.installers[installer_id].files:
            fileobj.update_chunklist()
            file_name = fileobj.filename
            file_md5 = fileobj.md5
            download_dir = dest_dir + game_name + '/' + lang + '/'
            if not os.path.exists(download_dir): os.makedirs(download_dir)
            dest_path = download_dir + file_name
            download_link = fileobj.securelink
            self.get_file(download_link, dest_path, file_md5)

    def get_file(self, url, file_path, file_md5):

        req = urllib_request(url)
        file_to_download = urllib_urlopen(req)
        file_size = float(file_to_download.getheader('Content-Length'))

        def md5_exists(old_file_md5):

            if file_md5 == old_file_md5:
                print(_("Already fully downloaded. Skipping."))
            else:
                print(_("File exists, but new version available"))
                #TODO Decide what to do: keep old or download new version

        if not os.path.exists(file_path):

            self.write_md5_to_file(file_path, file_md5)

            f = open(file_path, 'wb')
            downloaded = 0

        else:

            downloaded = os.path.getsize(file_path)

            if downloaded >= file_size:

                if os.path.exists(file_path + '.md5'):

                    old_file_md5 = open(file_path + '.md5', 'r').read()
                    md5_exists(old_file_md5)

                else:

                    print(_("Already exists. MD5 unknown. Recalculating MD5."))

                    old_file_md5 = self.recalculate_md5(file_path)
                    self.write_md5_to_file(file_path, old_file_md5)
                    md5_exists(old_file_md5)

                return

            else:

                if os.path.exists(file_path + '.md5'):

                    old_file_md5 = open(file_path + '.md5', 'r').read()

                    if file_md5 == old_file_md5:

                        print(_("File partially downloaded. Resuming download."))
                        req.add_header('Range','bytes=%d-' % downloaded)
                        file_to_download = urllib_urlopen(req)
                        f = open(file_path, 'ab')

                    else:

                        print(_("File partially downloaded, but it's no longer ") +
                                _("available on server. Donwloading new version."))

                        self.write_md5_to_file(file_path, file_md5)

                        f = open(file_path, 'wb')
                        downloaded = 0
                else:

                    print(_("File partially downloaded, but MD5 unknown.") +
                            _(" Re-downloading file."))

                    self.write_md5_to_file(file_path, file_md5)

                    f = open(file_path, 'wb')
                    downloaded = 0

        block_size = 8192

        while True:

            file_chunk = file_to_download.read(block_size)

            if not file_chunk:
                break

            downloaded += len(file_chunk)
            f.write(file_chunk)

            # Downloaded MB, %
            print('%5.2f MB, %3.2f%%' % (downloaded/1048576, downloaded*100./file_size))

        f.close()
