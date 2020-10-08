import os
from time import sleep
from urllib.parse import urljoin
import copy
import logging
import math
import sys

import redis
import requests

REDIS_HOSTNAME = os.getenv('REDIS_HOSTNAME')
REDIS_PORT = os.getenv('REDIS_PORT')
DB = os.getenv('REDIS_DB')

logger = logging.getLogger()

console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.WARNING)
logger.addHandler(console_handler)

r = redis.Redis(
    host=REDIS_HOSTNAME if REDIS_HOSTNAME else 'localhost',
    port=REDIS_PORT if REDIS_PORT else 6379,
    db=DB if DB else 0
)


def find_free_url(api_addr: list, interval: int) -> tuple:
    """
    Return url for request.
    :param api_addr: List of URLs
    :param interval: Min interval between requests
    :return: Is URL found. If found return url, else return min TTL of busy URLs
    """
    ttl = math.inf
    for url in api_addr:
        try:
            is_busy = r.get(url)
            if not is_busy:
                r.set(url, 'busy', px=interval)
                return True, url
        except redis.RedisError as error:
            logger.critical("Redis Error: {}".format(error))
            raise redis.RedisError
        ttl = min(ttl, r.pttl(url))
    return False, ttl


def mute_url(api_addr: list, url: str) -> list:
    """
    Delete unworkable URL from list of URLs
    :param api_addr: List of API URLs
    :param url: Unworkable URL
    :return: New list w/o unworkable URL
    """
    muted_url_api_addr = copy.deepcopy(api_addr)
    muted_url_api_addr.pop(muted_url_api_addr.index(url))
    return muted_url_api_addr


def send_request_to_api(api_addr: list, path: str, interval: int):
    """
    Send request to API URLs with select interval with protecting from throttle
    :param api_addr: List of API URLs
    :param path: Path to API endpoint
    :param interval: Interval in milliseconds
    :return: Response from API or None
    """

    if not len(api_addr):
        return None

    is_free, url = find_free_url(api_addr, interval)
    if is_free:
        try:
            return requests.get(urljoin(url, path)).json()
        except requests.exceptions.HTTPError as HTTPError:
            logger.critical("Http Error: {}".format(HTTPError))
            return send_request_to_api(mute_url(api_addr, url), path, interval)
        except requests.exceptions.ConnectionError as ConnectError:
            logger.critical("Error Connecting: {}".format(ConnectError))
            return send_request_to_api(mute_url(api_addr, url), path, interval)
        except requests.exceptions.Timeout as Timeout:
            logger.critical("Timeout Error: {}".format(Timeout))
            return send_request_to_api(mute_url(api_addr, url), path, interval)
        except requests.exceptions.RequestException as error:
            logger.critical(error)
            return send_request_to_api(mute_url(api_addr, url), path, interval)
    sleep(url / 1000.0)
    return send_request_to_api(api_addr, path, interval)
