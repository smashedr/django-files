import functools
import httpx
import io
import json
import logging
import os
import validators
from django.core import serializers
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import reverse, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from pytimeparse2 import parse
from typing import Optional, BinaryIO
from urllib.parse import urlparse

from home.models import Files, FileStats, ShortURLs
from home.util.file import process_file
from home.util.rand import rand_string
from home.util.misc import anytobool
from oauth.models import CustomUser, UserInvites
from settings.models import SiteSettings

log = logging.getLogger('app')
cache_seconds = 60*60*4


def auth_from_token(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        # TODO: Only Allow Token Auth, or else cache will prevent user switching
        if request.user.is_authenticated:
            return view(request, *args, **kwargs)
        authorization = request.headers.get('Authorization') or request.headers.get('Token')
        if authorization:
            user = CustomUser.objects.filter(authorization=authorization)
            if user:
                request.user = user[0]
                return view(request, *args, **kwargs)
        return JsonResponse({'error': 'Invalid Authorization'}, status=401)
    return wrapper


@csrf_exempt
@login_required
def api_view(request):
    """
    View  /api/
    """
    log.debug('%s - api_view: is_secure: %s', request.method, request.is_secure())
    return render(request, 'api.html')


@csrf_exempt
@require_http_methods(['OPTIONS', 'POST'])
@auth_from_token
def upload_view(request):
    """
    View  /upload/ and /api/upload
    """
    log.debug('upload_view')
    # log.debug(request.headers)
    post = request.POST.dict().copy()
    log.debug(post)
    log.debug(request.FILES)
    try:
        f = request.FILES.get('file')
        if not f and post.get('text'):
            f = io.BytesIO(bytes(post.pop('text'), 'utf-8'))
            f.name = post.pop('name', 'paste.txt') or 'paste.txt'
            f.name = f.name if '.' in f.name else f.name + '.txt'
        if not f:
            return JsonResponse({'error': 'No file or text keys found.'}, status=400)
        # TODO: Determine how to better handle expire and why info is still being used differently from other methods
        extra_args = parse_headers(request.headers, expr=parse_expire(request), **post)
        log.debug('f.name: %s', f.name)
        log.debug('extra_args: %s', extra_args)
        log.debug('request.user: %s', request.user)
        return process_file_upload(f, request.user.id, **extra_args)
    except Exception as error:
        log.exception(error)
        return JsonResponse({'error': str(error)}, status=500)


@csrf_exempt
@require_http_methods(['OPTIONS', 'POST'])
@auth_from_token
def shorten_view(request):
    """
    View  /shorten/ and /api/shorten
    """
    body = request.body.decode()
    try:
        url = request.headers.get('url')
        vanity = request.headers.get('vanity')
        max_views = request.headers.get('max-views')
        if not url:
            try:
                data = json.loads(body)
                log.debug('data: %s', data)
                url = data.get('url', url)
                vanity = data.get('vanity', vanity)
                max_views = data.get('max-views', max_views)
            except Exception as error:
                log.debug(error)
        if not url:
            return JsonResponse({'error': 'Missing Required Value: url'}, status=400)

        log.debug('url: %s', url)
        if not validators.url(url):
            return JsonResponse({'error': 'Unable to Validate URL'}, status=400)
        if max_views and not str(max_views).isdigit():
            return JsonResponse({'error': 'max-views Must be an Integer'}, status=400)
        if vanity and not validators.slug(vanity):
            return JsonResponse({'error': 'vanity Must be a Slug'}, status=400)
        short = gen_short(vanity)
        log.debug('short: %s', short)
        url = ShortURLs.objects.create(
            url=url,
            short=short,
            max=max_views or 0,
            user=request.user,
        )
        site_settings = SiteSettings.objects.settings()
        full_url = site_settings.site_url + reverse('home:short', kwargs={'short': url.short})
        return JsonResponse({'url': full_url}, safe=False)

    except Exception as error:
        log.exception(error)
        return JsonResponse({'error': str(error)}, status=500)


@csrf_exempt
@require_http_methods(['OPTIONS', 'GET', 'POST'])
@auth_from_token
@cache_control(no_cache=True)
@cache_page(cache_seconds, key_prefix='stats')
@vary_on_headers('Authorization')
@vary_on_cookie
def invites_view(request):
    """
    View  /api/invites/
    """
    log.debug('%s - invites_view: is_secure: %s', request.method, request.is_secure())
    if request.method == 'POST':
        body = request.body.decode()
        data = json.loads(body)
        log.debug('data: %s', data)
        invite = UserInvites.objects.create(
            owner=request.user,
            expire=parse(data.get('expire', 0)) or 0,
            max_uses=data.get('max_uses', 1),
            super_user=anytobool(data.get('super_user', False)),
        )
        log.debug(invite)
        log.debug(model_to_dict(invite))
        return JsonResponse(model_to_dict(invite))

    return JsonResponse({'error': 'Not Implemented'}, status=501)


@csrf_exempt
@require_http_methods(['OPTIONS', 'GET'])
@auth_from_token
@cache_control(no_cache=True)
@cache_page(cache_seconds, key_prefix='stats')
@vary_on_headers('Authorization')
@vary_on_cookie
def stats_view(request):
    """
    View  /api/stats/
    """
    log.debug('%s - stats_view: is_secure: %s', request.method, request.is_secure())
    amount = int(request.GET.get('amount', 10))
    log.debug('amount: %s', amount)
    # TODO: Format Stats
    stats = FileStats.objects.filter(user=request.user)[:amount]
    data = serializers.serialize('json', stats)
    return JsonResponse(json.loads(data), safe=False)


@csrf_exempt
@require_http_methods(['OPTIONS', 'GET'])
@auth_from_token
@cache_control(no_cache=True)
@cache_page(cache_seconds, key_prefix='files')
@vary_on_headers('Authorization')
@vary_on_cookie
def recent_view(request):
    """
    View  /api/recent/
    """
    log.debug('request.user: %s', request.user)
    log.debug('%s - recent_view: is_secure: %s', request.method, request.is_secure())
    amount = int(request.GET.get('amount', 10))
    log.debug('amount: %s', amount)
    files = Files.objects.filter(user=request.user).order_by('-id')[:amount]
    log.debug(files)
    data = [file.preview_url() for file in files]
    log.debug('data: %s', data)
    return JsonResponse(data, safe=False, status=200)


@csrf_exempt
@require_http_methods(['OPTIONS', 'POST'])
@auth_from_token
def remote_view(request):
    """
    View  /api/remote/
    """
    log.debug('%s - remote_view: is_secure: %s', request.method, request.is_secure())
    log.debug('request.POST: %s', request.POST)
    body = request.body.decode()
    log.debug('body: %s', body)
    try:
        data = json.loads(body)
    except Exception as error:
        log.debug(error)
        return JsonResponse({'error': f'{error}'}, status=400)

    url = data.get('url')
    log.debug('url: %s', url)
    if not validators.url(url):
        return JsonResponse({'error': 'Missing/Invalid URL'}, status=400)

    parsed_url = urlparse(url)
    log.debug('parsed_url: %s', parsed_url)
    name = os.path.basename(parsed_url.path)
    log.debug('name: %s', name)

    r = httpx.get(url, follow_redirects=True)
    if not r.is_success:
        return JsonResponse({'error': f'{r.status_code} Fetching {url}'}, status=400)

    extra_args = parse_headers(request.headers, expr=parse_expire(request), **request.POST.dict())
    log.debug('extra_args: %s', extra_args)
    file = process_file(name, io.BytesIO(r.content), request.user.id, **extra_args)
    response = {'url': f'{file.preview_url()}'}
    log.debug('response: %s', response)
    return JsonResponse(response)


def parse_headers(headers: dict, **kwargs) -> dict:
    data = {}
    # TODO: IMPORTANT: Determine why these values are not 1:1 - meta_preview:embed
    difference_mapping = {'embed': 'meta_preview'}
    for key in ['format', 'embed', 'password', 'private', 'strip-gps', 'strip-exif', 'auto-password']:
        if key in headers:
            value = headers[key]
            if key in difference_mapping:
                key = difference_mapping[key]
            data[key.replace('-', '_')] = value
    # data.update(**kwargs)
    for key, value in kwargs.items():
        if key in ['format', 'embed', 'password', 'private', 'strip-gps', 'strip-exif', 'auto-password']:
            data[key] = value
    return data


def process_file_upload(f: BinaryIO, user_id: int, **kwargs):
    log.debug('user_id: %s', user_id)
    log.debug('kwargs: %s', kwargs)
    name = kwargs.pop('name', f.name)
    file = process_file(name, f, user_id, **kwargs)
    data = {
        'files': [file.preview_url()],
        'url': file.preview_url(),
        'raw': file.get_url(),
        'name': file.name,
        'size': file.size,
    }
    return JsonResponse(data)


def gen_short(vanity: Optional[str] = None, length: int = 4) -> str:
    if vanity:
        if not ShortURLs.objects.filter(short=vanity):
            return vanity
        else:
            raise ValueError(f'Vanity Taken: {vanity}')
    rand = rand_string(length=length)
    while ShortURLs.objects.filter(short=rand):
        rand = rand_string(length=length)
    return rand


def parse_expire(request) -> str:
    # Get Expiration from POST or Default
    expr = ''
    if request.POST.get('Expires-At') is not None:
        expr = request.POST['Expires-At'].strip()
    elif request.POST.get('ExpiresAt') is not None:
        expr = request.POST['ExpiresAt'].strip()
    elif request.headers.get('Expires-At') is not None:
        expr = request.headers['Expires-At'].strip()
    elif request.headers.get('ExpiresAt') is not None:
        expr = request.headers['ExpiresAt'].strip()
    if expr.lower() in ['0', 'never', 'none', 'null']:
        return ''
    if parse(expr) is not None:
        return expr
    if request.user.is_authenticated:
        return request.user.default_expire or ''
    return ''
