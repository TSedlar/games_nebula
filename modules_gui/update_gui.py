import gettext

from modules.set_nebula_dir import set_nebula_dir

nebula_dir = set_nebula_dir()

gettext.bindtextdomain('games_nebula', nebula_dir + '/locale')
gettext.textdomain('games_nebula')
_ = gettext.gettext

def button(button, event_type):

    if event_type == 'install':
        button.set_label(_("Installing"))
        button.set_sensitive(False)
    elif event_type == 'install_completed':
        button_play = button.get_parent().get_children()[0]
        button.set_label(_("Uninstall"))
        button.set_sensitive(True)
        button_play.set_sensitive(True)

