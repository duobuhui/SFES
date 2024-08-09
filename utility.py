# Copyright (c) 2023-2024 ZianTT, FriendshipEnder
from logging import log
from os import pathsep
import requests

import noneprompt

import sentry_sdk
import pyperclip

from utils import save, check_policy

from i18n import *

from globals import *


def utility(config):
    import base64

    def add_buyer(config):
        fetch_url = f"https://hk4e-api.mihoyo.com/event/tickethub/query_user_info?badge_uid={config['role']['game_uid']}&badge_region={config['role']['region']}&lang=zh-cn&game_biz=hk4e_cn"
        origin = session.get(fetch_url, headers=headers).json()["data"]["user"]
        url=f"https://hk4e-api.mihoyo.com/event/tickethub/update_user_info?badge_uid={config['role']['game_uid']}&badge_region={config['role']['region']}&lang=zh-cn&game_biz=hk4e_cn"
        data = {
            "user": {
                "id_card_no": noneprompt.InputPrompt(
                    question=i18n_format("input_id_card_no")
                ).prompt(),
                "name": noneprompt.InputPrompt(
                    question=i18n_format("input_real_name")
                ).prompt(),
                "phone_number": noneprompt.InputPrompt(
                    question=i18n_format("input_phone")
                ).prompt(),
                "phone_code": "+86",
                "phone_verify_code": "",
                "uid": noneprompt.InputPrompt(
                    question=i18n_format("input_uid")
                ).prompt(),
            }
        }
        if data["user"]["phone_number"] != "":
            verify_url = f"https://hk4e-api.mihoyo.com/event/tickethub/send_phone_code?badge_uid={config['role']['game_uid']}&badge_region={config['role']['region']}&lang=zh-cn&game_biz=hk4e_cn"
            verify_data = {
                "phone": data["user"]["phone_number"],
                "area_code": "+86",
                "verify_type": 1
            }
            response = session.post(verify_url, headers=headers, json=verify_data).json()
            if response["retcode"] == 0:
                logger.info(i18n_format("send_verify_code"))
                data["user"]["phone_verify_code"] = noneprompt.InputPrompt(
                    question=i18n_format("input_verify_code")
                ).prompt()
            else:
                logger.error(response["message"])
                return add_buyer(config)
        if data["user"]["id_card_no"] == "":
            data["user"]["id_card_no"] = origin["id_card_no"]
        if data["user"]["name"] == "":
            data["user"]["name"] = origin["name"]
        if data["user"]["phone_number"] == "":
            data["user"]["phone_number"] = origin["phone_number"]
        if data["user"]["uid"] == "":
            data["user"]["uid"] = origin["uid"]
        response = session.post(url, headers=headers, json=data).json()
        if response["retcode"] == 0:
            logger.info(i18n_format("add_buyer_success"))
            return
        else:
            logger.error(response["message"])
            return add_buyer(config)

    def bind_ticket(config):
        url = f"https://hk4e-api.mihoyo.com/event/tickethub/get_acts?badge_uid={config["role"]["game_uid"]}&badge_region={config["role"]["region"]}&game_biz=hk4e_cn&page_index=1&page_size=20"
        response = session.get(url, headers=headers).json()
        #logger.debug(response)
        act = noneprompt.ListPrompt(
            question=i18n_format("select_act"),
            choices=[
                noneprompt.Choice(
                    name=f"{x['act_name']}({x['act_id']})", data=x["act_id"]
                )
                for x in response["data"]["infos"]
            ],
        ).prompt().data
        ticket_id = noneprompt.InputPrompt(
            question=i18n_format("input_ticket_id")
        ).prompt()
        url = f"https://hk4e-api.mihoyo.com/event/tickethub/user_bind_ticket?badge_uid={config['role']['game_uid']}&badge_region={config['role']['region']}&lang=zh-cn&game_biz=hk4e_cn"
        data = {
            "ticket_id": ticket_id,
            "act_id": act,
        }
        response = session.post(url, headers=headers, json=data).json()
        if response["retcode"] == 0:
            logger.info(i18n_format("bind_ticket_success"))
            return
        else:
            logger.error(response["message"])
            return bind_ticket(config)
    def modify_ua():
        ua = noneprompt.InputPrompt(question=i18n_format("modify_ua")).prompt()
        config["ua"] = ua

    def hunter_mode():
        config["hunter"] = 0
        logger.info(i18n_format("hunter_mode_on"))

    def hunter_mode_off():
        if "hunter" in config:
            config.pop("hunter")
        logger.info(i18n_format("hunter_mode_off"))

    def share_mode(config):
        import json

        json.dump(config, open("share.json", "w"))
        import os

        os.remove("data")
        logger.info(i18n_format("share_mode"))
        logger.info(i18n_format("auto_quit"))
        import sys

        sys.exit(0)
        return

    def pushplus_config(config):
        try:
            try:
                clip_value = pyperclip.paste()
                logger.info(i18n_format("clip_paste_success"))
            except pyperclip.PyperclipException:
                clip_value = ""
            token = noneprompt.InputPrompt(
                question=i18n_format("pushplus_token"),
                default_text=clip_value,
            ).prompt()
        except noneprompt.CancelledError:
            logger.info(i18n_format("cancelled"))
            return
        if token == "":
            if "pushplus" in config:
                config.pop("pushplus")
            logger.info(i18n_format("pushplus_off"))
            save(config)
            return
        config["pushplus"] = token
        logger.info(i18n_format("pushplus_on"))
        save(config)

    def webhook_config(config):
        try:
            try:
                clip_value = pyperclip.paste()
                logger.info(i18n_format("clip_paste_success"))
            except pyperclip.PyperclipException:
                clip_value = ""
            webhook = noneprompt.InputPrompt(
                question=i18n_format("webhook"), default_text=clip_value
            ).prompt()
        except noneprompt.CancelledError:
            logger.info(i18n_format("cancelled"))
            return
        if webhook == "":
            if "webhook" in config:
                config.pop("webhook")
            logger.info(i18n_format("webhook_off"))
            save(config)
            return
        config["webhook"] = webhook
        logger.info(i18n_format("webhook_on"))
        save(config)

    def set_offset(config):
        try:
            offset = noneprompt.InputPrompt(
                question=i18n_format("input_offset")
            ).prompt()
        except noneprompt.CancelledError:
            logger.info(i18n_format("cancelled"))
            return
        if offset == "":
            if "time_offset" in config:
                config.pop("time_offset")
            if "cover_time_offset" in config:
                config.pop("cover_time_offset")
            logger.info(i18n_format("offset_off"))
            save(config)
        else:
            config["time_offset"] = float(offset)
            config["cover_time_offset"] = True
            logger.info(i18n_format("save_offset"))
            save(config)

    def use_proxy(config):
        try:
            confirm_proxy = noneprompt.ConfirmPrompt(
                question=i18n_format("input_is_use_proxy"),
                default_choice=False,
            ).prompt()
        except noneprompt.CancelledError:
            logger.info(i18n_format("cancelled"))
            return
        if confirm_proxy:
            while True:
                try:
                    try:
                        try:
                            clip_value = pyperclip.paste()
                            logger.info(i18n_format("clip_paste_success"))
                        except pyperclip.PyperclipException:
                            clip_value = ""
                        config["proxy_auth"] = (
                            noneprompt.InputPrompt(
                                question=i18n_format("input_proxy"),
                                default_text=clip_value,
                            )
                            .prompt()
                            .split(" ")
                        )
                    except noneprompt.CancelledError:
                        logger.info(i18n_format("cancelled"))
                        return
                    assert len(config["proxy_auth"]) == 3
                    break
                except:
                    logger.error(i18n_format("wrong_proxy_format"))
                    continue
            try:
                config["proxy_channel"] = noneprompt.InputPrompt(
                    question=i18n_format("input_proxy_channel"),
                    validator=lambda x: x.isdigit(),
                ).prompt()
            except noneprompt.CancelledError:
                logger.info(i18n_format("cancelled"))
                return
            config["proxy"] = True
        else:
            config["proxy"] = False
        save(config)

    def captcha_mode(config):
        try:
            cap_pass = (
                noneprompt.ListPrompt(
                    question=i18n_format("input_use_captcha_mode"),
                    choices=[
                        noneprompt.Choice(name=i18n_format(x), data=x)
                        for x in ["local_gt", "rrocr", "manual"]
                    ],
                )
                .prompt()
                .data
            )
        except noneprompt.CancelledError as e:
            logger.info(i18n_format("cancelled"))
            return
        if cap_pass == "local_gt":
            config["captcha"] = "local_gt"
            sentry_sdk.set_tag("captcha", "local_gt")
        elif cap_pass == "rrocr":
            config["captcha"] = "rrocr"
            while True:
                try:
                    config["rrocr"] = noneprompt.InputPrompt(
                        question=i18n_format("input_rrocr_key")
                    ).prompt()
                except noneprompt.CancelledError:
                    logger.info(i18n_format("cancelled"))
                    return
                if config["rrocr"] != "":
                    break
            sentry_sdk.set_tag("captcha", "rrocr")
        elif cap_pass == "manual":
            config["captcha"] = "manual"
            sentry_sdk.set_tag("captcha", "manual")
        else:
            logger.error(i18n_format("captcha_mode_not_supported"))
        save(config)

    import random

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
        "Referer": "https://act.mihoyo.com/ys/event/offline-reserve/index.html",
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
    select = (
        noneprompt.ListPrompt(
            question=i18n_format("select_tool"),
            choices=[
                noneprompt.Choice(i18n_format(x), data=x)
                for x in ["tool_add_buyer", "tool_bind_ticket", "tool_modify_ua", "tool_hunter_mode", "tool_hunter_off", "tool_share_mode", "tool_pushplus", "tool_proxy_setting", "tool_capacha_mode", "tool_webhook", "tool_set_offset", "tool_hide_module", "back",]],
        )
        .prompt()
        .data
    )
    if select == "tool_add_buyer":
        add_buyer(config)
        return utility(config)
    elif select == "tool_bind_ticket":
        bind_ticket(config)
        return utility(config)
    elif select == "tool_modify_ua":
        modify_ua()
        return utility(config)
    elif select == "tool_hunter_mode":
        hunter_mode()
        return utility(config)
    elif select == "tool_hunter_off":
        hunter_mode_off()
        return utility(config)
    elif select == "tool_share_mode":
        share_mode(config)
        return utility(config)
    elif select == "tool_pushplus":
        pushplus_config(config)
        return utility(config)
    elif select == "tool_proxy_setting":
        use_proxy(config)
        return utility(config)
    elif select == "tool_capacha_mode":
        captcha_mode(config)
        return utility(config)
    elif select == "tool_webhook":
        webhook_config(config)
        return utility(config)
    elif select =="tool_set_offset":
        set_offset(config)
        return utility(config)
    elif select == "back":
        return
    elif select == "tool_hide_module":
        try:
            name = noneprompt.InputPrompt(
                i18n_format("input_hide_tool"),
                validator=lambda x: x != "" and x.isidentifier(),
            ).prompt(default="")
        except noneprompt.CancelledError:
            logger.info(i18n_format("cancelled"))
            return
        logger.error(i18n_format("tool_not_supported"))
        return utility(config)
