import logging
import mimetypes
import os
import httpx
import json
import urllib.parse
from celery import shared_task
from django_redis import get_redis_connection
from django.conf import settings
# from django.core import management
from django.core.cache import cache
# from django.core.cache.utils import make_template_fragment_key
from django.template.loader import render_to_string
from django.utils import timezone
from pytimeparse2 import parse

from home.models import Files, FileStats, ShortURLs, SiteSettings, Webhooks
from home.util.processors import ImageProcessor
from oauth.models import CustomUser

log = logging.getLogger('app')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 20, 'countdown': 3})
def app_init():
    # App Init Task
    log.info('app_init')
    site_settings, created = SiteSettings.objects.get_or_create(pk=1)
    if created:
        if not site_settings.site_url:
            site_settings.site_url = settings.SITE_URL
            site_settings.save()
        log.info('site_settings created')
    else:
        log.warning('site_settings already created')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 300})
def app_cleanup():
    # App Cleanup Task
    log.info('app_cleanup')
    with open(settings.NGINX_ACCESS_LOGS, 'a') as f:
        f.truncate(0)


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def flush_template_cache():
    # Flush all template cache on request
    log.info('flush_template_cache')
    return cache.delete_pattern('template.cache.*')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def clear_files_cache():
    # Clear Files cache
    log.info('clear_files_cache')
    return cache.delete_pattern('*files*')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def clear_shorts_cache():
    # Clear Shorts cache
    log.info('clear_shorts_cache')
    return cache.delete_pattern('template.cache.shorts*')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def clear_stats_cache():
    # Clear Stats cache
    log.info('clear_stats_cache')
    return cache.delete_pattern('template.cache.stats*')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 10})
def clear_settings_cache():
    # Clear Settings cache
    log.info('clear_settings_cache')
    return cache.delete_pattern('template.cache.settings*')


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 6, 'countdown': 5})
def process_file_upload(pk):
    # Process new file upload
    # TODO: Fix all the sub functions/classes
    img_mimes = ['image/jpe', 'image/jpg', 'image/jpeg', 'image/webp']
    log.info('process_file_upload: %s', pk)
    file = Files.objects.get(pk=pk)
    log.debug('-'*40)
    log.debug('file: %s', file)
    log.debug('file.file: %s', file.file)
    log.debug('file.file.path: %s', file.file.path)
    log.debug('-'*40)
    if not file or not file.file:
        return log.warning('WARNING NO FILE -- file or file.file is None --')
    file.name = os.path.basename(file.file.name)
    log.debug('file.name: %s', file.name)
    file.mime, _ = mimetypes.guess_type(file.file.path, strict=False)
    if not file.mime:
        file.mime, _ = mimetypes.guess_type(file.file.name, strict=False)
    file.mime = file.mime or 'application/octet-stream'
    log.debug('file.mime: %s', file.mime)
    file.size = file.file.size
    log.debug('file.size: %s', file.size)
    if file.mime.startswith('image'):
        if file.mime in img_mimes:
            processor = ImageProcessor(file)
            processor.process_file()
    file.save()
    log.info('-'*40)
    send_discord_message.delay(file.pk)
    return file.pk


@shared_task()
def delete_expired_files():
    # Delete Expired Files
    log.info('delete_expired_files')
    files = Files.objects.all()
    now = timezone.now()
    i = 0
    for file in files:
        if parse(file.expr):
            delta = now - file.date
            if delta.seconds > parse(file.expr):
                log.info('Deleting expired file: %s', file.file.name)
                file.delete()
                i += 1
    return f'Deleted/Processed: {i}/{len(files)}'


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': 30})
def process_stats():
    # Process file stats
    log.info('----- START process_stats -----')
    now = timezone.now()
    files = Files.objects.all()
    data = {'_totals': {'types': {}, 'size': 0, 'count': 0, 'shorts': 0}}
    for file in files:
        if file.user_id not in data:
            data[file.user_id] = {'types': {}, 'size': 0, 'count': 0, 'shorts': 0}

        data['_totals']['count'] += 1
        data[file.user_id]['count'] += 1

        data['_totals']['size'] += file.size
        data[file.user_id]['size'] += file.size

        if file.mime in data['_totals']['types']:
            data['_totals']['types'][file.mime]['count'] += 1
            data['_totals']['types'][file.mime]['size'] += file.size
        else:
            data['_totals']['types'][file.mime] = {'size': file.size, 'count': 1}

        if file.mime in data[file.user_id]['types']:
            data[file.user_id]['types'][file.mime]['count'] += 1
            data[file.user_id]['types'][file.mime]['size'] += file.size
        else:
            data[file.user_id]['types'][file.mime] = {'size': file.size, 'count': 1}

    shorts = ShortURLs.objects.all()
    users = CustomUser.objects.all()
    for user in users:
        s = shorts.filter(user=user)
        if user.id not in data:
            data[user.id] = {'types': {}, 'size': 0, 'count': 0, 'shorts': len(s)}
        else:
            data[user.id]['shorts'] = len(s)

    for user_id, _data in data.items():
        _data['human_size'] = Files.get_size_of(_data['size'])
        log.debug('user_id: %s', user_id)
        user_id = None if str(user_id) == '_totals' else user_id
        log.debug('user_id: %s', user_id)
        log.debug('_data: %s', _data)
        stats = FileStats.objects.filter(user_id=user_id, created_at__day=now.day)
        if stats:
            stats = stats[0]
            stats.stats = _data
            stats.save()
        else:
            stats = FileStats.objects.create(
                user_id=user_id,
                stats=_data,
            )
        log.debug('stats.pk: %s', stats.pk)
    log.debug(data)
    log.info('----- END process_stats -----')


@shared_task()
def process_vector_stats():
    # Process Vector Stats
    # TODO: Add try, expect, finally for deleting keys
    log.info('process_vector_stats')
    client = get_redis_connection('vector')
    _, keys = client.scan(0, '*', 1000)
    i = 0
    for key in keys:
        log.info('Processing Key: %s', key)
        raw = client.lrange(key, 0, -1)
        if not raw:
            log.warning('No Data for Key: %s', key)
            client.delete(key)
            continue
        try:
            data = json.loads(raw[0])
        except Exception as error:
            log.warning('Error Loading JSON for Key: %s: %s', key, error)
            client.delete(key)
            continue
        log.info(data)
        full_uri = data['request'].split()[1]
        log.info('full_uri: %s', full_uri)
        if '?' in full_uri:
            uri, query = full_uri.split('?', 1)
        else:
            uri, query = full_uri, None
        log.info('query: %s', query)
        if query:
            qs = urllib.parse.parse_qs(query) or {}
            log.info('qs: %s', qs)
            if qs.get('view'):
                log.info('Not Processing due to QS: %s: %s', uri, qs)
                client.delete(key)
                continue
        name = uri.replace('/r/', '')
        file = Files.objects.filter(name=name)
        if not file:
            log.warning('404 File Not Found: %s', name)
            client.delete(key)
            continue
        else:
            file = file[0]
        file.view += 1
        file.save()
        client.delete(key)
        i += 1
    return f'Processed {i}/{len(keys)} Files/Keys'


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60}, rate_limit='10/m')
def send_discord_message(pk):
    # Send a Discord message for a new file
    log.info('send_discord_message: pk: %s', pk)
    file = Files.objects.get(pk=pk)
    webhooks = Webhooks.objects.filter(owner=file.user)
    context = {'file': file}
    message = render_to_string('message/new-file.html', context)
    log.info(message)
    for hook in webhooks:
        send_discord.delay(hook.id, message)


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60}, rate_limit='10/m')
def send_success_message(hook_pk):
    # Send a success message for new webhook
    site_settings = SiteSettings.objects.get(pk=1)
    log.info('send_success_message: %s', hook_pk)
    context = {'site_url': site_settings.site_url}
    message = render_to_string('message/welcome.html', context)
    send_discord.delay(hook_pk, message)


@shared_task(autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60}, rate_limit='10/m')
def send_discord(hook_pk, message):
    log.info('send_discord: %s', hook_pk)
    try:
        webhook = Webhooks.objects.get(pk=hook_pk)
        body = {'content': message}
        log.info(body)
        r = httpx.post(webhook.url, json=body, timeout=30)
        if r.status_code == 404:
            log.warning('Hook %s removed by owner %s', webhook.hook_id, webhook.owner.username)
            webhook.delete()
            return 404
        if not r.is_success:
            log.warning(r.content.decode(r.encoding))
            r.raise_for_status()
        return r.status_code
    except Exception as error:
        log.exception(error)
        raise
