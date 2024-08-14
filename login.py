# Copyright (c) 2023-2024 ZianTT, FriendshipEnder
import base64
import json
import re
import time

import qrcode
import requests
from loguru import logger

import noneprompt

from i18n import *
from globals import *


def cookie(cookies):
    lst = []
    for item in cookies.items():
        lst.append(f"{item[0]}={item[1]}")

    cookie_str = ";".join(lst)
    return cookie_str

def qr_login(session, headers):
    headers["x-rpc-app_id"]="cie2gjc0sg00"
    import uuid
    headers["x-rpc-device_id"]=uuid.uuid4().hex
    generate = session.post(
        "https://passport-api.mihoyo.com/account/ma-cn-passport/web/createQRLogin",
        headers=headers,
        json={}
    )
    generate = generate.json()
    if generate["retcode"] == 0:
        url = generate["data"]["url"]
    else:
        logger.error(generate)
        return
    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii(invert=True)
    img = qr.make_image()
    img.show()
    logger.info(i18n_format("qr_login"))
    while True:
        time.sleep(1)
        url = "https://passport-api.mihoyo.com/account/ma-cn-passport/web/queryQRLoginStatus"
        req = session.post(url, headers=headers,json={"ticket":generate["data"]["ticket"]})
        # read as utf-8
        check = req.json()
        if check["retcode"] == 0:
            if check["data"]["status"] == "Confirmed":
                logger.debug(check)
                username = check["data"]["user_info"]["mobile"] if check["data"]["user_info"]["mobile"] else check["data"]["user_info"]["email"]
                logger.success(i18n_format("login_success").format(username, "UNK", check["data"]["user_info"]["aid"]))
                cookies = requests.utils.dict_from_cookiejar(session.cookies)
                break
            else:
                pass
        elif check["retcode"] == -3501:
            logger.info(check["message"])
        elif check["retcode"] == -3505:
            logger.error(check["message"])
            return qr_login(session, headers)
        else:
            logger.error(check)
            return qr_login(session, headers)
    return cookie(cookies)


def _verify(gt, challenge, token):
    global sdk
    #from geetest import run

    time_start = time.time()
    data = run(gt, challenge, token, "local_gt")
    delta = time.time() - time_start
    sdk.metrics.distribution(
        key="gt_solve_time", value=delta * 1000, unit="millisecond"
    )
    return data

def interactive_login(sentry_sdk=None):
    # from globals import i18n_lang
    global sdk
    sdk = sentry_sdk
    import random

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    }

    session = requests.session()

    try:
        try:
            method = (
                noneprompt.ListPrompt(
                    question=i18n_format("bi_login_method"),
                    choices=[
                        noneprompt.Choice(name=i18n_format(x), data=x)
                        for x in [
                            "login_qr",
                            "bi_login_cookie",
                        ]
                    ],
                    default_select=1,
                )
                .prompt()
                .data
            )
        except noneprompt.CancelledError as e:
            return
        if method == "bi_login_cookie":
            try:
                cookie_str = input(i18n_format("bi_input_cookie"))
            except noneprompt.CancelledError:
                logger.error(i18n_format("cancelled"))
                return
            # verify cookie
            try:
                session.get(
                    "https://ys.mihoyo.com/",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
                        "Cookie": cookie_str,
                    },
                )
            except Exception:
                logger.error(i18n_format("bi_illegal_cookie"))
                return interactive_login()
            cookies = cookie_str.split(";")
            new_cookie = []
            for cookie in cookies:
                if "e_hk4e_token" not in cookie:
                    new_cookie.append(cookie)
            cookie_str = ";".join(new_cookie)
        elif method == "login_qr":
            cookie_str = qr_login(session, headers)
        else:
            logger.error(i18n_format("login_not_supported"))
            return interactive_login()
    except Exception as e:
        logger.error(i18n_format("login_failed"))
        logger.debug(e)
        return interactive_login()

    logger.debug("=" * 20)
    logger.debug(cookie_str)
    logger.debug("=" * 20)
    return cookie_str
