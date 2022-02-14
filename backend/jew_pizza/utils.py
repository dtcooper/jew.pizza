import datetime
import json
import logging

from dateutil.parser import parse as dateutil_parse
import requests

from django.conf import settings
from django.core.cache import cache
from django.utils.formats import date_format as django_date_format
from django.utils.timezone import localtime


logger = logging.getLogger(f"jewpizza.{__name__}")
SSE_MESSAGE_CACHE_KEY_PREFIX = "sse-message::"


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip or "[unknown]"


def format_datetime(dt, format="N j, Y g:i A"):
    return django_date_format(localtime(dt), format)


def format_datetime_short(dt):
    return format_datetime(dt, format="n/j/y g:i A")


def format_date(date, format="N j, Y"):
    return django_date_format(date, format=format)


def format_date_short(date):
    return format_date(date, format="n/j/y")


def format_time(time, format="g:i A"):
    return django_date_format(time, format=format)


def store_sse_message_in_cache(message_type, message):
    cache.set(f"{SSE_MESSAGE_CACHE_KEY_PREFIX}{message_type}", message, timeout=None)


def get_last_sse_message(message_type):
    return cache.get(f"{SSE_MESSAGE_CACHE_KEY_PREFIX}{message_type}")


def send_sse_message(message_type, message, delay=None):
    if not isinstance(message, dict):
        raise TypeError("message must be a dict")

    if delay is None:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        message = {"type": message_type, "timestamp": timestamp, "message": message}
        try:
            response = requests.post(
                "http://nginx:3000/",
                data=json.dumps(message),
                # We store it in the cache below, no need for nginx to call app back, skip via X-Skip-Store-SSE-In-Cache
                headers={"Accept": "text/json", "X-EventSource-Event": message_type, "X-Skip-Store-SSE-In-Cache": "1"},
            )
        except requests.RequestException:
            logger.exception("An error occurred while making sending an SSE message")
        else:
            if response.status_code in (201, 202):
                store_sse_message_in_cache(message_type, message)
                num_subscribers = response.json().get("subscribers", 0)
                logger.info(
                    f"{message_type} message sent to nchan to {num_subscribers} subscriber(s) (code:"
                    f" {response.status_code})"
                )
            else:
                logger.error(
                    f"Got code {response.status_code} while sending {message_type} message to nchan: {response.text}"
                )
    else:
        from webcore.tasks import send_sse_message_async

        logger.info(f"Delaying {message_type} message by {delay} seconds")
        send_sse_message_async.schedule((message_type, message), delay=delay)


def reload_radio_container():
    try:
        response = requests.get("http://radio:8000/reload/", headers={"X-Secret-Key": settings.SECRET_KEY}).json()
    except Exception:
        logger.exception("Error reloading radio container")
        return False

    if response["status"] != "okay":
        logger.error(f"Error reloading radio container: {response['error']}")
        return False
    return True


try:
    BUILD_DATE_FORMATTED = format_datetime(dateutil_parse(settings.BUILD_DATE))
except ValueError:
    BUILD_DATE_FORMATTED = "unknown"


def django_template_context(request):
    # Template context processor for Django templates
    return {
        "settings": settings,
        "BUILD_DATE": BUILD_DATE_FORMATTED,
    }
