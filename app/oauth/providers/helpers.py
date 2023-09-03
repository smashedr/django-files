import logging
from decouple import config, Csv
from django.http import HttpRequest
from django.urls import reverse
from typing import Optional

from home.models import SiteSettings
from oauth.models import CustomUser

log = logging.getLogger('app')


class OauthUser(object):
    __slots__ = [
        'id',
        'username',
        'user',
        'data',
        'profile',
    ]

    def __init__(self, _id, username, user, data, profile):
        self.id: int = _id
        self.username: int = username
        self.user: CustomUser = user
        self.data: dict = data
        self.profile: dict = profile


def get_or_create_user(_id, username):
    # get user by ID
    # user = CustomUser.objects.filter(id=oauth_profile['id'])
    user = CustomUser.objects.filter(discord__id=_id)
    if user:
        return user[0]

    # get user by username - check if the user has logged in or not
    user = CustomUser.objects.filter(username=username)
    if user:
        if user[0].last_login:
            log.warning('Hijacking Attempt BLOCKED! Connect account via Settings page.')
            return None
        log.info('User %s claimed by Discord User: %s', user.id, _id)
        return user[0]

    if SiteSettings.objects.get(pk=1).oauth_reg or is_super_id(_id):
        log.info('%s created by oauth_reg with id: %s', username, _id)
        return CustomUser.objects.create(username=username, oauth_id=_id)

    log.debug('User does not exist locally and oauth_reg is off: %s', _id)
    return None


def get_next_url(request: HttpRequest) -> str:
    """
    Determine 'next' parameter
    """
    log.debug('get_next_url')
    if 'next' in request.GET:
        log.debug('next in request.GET: %s', str(request.GET['next']))
        return str(request.GET['next'])
    if 'next' in request.POST:
        log.debug('next in request.POST: %s', str(request.POST['next']))
        return str(request.POST['next'])
    if 'login_next_url' in request.session:
        log.debug('login_next_url in request.session: %s', request.session['login_next_url'])
        url = request.session['login_next_url']
        del request.session['login_next_url']
        request.session.modified = True
        return url
    if 'HTTP_REFERER' in request.META:
        log.debug('HTTP_REFERER in request.META: %s', request.META['HTTP_REFERER'])
        return request.META['HTTP_REFERER']
    log.info('----- get_next_url FAILED -----')
    return reverse('home:index')


def get_login_redirect_url(request: HttpRequest) -> str:
    """
    Determine 'login_redirect_url' parameter
    """
    log.debug('get_login_redirect_url: login_redirect_url: %s', request.session.get('login_redirect_url'))
    if 'login_redirect_url' in request.session:
        url = request.session['login_redirect_url']
        del request.session['login_redirect_url']
        request.session.modified = True
        return url
    return reverse('home:index')


def is_super_id(oauth_id):
    if oauth_id in config('SUPER_USERS', '', Csv()):
        return True
    else:
        return False
