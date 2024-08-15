# -*- coding: UTF-8 -*-
# Contains global variables
# Copyright (c) 2023-2024 ZianTT, FriendshipEnder

import sys
import os
import json

import noneprompt

import sentry_sdk
from loguru import logger
from sentry_sdk.integrations.loguru import LoggingLevels, LoguruIntegration

from login import *

from utility import utility

from utils import save, load

import time
from i18n import *

ver_int = 201
version = "v{}.{}.{}".format(
    (ver_int // 10000) % 100, (ver_int // 100) % 100, ver_int % 100
)


def agree_terms():
    logger.info(i18n_format("eula"))
    try:
        _ = noneprompt.InputPrompt(
            question="Please input",
            validator=lambda x: (
                all(keyword in x for keyword in ["同意", "死妈", "黄牛"])
                and "不" not in x
            ),
        ).prompt()
    except noneprompt.CancelledError as e:
        raise KeyboardInterrupt("Cancelled by user.") from e
    with open("agree-terms", "w") as f:
        import machineid

        f.write(machineid.id())
    logger.info(i18n_format("agree_eula"))


def init(version):
    logger.remove(handler_id=0)
    if not os.path.exists("logs"):
        os.mkdir("logs")
    if sys.argv[0].endswith(".py"):
        debug = True
        level = "DEBUG"
        format = "DEBUG MODE | <green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        environment = "development"
        print("WARNING: YOU ARE IN DEBUG MODE")
    else:
        debug = False
        level = "INFO"
        format = "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        environment = "production"
    handler_id = logger.add(
        sys.stderr,
        format=format,
        level=level,
        backtrace=debug,
        diagnose=debug,
    )
    logger.add(
        "./logs/{time:YYYYMMDD-HHmmss}.log",
        format=format,
        level="DEBUG",
        backtrace=True,
        diagnose=True,
        colorize=False,
        encoding="utf-8",
    )
    if not os.path.exists("agree-terms"):
        agree_terms()
    else:
        with open("agree-terms", "r") as f:
            hwid = f.read()
            import machineid

            if hwid != machineid.id():
                agree_terms()
                with open("agree-terms", "w") as f:
                    f.write(machineid.id())

    sentry_sdk.init(
        dsn="https://9c5cab8462254a2e1e6ea76ffb8a5e3d@sentry-inc.bitf1a5h.eu.org/4",
        release=version,
        profiles_sample_rate=1.0,
        enable_tracing=True,
        integrations=[
            LoguruIntegration(
                level=LoggingLevels.DEBUG.value,
                event_level=LoggingLevels.CRITICAL.value,
            ),
        ],
        sample_rate=1.0,
        environment=environment,
    )
    with sentry_sdk.configure_scope() as scope:
        scope.add_attachment(path="data")

    import machineid

    sentry_sdk.set_user({"hwid": machineid.id()[:16], "ip_address": "{{auto}}"})
    try:
        os_username = os.getlogin()
        sentry_sdk.set_tag("os_username", os_username)
    except Exception:
        pass
    return sentry_sdk


class HygException(Exception):
    pass


def load_config():
    go_utility = False
    if os.path.exists("config.json"):
        logger.info(i18n_format("welcome_new_version"))
        if os.path.isdir("data"):
            import shutil

            shutil.rmtree("data")
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            save(config)
        os.remove("config.json")
        logger.info(i18n_format("new_version_ok"))
    if os.path.exists("share.json"):
        logger.info(i18n_format("check_share"))
        with open("share.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            save(config)
        os.remove("share.json")
    if os.path.isdir("data"):
        import shutil

        shutil.rmtree("data")
    if os.path.exists("data"):
        use_login = True
        try:
            run_info = (
                noneprompt.ListPrompt(
                    i18n_format("select_setting"),
                    choices=[
                        noneprompt.Choice(
                            i18n_format("select_keep_all"), data="select_keep_all"
                        ),
                        noneprompt.Choice(
                            i18n_format("select_keep_login"), data="select_keep_login"
                        ),
                        noneprompt.Choice(
                            i18n_format("select_new_boot"), data="select_new_boot"
                        ),
                        noneprompt.Choice(
                            i18n_format("select_tools"), data="select_tools"
                        ),
                        noneprompt.Choice(
                            i18n_format("select_tools_relogin"),
                            data="select_tools_relogin",
                        ),
                        noneprompt.Choice(
                            i18n_format("select_reset"), data="select_reset"
                        ),
                        noneprompt.Choice(
                            "语言设置/Language setting",
                            data="语言设置/Language setting",
                        ),
                    ],
                    default_select=1,
                )
                .prompt(
                    default=noneprompt.Choice(
                        i18n_format("select_keep_all"), data="select_keep_all"
                    )
                )
                .data
            )
        except noneprompt.CancelledError as e:
            raise KeyboardInterrupt("Cancelled by user.") from e

        if run_info == "select_new_boot":
            logger.info(i18n_format("select_new_boot_msg"))
            temp = load()
            config = {}
            if "pushplus" in temp:
                config["pushplus"] = temp["pushplus"]
            if "webhook" in temp:
                config["webhook"] = temp["webhook"]
            if "ua" in temp:
                config["ua"] = temp["pushplus"]
            if "captcha" in temp:
                config["captcha"] = temp["captcha"]
            if "rrocr" in temp:
                config["rrocr"] = temp["rrocr"]
            if "time_offset" in temp:
                config["time_offset"] = temp["time_offset"]
            if "proxy" in temp:
                config["proxy"] = temp["proxy"]
                if "proxy_auth" in temp:
                    config["proxy_auth"] = temp["proxy_auth"]
                if "proxy_channel" in temp:
                    config["proxy_channel"] = temp["proxy_channel"]
            use_login = False
        elif run_info == "select_keep_login":
            logger.info(i18n_format("select_keep_login_msg"))
            temp = load()
            config = {}
            if "gaia_vtoken" in temp:
                config["gaia_vtoken"] = temp["gaia_vtoken"]
            if "ua" in temp:
                config["ua"] = temp["ua"]
            if "cookie" in temp:
                config["cookie"] = temp["cookie"]
            if "role" in temp:
                config["role"] = temp["role"]
            if "pushplus" in temp:
                config["pushplus"] = temp["pushplus"]
            if "webhook" in temp:
                config["webhook"] = temp["webhook"]
            if "captcha" in temp:
                config["captcha"] = temp["captcha"]
            if "rrocr" in temp:
                config["rrocr"] = temp["rrocr"]
            if "time_offset" in temp:
                config["time_offset"] = temp["time_offset"]
            if "proxy" in temp:
                config["proxy"] = temp["proxy"]
                if "proxy_auth" in temp:
                    config["proxy_auth"] = temp["proxy_auth"]
                if "proxy_channel" in temp:
                    config["proxy_channel"] = temp["proxy_channel"]
            use_login = True
        elif run_info == "select_keep_all":
            logger.info(i18n_format("select_keep_all_msg"))
            config = load()
            use_login = True
        elif run_info == "select_tools":
            logger.info(i18n_format("select_tools"))
            go_utility = True
            use_login = True
            config = load()
        elif run_info == "select_tools_relogin":
            logger.info(i18n_format("select_tools_relogin"))
            go_utility = True
            use_login = False
            config = {}
        elif run_info == "select_reset":
            try:
                choice = (
                    noneprompt.ListPrompt(
                        i18n_format("select_reset_msg"),
                        choices=[
                            noneprompt.Choice(i18n_format("no"), data=False),
                            noneprompt.Choice(i18n_format("yes"), data=True),
                        ],
                    )
                    .prompt(default=noneprompt.Choice(i18n_format("no"), data=False))
                    .data
                )
            except noneprompt.CancelledError:
                return
            if choice:
                os.remove("language")
                os.remove("data")
                os.remove("agree-terms")
                config = {}
                logger.info(i18n_format("select_reset_ok"))
            else:
                logger.info(i18n_format("select_reset_cancel"))
            return
        elif run_info == "语言设置/Language setting":
            set_language(True)
            config = load()
            go_utility = True
            use_login = True
    else:
        save({})
        config = {}
        use_login = False
    if "cover_time_offset" in config:
        logger.info(i18n_format("cover_time_offset"))
        logger.info(i18n_format("time_offset").format(config["time_offset"]))
    else:
        logger.info(i18n_format("auto_time_offset"))
        import ntplib

        c = ntplib.NTPClient()
        ntp_servers = (
            "ntp.ntsc.ac.cn",  # //Zhejiang ping: 27.75 ms
            "time.pool.aliyun.com",  # //Zhejiang ping:  32.5 ms
            "time1.cloud.tencent.com",  # //Zhejiang ping:    35 ms
            "asia.pool.ntp.org",  # //Zhejiang ping:    37 ms
            "edu.ntp.org.cn",  # //Zhejiang ping:    41 ms
            "cn.ntp.org.cn",  # //Zhejiang ping:    41 ms | ipv6 | 有时候抽风
            "cn.pool.ntp.org",  # //Zhejiang ping:    50 ms | 有时候抽风
            "ntp.tuna.tsinghua.edu.cn",  # //Zhejiang ping:    55 ms | ipv6
            "time.asia.apple.com",  # //Zhejiang ping: 78.75 ms
            "time.windows.com",  # //Zhejiang ping:    89 ms
        )
        skip = 0
        for i in range(10):
            try:
                response = c.request(ntp_servers[i], timeout=1)
            except Exception:
                skip += 1
            else:
                break
        if skip >= 10:
            logger.error(i18n_format("time_sync_fail"))
            config["time_offset"] = -0.5
        else:
            time_offset = response.offset - 0.5
            logger.info(i18n_format("time_offset").format(time_offset))
            config["time_offset"] = time_offset
    while True:
        if "cookie" not in config or not use_login:
            config["cookie"] = interactive_login(sentry_sdk)
        import random

        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/618.1.15.10.15 (KHTML, like Gecko)",
            "Cookie": config["cookie"],
        }
        session = requests.session()
        def cookie(cookies):
            # lst = []
            # for item in cookies.items():
            #     lst.append(f"{item[0]}={item[1]}")

            # cookie_str = ";".join(lst)
            # return cookie_str
            lst = {}
            cookies = cookies.split(";")
            for item in cookies:
                lst[item.split("=")[0]] = item.split("=")[1]
            return lst
        requests.utils.add_dict_to_cookiejar(session.cookies, cookie(config["cookie"]))
        available = session.post(
            "https://passport-api.mihoyo.com/account/ma-cn-session/web/verifyCookieToken", headers=headers
        ).json()
        logger.debug(available)
        user = session.get(
            "https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookieToken?game_biz=hk4e_cn", headers=headers
        )
        user = user.json()
        if user["retcode"] == 0 and available["retcode"] == 0:
            if "role" not in config:
                config["role"] = noneprompt.ListPrompt(
                    i18n_format("select_game_role"),
                    choices = [noneprompt.Choice("{} {} Level {} UID:{}".format(x["region_name"], x["nickname"], x["level"], x["game_uid"]),data = x) for x in user["data"]["list"]],
                ).prompt().data
            url = "https://api-takumi.mihoyo.com/common/badge/v1/login/account"
            login_info = session.post(
                url, headers=headers,
                json={
                    "game_biz": "hk4e_cn",
                    "region": config["role"]["region"],
                    "lang": "zh-cn",
                    "uid": config["role"]["game_uid"],
                }
                ).json()
            logger.debug(login_info)
            if login_info["retcode"] != 0:
                config["role"] = noneprompt.ListPrompt(
                    i18n_format("select_game_role"),
                    choices = [noneprompt.Choice("{} {} Level {} UID:{}".format(x["region_name"], x["nickname"], x["level"], x["game_uid"]),data = x) for x in user["data"]["list"]],
                ).prompt().data
                url = "https://api-takumi.mihoyo.com/common/badge/v1/login/account"
                login_info = session.post(
                    url, headers=headers,
                    json={
                        "game_biz": "hk4e_cn",
                        "region": config["role"]["region"],
                        "lang": "zh-cn",
                        "uid": config["role"]["game_uid"],
                    }
                    ).json()
                logger.debug(login_info)
                if login_info["retcode"] != 0:
                    logger.error(i18n_format("login_failure"))
                    use_login = False
                    config.pop("cookie")
                    save(config)
                    continue
            logger.info(i18n_format("login_success").format(login_info["data"]["nickname"],login_info["data"]["game_uid"],"UNK"))
            import machineid

            sentry_sdk.set_user(
                {
                    "username": config["role"]["game_uid"],
                    "hwid": machineid.id()[:16],
                    "ip_address": "{{auto}}",
                }
            )
            config["uid"] = config["role"]["game_uid"]
            def extract_cookie(cookies):
                lst = []
                for item in cookies.items():
                    lst.append(f"{item[0]}={item[1]}")

                cookie_str = ";".join(lst)
                return cookie_str
            config["cookie"] = extract_cookie(session.cookies)
            logger.debug(extract_cookie(session.cookies))
            if "hunter" in config:
                logger.success(i18n_format("hunter_mode"))
                logger.info(i18n_format("hunter_grade").format(config["hunter"]))
            save(config)
            break
        else:
            logger.error(i18n_format("login_failure"))
            use_login = False
            config.pop("cookie")
            save(config)
    if go_utility:
        utility(config)
        return load_config()
    return config
