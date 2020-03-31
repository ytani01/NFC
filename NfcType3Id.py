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
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class NfcType3Id:
    """
    targets: ['212F' , '106A', '106B']   # default
    targets: ['212F' , '424F']           # Type3に限定？

    """
    CONNECT = 'connect'
    RELEASE = 'release'

    _log = get_logger(__name__, False)

    def __init__(self, cb_connect, cb_release, loop=False, debug=False):
        """
        Parameters
        ----------
        cb_connect: func(id_str)

            Parameters
            ----------
            id_str: str

            Returns
            -------
            ret: bool
                True:  OK
                False: NG

        cb_release: func(id_str)
            same as ``cb_connect``

        loop: bool

        """
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('loop=%s', loop)

        self._cb_connect = cb_connect
        self._cb_release = cb_release
        self._loop = loop

        self._idq = queue.Queue()
        self._targets = ['212F', '424F']
        self._sense_th = threading.Thread(target=self.sense,
                                          args=( self._targets, ),
                                          daemon=True)

        self._active = False

    def start(self):
        self._log.debug('')

        self._active = True
        self._sense_th.start()

        while self._active:
            try:
                event, id_str = self._idq.get(timeout=1.0)
                self._log.debug('event=%s, id_str=%s', event, id_str)

                if event == self.CONNECT:
                    if not self._cb_connect(id_str):
                        self._log.error('Error in %s' % (self._cb_connect))
                        break

                if event == self.RELEASE:
                    if not self._cb_release(id_str):
                        self._log.error('Error in %s' % (self._cb_release))
                        break

                if not self._loop:
                    break

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
        self._log.debug('targets=%s', [str(t) for t in targets])
        return targets

    def connect(self, tag):
        self._log.debug('tag=%s', tag)

        id_str = bytes.hex(tag.identifier)
        self._log.debug('id_str=%s', id_str)

        id_str = self.get_tagidstr(tag)

        self._idq.put((self.CONNECT, id_str))

        return True

    def release(self, tag):
        self._log.debug('tag=%s', tag)

        id_str = self.get_tagidstr(tag)

        self._idq.put((self.RELEASE, id_str))

        return False

    def get_tagidstr(self, tag):
        self._log.debug('tag=%s', tag)
        id_str = bytes.hex(tag.identifier)
        return id_str


class App:
    _log = get_logger(__name__, False)

    def __init__(self, loop, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('loop=%s', loop)

        self._loop = loop

        self._nfc = NfcType3Id(self.cb_connect, self.cb_release,
                               loop=self._loop, debug=self._dbg)

    def main(self):
        self._log.debug('')

        self._nfc.start()

    def end(self):
        self._log.debug('')
        self._nfc.end()
        self._log.debug('done')

    def cb_connect(self, id_str):
        print('*CONNECT: %s' % (id_str))
        return True

    def cb_release(self, id_str):
        print('*RELEASE: %s' % (id_str))
        return True


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--loop', '-l', 'loop', is_flag=True, default=False,
              help='loop flag')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(loop, debug):
    _log = get_logger(__name__, debug)
    _log.debug('loop=%s', loop)

    app = App(loop, debug=debug)
    try:
        app.main()
    finally:
        _log.debug('finally')
        app.end()
        _log.debug('done')


if __name__ == '__main__':
    main()
