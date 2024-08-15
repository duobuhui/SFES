import json
import random
import time
import urllib.parse
import hashlib
import hmac

import qrcode
import requests
from loguru import logger

from i18n import *

from utils import save, load
from globals import *


class BilibiliHyg:
    global sdk

    def __init__(self, config, sdk, client, session):
        self.waited = False
        self.sdk = sdk
        self.config = config
        self.config["gaia_vtoken"] = None
        self.session = requests.Session()
        if "user-agent" in self.config:
            self.headers = {
                "User-Agent": self.config["user-agent"],
            }
        else:
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
            }

        if self.config["proxy"]:
            if self.config["proxy_channel"] != "0":
                self.headers["kdl-tps-channel"] = config["proxy_channel"]

        self.client = client
        self.session = session
        if self.client != None:
            self.ip = self.client.tps_current_ip(sign_type="hmacsha1")
        if self.config["mode"] == "time":
            logger.info(i18n_format("now_mode_time_on"))
            logger.info(i18n_format("wait_get_token"))
            while self.get_time() < self.config["time"] - 60:
                time.sleep(10)
                logger.info(
                    i18n_format("now_waiting_info").format(
                        (self.config["time"] - self.get_time())
                    )
                )
            while self.get_time() < self.config["time"]-10:
                pass
            url = "https://api-takumi.mihoyo.com/common/badge/v1/login/account" 
            login_info = self.session.post( 
                url, headers=self.headers, 
                json={ 
                    "game_biz": "hk4e_cn", 
                    "region": self.config["role"]["region"], 
                    "lang": "zh-cn", 
                    "uid": self.config["role"]["game_uid"], 
                } 
                ).json() 
            logger.debug(login_info) 
            if login_info["retcode"] != 0:
                logger.error(i18n_format("login_failure"))
        logger.info(i18n_format("will_pay_bill"))

    def get_time(self):
        return float(time.time() + self.config["time_offset"])

    def get_ticket_status(self):
        url = f'https://hk4e-api.mihoyo.com/event/tickethub/get_act_schedule_remain?badge_uid={self.config["role"]["game_uid"]}&badge_region={self.config["role"]["region"]}&lang=zh-cn&game_biz=hk4e_cn&act_id={self.config["act_id"]}&schedule_ids[]={self.config["schedule_id"]}'
        try:
            response = self.session.get(url, headers=self.headers, timeout=1)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
        ):
            logger.error(i18n_format("network_timeout"))
            if self.config["proxy"]:
                if self.ip == self.client.tps_current_ip(sign_type="hmacsha1"):
                    logger.info(
                        i18n_format("manual_change_ip").format(
                            self.client.change_tps_ip(sign_type="hmacsha1")
                        )
                    )
                self.session.close()
                return self.get_ticket_status()
            return -1
        try:
            if response.status_code == 412:
                logger.error(i18n_format("wind_control"))
                if self.config["proxy"]:
                    if self.ip == self.client.tps_current_ip(sign_type="hmacsha1"):
                        logger.info(
                            i18n_format("manual_change_ip").format(
                                self.client.change_tps_ip(sign_type="hmacsha1")
                            )
                        )
                    self.session.close()
                    return self.get_ticket_status()
                else:
                    self.risk = True
                    logger.error(i18n_format("net_method"))
                    try:
                        if noneprompt.ConfirmPrompt(
                            question=i18n_format("res_return")
                        ).prompt():
                            return -1
                    except noneprompt.CancelledError:
                        return -1
            remain = response.json()["data"]["schedule_remains"][self.config["schedule_id"]]
            return remain
        except Exception as e:
            logger.error(i18n_format("unknown_error") + str(response.text))
            logger.debug(e)
            return -1

    def create_order(self):
        url = f"https://hk4e-api.mihoyo.com/event/tickethub/immediate_book?badge_uid={self.config['role']['game_uid']}&badge_region={self.config['role']['region']}&lang=zh-cn&game_biz=hk4e_cn"
        data = {
            "act_id": self.config["act_id"],
            "schedule_id": self.config["schedule_id"],
            "bind_ticket_id": self.config["bind_ticket_id"],
            "has_partner": False,
        }
        try:
            response = self.session.post(url, headers=self.headers, json=data)
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
        ):
            logger.error(i18n_format("network_timeout"))
            if self.config["proxy"]:
                if self.ip == self.client.tps_current_ip(sign_type="hmacsha1"):
                    logger.info(
                        i18n_format("manual_change_ip").format(
                            self.client.change_tps_ip(sign_type="hmacsha1")
                        )
                    )
                self.session.close()
            return self.create_order()
        if response.status_code == 412:
            logger.error(i18n_format("wind_control"))
            if self.config["proxy"]:
                if self.ip == self.client.tps_current_ip(sign_type="hmacsha1"):
                    logger.info(
                        i18n_format("manual_change_ip").format(
                            self.client.change_tps_ip(sign_type="hmacsha1")
                        )
                    )
                self.session.close()
                return self.create_order()
            else:
                self.risk = True
                logger.error(i18n_format("pause_60s"))
                time.sleep(60)
                return {}
        return response.json()

    def try_create_order(self):
        time.sleep(self.config["co_delay"])
        result = self.create_order()
        logger.debug(result)
        if result["retcode"] == -500004:
            logger.warning(i18n_format("bili_speed_limit"))
        elif result["retcode"] == -620003:
            logger.warning(i18n_format("not_started"))
        elif result["retcode"] == 0:
            logger.success(i18n_format("bill_push_ok"))
            self.sdk.capture_message("Get order!")
            if "pushplus" in self.config:
                    # https://www.pushplus.plus/send/
                    url = "https://www.pushplus.plus/send"
                    response = requests.post(
                        url,
                        json={
                            "token": self.config["pushplus"],
                            "title": i18n_format("BHYG_notify"),
                            "content": i18n_format("rob_ok_paying") + self.order_id,
                        },
                    ).json()
                    if response["code"] == 200:
                        logger.success(
                            i18n_format("notify_ok") + " " + response["data"]
                        )
                    else:
                        logger.error(i18n_format("notify_fail") + " " + response)
            if "webhook" in self.config:
                    url = self.config["webhook"]
                    response = requests.post(
                        url,
                        json={
                            "msg_type": "text",
                            "text": {
                                "content": i18n_format("rob_ok_paying") + self.order_id,
                            },
                        },
                    ).json()
                    if response["code"] == 200:
                        logger.success(
                            i18n_format("notify_ok") + " " + response["data"]
                        )
                    else:
                        logger.error(i18n_format("notify_fail") + " " + response)
            if "hunter" in self.config:
                    return True
            self.sdk.capture_message("Exit by in-app exit")
            return True
        else:
            logger.error(i18n_format("unknown_error") + str(result))
        return False
