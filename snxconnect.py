#!/usr/bin/python

import os
import sys
import urllib2
from rsclib.HTML_Parse import Page_Tree
from cookielib         import CookieJar
from bs4               import BeautifulSoup
from getpass           import getpass
from urllib            import urlencode
from argparse          import ArgumentParser
from netrc             import netrc
from Crypto.PublicKey  import RSA

class HTML_Requester (object) :

    def __init__ (self, args) :
        self.args     = args
        self.jar      = j = CookieJar ()
        self.opener   = urllib2.build_opener (urllib2.HTTPCookieProcessor (j))
        self.nextfile = args.file
    # end def __init__

    def open (self, filepart = None, data = None) :
        filepart = filepart or self.nextfile
        url = '/'.join (('https:/', self.args.host, self.args.file))
        rq = urllib2.Request (url, data)
        f  = self.opener.open (rq, timeout = 10)
        self.soup = BeautifulSoup (f)
        #purl  = f.geturl ()
        #pinfo = f.info ()
    # end def open

    def login (self) :
        self.open ()
        forms = self.soup.find_all ('form')
        for form in forms :
            if 'id' in form.attrs and form ['id'] == 'loginForm' :
                self.nextfile = form ['action']
                assert form ['method'] == 'post'
                break
        print self.nextfile
        # FIXME: We may want to get the RSA parameters from the
        #        javascript in the received html
        enc = PW_Encode ()
        d = dict \
            ( password      = enc.encrypt (self.args.password)
            , userName      = self.args.username
            , selectedRealm = self.args.realm
            , loginType     = self.args.login_type
            , vpid_prefix   = self.args.vpid_prefix
            , HeightData    = self.args.height_data
            )
        self.open (data = urlencode (d))
        print self.soup.prettify ()
    # end def login

# end class HTML_Requester

def main () :
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( '-F', '--file'
        , help    = 'File part of URL default=%(default)s'
        , default = 'sslvpn'
        )
    cmd.add_argument \
        ( '-H', '--host'
        , help    = 'Host part of URL default=%(default)s'
        , default = 'snx.lfrz.at'
        )
    cmd.add_argument \
        ( '--height-data'
        , help    = 'Height data in form, default empty'
        , default = ''
        )
    cmd.add_argument \
        ( '-L', '--login-type'
        , help    = 'Login type, default=%(default)s'
        , default = 'Standard'
        )
    cmd.add_argument \
        ( '-p', '--password'
        , help    = 'Login password, not a good idea to specify on commandline'
        )
    cmd.add_argument \
        ( '-R', '--realm'
        , help    = 'Selected realm, default=%(default)s'
        , default = 'ssl_vpn'
        )
    cmd.add_argument \
        ( '-U', '--username'
        , help    = 'Login username'
        )
    cmd.add_argument \
        ( '-V', '--vpid-prefix'
        , help    = 'VPID prefix, default empty'
        , default = ''
        )
    args = cmd.parse_args ()
    if not args.username or not args.password :
        n = netrc ()
        a = n.authenticators (args.host)
        if a :
            un, dummy, pw = a
            if not args.username :
                args.username = un
            if not args.password :
                args.password = pw
        if 'password' not in args :
            password = getpass ('Password: ')
    rq = HTML_Requester (args)
    rq.login ()
# end def main ()

class PW_Encode (object) :
    """ RSA encryption module with special padding and reversing to be
        compatible with checkpoints implementation.
        Test with non-random padding to get known value:
        >>> p = PW_Encode (testing = True)
        >>> print p.encrypt ('xyzzy')
        451c2d5b491ee22d6f7cdc5a20f320914668f8e01337625dfb7e0917b16750cfbafe38bfcb68824b30d5cc558fa1c6d542ff12ac8e1085b7a9040f624ab39f625cabd77d1d024c111e42fede782e089400d2c9b1d6987c0005698178222e8500243f12762bebba841eae331d17b290f80bca6c3f8a49522fb926646c24db3627
    """

    def __init__ (self, m = None, e = None, testing = False) :
        modulus = long \
            ( 'c87e9e96ffde3ec47c3f116ea5ac0e15'
              '34490b3da6dbbedae1af50dc32bf1012'
              'bdb7e1ff67237e0302b48c8731f343ff'
              '644662de2bb21d2b033127660e525d58'
              '889f8f6f05744906dddc8f4b85e0916b'
              '5d9cf5b87093ed260238674f143801b7'
              'e58a18795adc9acefaf0f378326fea19'
              '9ac6e5a88be83a52d4a77b3bba5f1aed'
            , 16
            )
        exponent = long ('010001', 16)
        m = m or modulus
        e = e or exponent
        self.pubkey  = RSA.construct ((m, e))
        self.testing = testing
    # end def __init__

    def pad (self, txt) :
        l = (self.pubkey.size () + 7) >> 3
        r = []
        r.append ('\0')
        for x in reversed (txt) :
            r.append (x)
        r.append ('\0')
        n = l - len (r) - 2
        if self.testing :
            r.append ('\1' * n)
        else :
            r.append (os.urandom (n))
        r.append ('\x02')
        r.append ('\x00')
        return ''.join (reversed (r))
    # end def pad

    def encrypt (self, password) :
        x = self.pad (password)
        e = self.pubkey.encrypt (x, '')[0]
        e = ''.join ('%02x' % ord (c) for c in reversed (e))
        return e
    # end def encrypt

# end class PW_Encode

if __name__ == '__main__' :
    main ()