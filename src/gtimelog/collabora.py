"""
A temporary holding zone for troublesome things.
"""

import datetime
import functools
import os

from gi.repository import GObject, Gtk, Soup

from gtimelog.timelog import TaskList
from gtimelog.tzoffset import TZOffset

# Global HTTP stuff

class Authenticator(object):
    # try to use GNOME Keyring if available
    try:
        import gnomekeyring
    except ImportError:
        gnomekeyring = None

    def __init__(self):
        object.__init__(self)
        self.pending = []
        self.lookup_in_progress = False

    def find_in_keyring(self, uri, callback):
        """Attempts to load a username and password from the keyring, if the
        keyring is available"""
        if self.gnomekeyring is None:
            callback(None, None)
            return

        username = None
        password = None

        try:
            # FIXME - would be nice to make all keyring calls async, to dodge
            # the possibility of blocking the UI. The code is all set up for
            # that, but there's no easy way to use the keyring asynchronously
            # from Python (as of Gnome 3.2)...
            l = self.gnomekeyring.find_network_password_sync(
                None,       # user
                uri.get_host(), # domain
                uri.get_host(), # server
                None,       # object
                uri.get_scheme(),   # protocol
                None,       # authtype
                uri.get_port())       # port
        except self.gnomekeyring.NoMatchError:
            # We didn't find any passwords, just continue
            pass
        except self.gnomekeyring.NoKeyringDaemonError:
            pass
        except IOError:
            gnomekeyring = None
        except gnomekeyring.IOError: # thanks, gnomekeyring python binding maker
            gnomekeyring = None
        else:
            l = l[-1] # take the last key (Why?)
            username = l['user']
            password = l['password']

        callback(username, password)

    def save_to_keyring(self, uri, username, password):
        try:
            self.gnomekeyring.set_network_password_sync(
                None,               # keyring
                username,   # user
                uri.get_host(),     # domain
                uri.get_host(),     # server
                None,               # object
                uri.get_scheme(),   # protocol
                None,               # authtype
                uri.get_port(),             # port
                password)   # password
        except self.gnomekeyring.NoKeyringDaemonError:
            pass

    def ask_the_user(self, auth, uri, callback):
        """Pops up a username/password dialog for uri"""
        d = Gtk.Dialog()
        d.set_title('Authentication Required')
        d.set_resizable(False)

        grid = Gtk.Grid()
        grid.set_border_width(5)
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)

        l = Gtk.Label('Authentication is required for the domain "%s".' % auth.get_realm())
        l.set_line_wrap(True)
        grid.attach(l, 0, 0, 2, 1)

        username_label = Gtk.Label("Username:")
        grid.attach_next_to(username_label, l, Gtk.PositionType.BOTTOM, 1, 1)

        password_label = Gtk.Label("Password:")
        grid.attach_next_to(password_label, username_label, Gtk.PositionType.BOTTOM, 1, 1)

        userentry = Gtk.Entry()
        userentry.set_hexpand(True)
        passentry = Gtk.Entry()
        passentry = Gtk.Entry()
        passentry.set_visibility(False)

        userentry.set_activates_default(True)
        passentry.set_activates_default(True)

        grid.attach_next_to(userentry, username_label, Gtk.PositionType.RIGHT, 1, 1)
        grid.attach_next_to(passentry, password_label, Gtk.PositionType.RIGHT, 1, 1)

        if self.gnomekeyring:
            savepasstoggle = Gtk.CheckButton("Save Password in Keyring")
            savepasstoggle.set_active(True)
            grid.attach_next_to(savepasstoggle, passentry,
                                Gtk.PositionType.BOTTOM, 1, 1)

        d.vbox.pack_start(grid, True, True, 0)
        d.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        ok_button = d.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)
        d.set_default(ok_button)

        def update_ok_sensitivity(*args):
            ok_button.set_sensitive(userentry.get_text() and passentry.get_text())
        userentry.connect('notify::text', update_ok_sensitivity)
        passentry.connect('notify::text', update_ok_sensitivity)
        update_ok_sensitivity()

        def on_response(dialog, r):
            save_to_keyring = self.gnomekeyring and savepasstoggle.get_active()

            if r == Gtk.ResponseType.OK:
                username = userentry.get_text()
                password = passentry.get_text()

                if username and password and save_to_keyring:
                    self.save_to_keyring(uri, username, password)

            else:
                username = None
                password = None

            d.destroy()
            callback(username, password)

        d.connect('response', on_response)
        d.show_all()

    def find_password(self, auth, uri, retrying, callback):
        def keyring_callback(username, password):
            # If not found, ask the user for it
            if username is None or retrying:
                GObject.idle_add(lambda: self.ask_the_user(auth, uri, callback))
            else:
                callback(username, password)

        self.find_in_keyring(uri, keyring_callback)

    def http_auth_cb(self, session, message, auth, retrying, *args):
        session.pause_message(message)
        self.pending.insert(0, (session, message, auth, retrying))
        self.maybe_pop_queue()

    def maybe_pop_queue(self):
        # I don't think we need any locking, because GIL.
        if self.lookup_in_progress:
            return

        try:
            (session, message, auth, retrying) = self.pending.pop()
        except IndexError:
            pass
        else:
            self.lookup_in_progress = True
            uri = message.get_uri()
            self.find_password(
                auth,
                uri,
                retrying,
                callback=functools.partial(
                    self.http_auth_finish, session, message, auth)
            )

    def http_auth_finish(self, session, message, auth, username, password):
        if username and password:
            auth.authenticate(username, password)

        session.unpause_message(message)
        self.lookup_in_progress = False
        self.maybe_pop_queue()

soup_session = Soup.SessionAsync()
authenticator = Authenticator()
soup_session.connect('authenticate', authenticator.http_auth_cb)

class RemoteTaskList(TaskList):
    """Task list stored on a remote server.

    Keeps a cached copy of the list in a local file, so you can use it offline.
    """

    def __init__(self, settings, cache_filename):
        self.url = settings.task_list_url
        TaskList.__init__(self, cache_filename)
        self.settings = settings

        #Even better would be to use the Expires: header on the list itself I suppose...
        self.max_age = settings.task_list_expiry

        mtime = self.get_mtime()
        if mtime:
            self.last_time = datetime.datetime.fromtimestamp(mtime, TZOffset())
        else:
            self.last_time = datetime.datetime.now(TZOffset()) - self.max_age * 2

    def check_reload(self):
        """Check whether the task list needs to be reloaded.

        Download the task list if this is the first time, and a cached copy is
        not found.

        Returns True if the file was reloaded.
        """
        if datetime.datetime.now(TZOffset()) - self.last_time > self.max_age:
            self.last_time = datetime.datetime.now(TZOffset())
            #Always redownload if past the expiry date.
            self.download()
            return True
        return TaskList.check_reload(self)

    def download_finished_cb(self, session, message, *args):
        if message.status_code == 200:
            try:
                out = open(self.filename, 'w')
                out.write(message.response_body.data)
            except IOError, e:
                print e
                if self.error_callback:
                    self.error_callback()
            finally:
                out.close()
                self.load_file()
        else:
            if self.error_callback:
                self.error_callback()

    def download(self):
        """Download the task list from the server."""
        if self.loading_callback:
            self.loading_callback()

        if not os.path.exists(self.settings.server_cert):
            self.error_callback("Certificate file not found")
            return

        message = Soup.Message.new('GET', self.url)
        soup_session.queue_message(message, self.download_finished_cb, None)

    def load_file(self):
        """Load the file in the UI"""
        self.load()
        if self.loaded_callback:
            self.loaded_callback()

    def reload(self):
        """Reload the task list."""
        self.download()
