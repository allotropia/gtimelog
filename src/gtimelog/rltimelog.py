#!/usr/bin/python

'''A readline interface for gtimelog.'''

from __future__ import print_function

import os
import signal
from datetime import datetime, timedelta

from gtimelog import (Settings, configdir, soup_session, TimeLog,
                      RemoteTaskList, TaskList, TZOffset)


class MainWindow(object):
    '''Simple readline interface for gtimelog.'''

    def __init__(self, timelog, tasks):
        self.timelog = timelog
        self.tasks = tasks

        self.display_time_window(timelog.window)
        print()
        self.setup_readline()

    def setup_readline(self):
        '''Setup readline for our completer.'''
        import readline
        readline.parse_and_bind('tab: complete')
        readline.set_completer_delims('')
        readline.set_completer(self.completer)

    def completer(self, text, state):
        '''Returns the state-th result for text, or None.'''
        items = self.tasks.items
        results = [x + ': ' for x in items if x.startswith(text)] + [None]
        return results[state]

    def run(self):
        '''Main loop'''
        while True:
            self.tasks.check_reload()
            try:
                line = raw_input('timelog> ')
            except EOFError:
                print()
                break
            if not line:
                continue
            self.timelog.append(line)
            self.display_last_minute()
            print()

    def display_last_minute(self):
        '''Display the timelog messages of the past minute.'''
        now = datetime.now(TZOffset())
        time_window = self.timelog.window_for(now - timedelta(minutes=1), now)
        self.display_time_window(time_window)

    def display_time_window(self, time_window):
        '''Display the timelog messages of the current day.'''
        for message in time_window.all_entries():
            self.display_message(*message)

    def display_message(self, start, end, duration, message):
        '''Display one timelog message.'''
        if '**' in message:
            print('[%s] [32m%s[0m' % (end, message))
        elif message.startswith(tuple(self.tasks.items)):
            print('[%s] %s' % (end, message))
        else:
            print('[%s] [31;1m%s[0m' % (end, message))


def main():
    '''Entry point, copy/pasted from gtimelog.Application but without GTK+.'''
    settings = Settings()
    settings_file = os.path.join(configdir, 'gtimelogrc')
    if not os.path.exists(settings_file):
        settings.save(settings_file)
    else:
        settings.load(settings_file)
        if settings.server_cert and os.path.exists(settings.server_cert):
            soup_session.set_property('ssl-ca-file', settings.server_cert)
    timelog = TimeLog(os.path.join(configdir, 'timelog.txt'),
                      settings.virtual_midnight, settings.autoarrival)
    if settings.task_list_url:
        tasks = RemoteTaskList(settings,
                               os.path.join(configdir, 'remote-tasks.txt'))
    else:
        tasks = TaskList(os.path.join(configdir, 'tasks.txt'))
    main_window = MainWindow(timelog, tasks)
    # Make ^C terminate gtimelog when hanging
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main_window.run()

if __name__ == '__main__':
    main()
