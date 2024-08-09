# -*- coding: UTF-8 -*-
# Copyright (c) 2023-2024 ZianTT, FriendshipEnder
import json
import os
import threading
import time

import kdl

import noneprompt

import requests
from loguru import logger

from api import BilibiliHyg
from globals import *

from utils import save, load, check_policy

import noneprompt

from i18n import *

common_project_id = [
    {"name": "上海·BilibiliWorld 2024", "id": 85939},
    {"name": "上海·BILIBILI MACRO LINK 2024", "id": 85938},
]


def run(hyg):
    if hyg.config["mode"] == "direct" or hyg.config["mode"] == "time":
        while True:
            if hyg.try_create_order():
                if "hunter" not in hyg.config:
                    hyg.sdk.capture_message("Pay success!")
                    logger.success(i18n_format("pay_success"))
                    return
                else:
                    hyg.config["hunter"] += 1
                    save(hyg.config)
                    logger.success(
                        i18n_format("hunter_prompt").format(hyg.config["hunter"])
                    )
    elif hyg.config["mode"] == "detect":
        token_time = time.time()
        while 1:
            if time.time() - token_time > 300:
                token_time = time.time()
                try:
                    hyg.get_token()
                except:
                    continue
            hyg.risk = False
            if hyg.risk:
                remain = -1
            remain = hyg.get_ticket_status()
            if remain > 0:
                logger.info(i18n_format("begin_buy"))
                start_time = time.time()
                hyg.sold_out = False
                while time.time() - start_time < 20 and not hyg.sold_out:
                    if hyg.try_create_order():
                        if "hunter" not in hyg.config:
                            hyg.sdk.capture_message("Pay success!")
                            logger.success(i18n_format("pay_success"))
                            return
                        else:
                            hyg.config["hunter"] += 1
                            save(hyg.config)
                            logger.success(
                                i18n_format("hunter_prompt").format(
                                    hyg.config["hunter"]
                                )
                            )
                        break

            elif remain == -1:
                continue
            else:
                logger.error(i18n_format("unk_status") + str(remain))
            time.sleep(hyg.config["status_delay"])


def main():
    #    easter_egg = False
    #    user_male = False
    #    user_female = False
    from globals import version

    set_language(False)
    print(i18n_format("start_up").format(version))
    global kdl_client
    kdl_client = None
    try:
        sentry_sdk = init(version)
        session = requests.session()

        check_key = check_policy()
        logger.info(i18n_format("tips"))
        config = load_config()
        if config == None:
            return
        if check_key:
            check_policy(uid=config["uid"])
        if "super" in config:
            check_policy(uid=config["uid"], res="super")
        import random

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
        }
        if "user-agent" in config:
            headers["User-Agent"] = config["user-agent"]
        session = requests.Session()
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
        logger.debug(session.cookies)
        if "mode" not in config:
            try:
                mode_str = (
                    noneprompt.ListPrompt(
                        question=i18n_format("choose_mode"),
                        choices=[
                            noneprompt.Choice(name=i18n_format(x), data=x)
                            for x in ["mode_time", "mode_direct", "mode_detect"]
                        ],
                    )
                    .prompt()
                    .data
                )
            except noneprompt.CancelledError as e:
                return
            if mode_str == "mode_direct":
                config["mode"] = "direct"
                logger.info(i18n_format("mode_direct_on"))
            elif mode_str == "mode_detect":
                config["mode"] = "detect"
                logger.info(i18n_format("mode_detect_on"))
            else:
                config["mode"] = "time"
                logger.info(i18n_format("mode_time_on"))
        if "status_delay" not in config and config["mode"] == "detect":
            while True:
                try:
                    config["status_delay"] = noneprompt.InputPrompt(
                        question=i18n_format("input_status_delay")
                    ).prompt(default="0.2")
                except noneprompt.CancelledError:
                    logger.info(i18n_format("cancelled"))
                    return
                if config["status_delay"] == "":
                    config["status_delay"] = 0.2
                try:
                    config["status_delay"] = float(config["status_delay"])
                    if config["status_delay"] < 0:
                        raise ValueError
                    break
                except ValueError:
                    logger.error(i18n_format("wrong_input"))
        if "co_delay" not in config:
            while True:
                config["co_delay"] = noneprompt.InputPrompt(
                    question=i18n_format("input_co_delay"),
                    default_text="0",
                ).prompt(default="0")
                if config["co_delay"] == "":
                    config["co_delay"] = 0
                try:
                    config["co_delay"] = float(config["co_delay"])
                    if config["co_delay"] < 0:
                        raise ValueError
                    break
                except ValueError:
                    logger.error(i18n_format("wrong_input"))
        if "proxy" not in config:
            logger.info(i18n_format("no_proxy_by_default"))
            config["proxy"] = False
        if "captcha" not in config:
            logger.info(i18n_format("captcha_mode_gt_by_default"))
            config["captcha"] = "local_gt"
        if "rrocr" not in config:
            config["rrocr"] = None
        if config["captcha"] == "local_gt":
            logger.info(i18n_format("captcha_mode_gt"))
        elif config["captcha"] == "rrocr":
            logger.info(i18n_format("captcha_mode_rrocr"))
        elif config["captcha"] == "manual":
            logger.info(i18n_format("captcha_mode_manual"))
        else:
            logger.error(i18n_format("captcha_mode_not_supported"))
            return
        if config["proxy"] == True:
            auth = kdl.Auth(config["proxy_auth"][0], config["proxy_auth"][1])
            kdl_client = kdl.Client(auth)
            session.proxies = {
                "http": config["proxy_auth"][2],
                "https": config["proxy_auth"][2],
            }
            if config["proxy_channel"] != "0":
                headers["kdl-tps-channel"] = config["proxy_channel"]
            session.keep_alive = False
            logger.info(
                i18n_format("test_proxy").format(
                    kdl_client.tps_current_ip(sign_type="hmacsha1")
                )
            )
        if (
            "role" not in config
            or "game_uid" not in config["role"]
            or "region" not in config["role"]
            or "act_id" not in config
            or "time" not in config
            or "bind_ticket_id" not in config
            or "schedule_id" not in config
        ):
            url = f'https://hk4e-api.mihoyo.com/event/tickethub/get_acts?badge_uid={config["role"]["game_uid"]}&badge_region={config["role"]["region"]}&game_biz=hk4e_cn&page_index=1&page_size=20'
            acts = session.get(url, headers=headers).json()
            if acts["data"]["is_login"] == False:
                logger.error(i18n_format("login_failed"))
                return
            act = noneprompt.ListPrompt(
                i18n_format("select_act"),
                choices=[
                    noneprompt.Choice(
                        f"{i['act_name']}",
                        data=i,
                    )
                    for i in acts["data"]["infos"]
                ],
            ).prompt()
            config["act_id"] = act.data["act_id"]
            url = f'https://hk4e-api.mihoyo.com/event/tickethub/get_act_detail?badge_uid={config["role"]["game_uid"]}&badge_region={config["role"]["region"]}&lang=zh-cn&game_biz=hk4e_cn&act_id={config["act_id"]}'
            act_detail = session.get(url, headers=headers).json()["data"]
            config["time"] = act_detail["book_start_timestamp"]
            schedules = act_detail["data_schedules"]
            schedule = noneprompt.ListPrompt(
                i18n_format("select_schedule"),
                choices=[
                    noneprompt.Choice(
                        f"{i['date']}",
                        data=i,
                    )
                    for i in schedules
                ],
            ).prompt().data
            if schedule["bind_ticket_id"] == "":
                logger.error(i18n_format("no_ticket_binded"))
                return
            sub_act = noneprompt.ListPrompt(
                i18n_format("select_sub_act"),
                choices=[
                    noneprompt.Choice(
                        f"{i['name']}",
                        data=i,
                    )
                    for i in schedule["sub_acts"]
                ],
            ).prompt().data["scheduleInfos"][0]
            config["bind_ticket_id"] = schedule["bind_ticket_id"]
            config["schedule_id"] = sub_act["schedule_id"]
        save(config)
        sentry_sdk.set_context("config", config)
        sentry_sdk.capture_message("config complete")
        BHYG = BilibiliHyg(config, sentry_sdk, kdl_client, session)
        BHYG.waited = True
        run(BHYG)
    except KeyboardInterrupt:
        logger.info(i18n_format("exit_manual"))
        return
    except Exception as e:
        track = sentry_sdk.capture_exception(e)
        logger.error(i18n_format("error_occured").format(str(e), str(track)))
        return
    return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info(i18n_format("exit_manual"))
    from sentry_sdk import Hub

    client = Hub.current.client
    if client is not None:
        client.close(timeout=2.0)
    logger.info(i18n_format("exit_sleep_15s"))
    try:
        time.sleep(15)
    except KeyboardInterrupt:
        pass
