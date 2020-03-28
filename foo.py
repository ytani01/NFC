#!/usr/bin/env python3
#

import nfc
import binascii

from MyLogger import get_logger


class App:
    def __init__(self, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('')

        self.clf = nfc.ContactlessFrontend('usb')
        self._log.debug('clf=%s', self.clf)

    def main(self):
        self._log.debug('')
        if self.clf:
            while self.clf.connect(rdwr={
                    """
                    'targets': ['212F' , '424F'],  # Type4を排除(?)
                    """
                    'on-startup': self.startup,
                    'on-connect': self.connect,
                    'on-release': self.release,
            }):
                pass

    def end(self):
        self._log.debug('')

    def startup(self, targets):
        self._log.debug('targets=%s', targets)

        for t in targets:
            self._log.debug('t=%s', t)
            
        return targets

    def connect(self, tag):
        self._log.debug('tag=%s', tag)

        self._log.info('type=%s', tag.type)
        self._log.info('identifier=%s', binascii.hexlify(tag.identifier))

        try:
            sys_codes = tag.request_system_code()
            self._log.debug('sys_codes=%s', sys_codes)
        except Exception as e:
            msg = '%s:%s' % (type(e).__name__, e)
            self._log.warning(msg)

            """
        n = 32
        for i in range(0, 0x10000, n):
            self.check_services(tag, i , n)
        """

        return True

    def release(self, tag):
        self._log.debug('tag=%s', tag)

    def check_system(tag, system_code):
        idm, pmm = tag.polling(system_code=system_code)
        tag.idm, tag.pmm, tag.sys = idm, pmm, system_code
        print(tag)
        n = 32
        for i in xrange(0, 0x10000, n):
            check_services(tag, i, n)

    def check_services(self, tag, start, n):
        services = [nfc.tag.tt3.ServiceCode(i >> 6, i & 0x3f)
                    for i in range(start, start + n)]
        versions = tag.request_service(services)

        for i in range(n):
            if versions[i] == 0xffff:
                continue
            print(services[i], versions[i])


import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
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
