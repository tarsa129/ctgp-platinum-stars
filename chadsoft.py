
import requests
import urllib
import pathlib
import json
import time
import re
import os
import random
import traceback

API_URL = "https://tt.chadsoft.co.uk"

class CacheSettings:
    __slots__ = ("read_cache", "write_cache", "cache_dirname", "rate_limit", "retry_on_empty")

    def __init__(self, read_cache, write_cache, cache_dirname, rate_limit=False, retry_on_empty=False):
        self.read_cache = read_cache
        self.write_cache = write_cache
        self.cache_dirname = cache_dirname
        self.rate_limit = rate_limit
        self.retry_on_empty = retry_on_empty

default_cache_settings = CacheSettings(True, True, "chadsoft_cached")

def get_cached_endpoint_filepath(endpoint, params, is_binary, cache_settings):
    if not is_binary:
        endpoint_as_pathname = f"{cache_settings.cache_dirname}/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.json"
    else:
        endpoint_as_pathname = f"{cache_settings.cache_dirname}/{urllib.parse.quote(endpoint, safe='')}_q_{urllib.parse.urlencode(params, doseq=True)}.rkg"

    return pathlib.Path(endpoint_as_pathname)

def get(endpoint, params=None, is_binary=False, cache_settings=None):
    exception_sleep_time = 15

    while True:
        try:
            return get_in_loop_code(endpoint, params, is_binary, cache_settings)
        except ConnectionError as e:
            print(f"Exception occurred: {e}\n{''.join(traceback.format_tb(e.__traceback__))}\nSleeping for {exception_sleep_time} seconds now.")
            time.sleep(exception_sleep_time)
            exception_sleep_time *= 2
            if exception_sleep_time > 1000:
                exception_sleep_time = 1000

def get_in_loop_code(endpoint, params, is_binary, cache_settings):
    if params is None:
        params = {}

    if cache_settings is None:
        cache_settings = default_cache_settings

    endpoint_as_path = get_cached_endpoint_filepath(endpoint, params, is_binary, cache_settings)
    if cache_settings.read_cache and endpoint_as_path.is_file():
        error_code = None

        endpoint_as_path_size = endpoint_as_path.stat().st_size
        if endpoint_as_path_size == 0:
            if not is_binary:
                return {}, 404
            else:
                return bytes(), 404

        if not is_binary:
            #print(f"endpoint_as_path: {endpoint_as_path}")
            with open(endpoint_as_path, "r", encoding="utf-8-sig") as f:
                content = f.read().encode("utf-8")
                if len(content) < 5:
                    try:
                        error_code = int(content, 10)
                    except ValueError:
                        pass

                if error_code is None:
                    data = json.loads(content)
        else:
            with open(endpoint_as_path, "rb") as f:
                data = f.read()

            if len(data) < 5:
                try:
                    data_as_str = data.decode("utf-8")
                    error_code = int(data_as_str, 10)
                except (ValueError, UnicodeDecodeError):
                    pass

        if error_code is None:
            return data, 200

    url = f"{API_URL}{endpoint}"
    print(f"url: {url}?{urllib.parse.urlencode(params, doseq=True)}")
    start_time = time.time()
    r = requests.get(url, params=params)
    end_time = time.time()
    print(f"Request took {end_time - start_time}.")

    if cache_settings.write_cache:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)

    if r.status_code != 200:
        if r.status_code != 404:
            raise ConnectionError(f"Got status code {r.status_code}!")

        if cache_settings.write_cache:
            if r.status_code == 404:
                endpoint_as_path.touch()
            else:
                print(f"Got non-404 error code: {r.status_code}")
                with open(endpoint_as_path, "w+") as f:
                    f.write(str(r.status_code))

        return r.reason, r.status_code
        #raise RuntimeError(f"API returned {r.status_code}: {r.reason}")

    if not is_binary:
        data = json.loads(r.content.decode("utf-8-sig"))
    else:
        data = r.content

    if cache_settings.write_cache:
        endpoint_as_path.parent.mkdir(parents=True, exist_ok=True)
        if not is_binary:
            with open(endpoint_as_path, "w+", encoding="utf-8-sig") as f:
                f.write(r.text)
        else:
            with open(endpoint_as_path, "wb+") as f:
                f.write(r.content)

    if cache_settings.rate_limit:
        time.sleep(1)

    return data, r.status_code
