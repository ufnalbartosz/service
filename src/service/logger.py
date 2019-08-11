import logging
import sys

applog = logging.getLogger()
applog.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
applog.addHandler(handler)