#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
NFC Type3
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2020'

import nfc
import threading
import queue

from MyLogger import get_logger
import click
CONTEXT_SETTINGS = dict(help_option_names=['-1h', '--help'])


class App:
    """
    targets: ['212F' , '106A', '106B']   # default
    targets: ['212F' , '424F']           # Type3に限定？
    """
    _log = get_logger(__name__, False)

    def __init__(self, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('')

        self._idq = queue.Queue()
        self._targets = ['212F', '424F']
        self._sense_th = threading.Thread(target=self.sense,
                                          args=( self._targets, ),
                                          daemon=True)

        self._active = False

    def main(self):
        self._log.debug('')

        self._active = True
        self._sense_th.start()

        while self._active:
            try:
                id_str = self._idq.get(timeout=1.0)
                self._log.info('id_str=%s', id_str)

            except queue.Empty as e:
                self._log.debug('%s:%s', type(e).__name__, e)
                continue

            except Exception as e:
                self._log.error('%s:%s', type(e).__name__, e)
                break

        self._log.warning('done')

    def end(self):
        self._log.debug('')
        self._active = False

    def sense(self, targets):
        self._log.debug('targets=%s', targets)

        with nfc.ContactlessFrontend('usb') as clf:
            rdwr = {
                'targets': targets,
                'on-startup': self.startup,
                'on-connect': self.connect,
                'on-release': self.release,
            }
            clf.connect(rdwr=rdwr)

        self._active = False  # 異常終了
        self._log.debug('done')

    def startup(self, targets):
        self._log.debug('targets=%s', targets)

        for t in targets:
            self._log.debug('t=%s', t)

        return targets

    def connect(self, tag):
        self._log.debug('tag=%s', tag)

        id_str = bytes.hex(tag.identifier)
        self._log.debug('id_str=%s', id_str)

        self._idq.put(id_str)

        return True

    def release(self, tag):
        self._log.debug('tag=%s', tag)


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    '--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    _log = get_logger(__name__, debug)

    app = App(debug=debug)
    try:
        app.main()
    finally:
        _log.info('finally')
        app.end()


if __name__ == '__main__':
    main()
