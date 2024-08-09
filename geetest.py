# Copyright (c) 2023-2024 ZianTT, FriendshipEnder
import time
import importlib
import noneprompt
import requests


from loguru import logger

# REF: https://github.com/mikumifa/biliTickerBuy
# REF: https://github.com/Amorter/biliTicker_gt
# LICENSE: GPL-3.0

from i18n import i18n_format


def run(gt, challenge, token, mode="local_gt", key=None):
    if mode == "local_gt":
        try:
            validator = Validator()
            validate_string = validator.validate(gt, challenge)
            data = {
                "success": True,
                "challenge": challenge,
                "validate": validate_string,
                "seccode": validate_string,
            }

            return data
        except Exception as e:
            print(f"Error: {e}")
    elif mode == "rrocr":
        # http://api.rrocr.com/api/recognize.html
        param = {
            "appkey": key,
            "gt": gt,
            "challenge": challenge,
        }
        try:
            response = requests.post(
                "http://api.rrocr.com/api/recognize.html", data=param
            ).json()
        except Exception as e:
            print(f"Error: {e}")
            return
        if response["status"] == 0:
            data = {
                "success": True,
                "challenge": response["data"]["challenge"],
                "validate": response["data"]["validate"],
                "seccode": response["data"]["validate"],
            }
            return data
        else:
            print(f"Error: {response['msg']}")
    elif mode == "manual":
        logger.info(i18n_format("manual_verify"))
        logger.info(gt + " " + challenge)
        import pyperclip

        try:
            pyperclip.copy(gt + " " + challenge)
        except pyperclip.PyperclipException:
            logger.error(i18n_format("manual_copy"))
        try:
            validate = noneprompt.InputPrompt(
                question=i18n_format("input_captcha")
            ).prompt()
        except noneprompt.CancelledError:
            return
        data = {
            "success": True,
            "challenge": challenge,
            "validate": validate,
            "seccode": validate,
        }
        return data
    else:
        logger.critical(i18n_format("captcha_mode_not_supported"))


class Validator:
    def __init__(self):
        try:
            logger.info(i18n_format("try_load_local_captcha"))
            bili_ticket_gt_python = importlib.import_module("bili_ticket_gt_python")
            logger.info(i18n_format("load_success"))
        except Exception as e:
            logger.error(i18n_format("local_captcha_load_failed".format(e)))
            raise KeyboardInterrupt
        self.click = bili_ticket_gt_python.ClickPy()
        pass

    def validate(self, gt, challenge) -> str:
        try:
            validate = self.click.simple_match_retry(gt, challenge)
            return validate
        except Exception as e:
            return ""


if __name__ == "__main__":
    import random

    captcha = requests.get(
        "https://www.geetest.com/demo/gt/register-slide-official?t="
        + str(random.randint(0, 9999)),
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        },
    ).json()
    gt = captcha["gt"]
    challenge = captcha["challenge"]
    token = "1"
    # validate = run(gt, challenge, token)
    start_time = time.time()
    validate = run(gt, challenge, token, mode="local_gt")
    print(f"Time: {time.time() - start_time}")
    print(validate)
