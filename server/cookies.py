import base64
import os
import logging
from flask import request

logger = logging.getLogger(__name__)

KEY_USERID = 'cmu.table.arxiv.userid'

def setUserId():
    if KEY_USERID not in request.cookies:
        userid = base64.b64encode(os.urandom(16))
        logger.info("New user from ip {0} with id {1} created.".format(request.remote_addr, userid))
    else:
        userid = request.cookies.get(KEY_USERID)
        logger.info("User from ip {0}  with id {1} logged in.".format(request.remote_addr, userid))
    return userid
