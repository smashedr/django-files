import json
import logging
import urllib.parse
import duo_universal
from decouple import config
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import HttpResponseRedirect, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from typing import Optional

from home.models import SiteSettings, Webhooks
from oauth.forms import LoginForm
from oauth.providers.helpers import get_login_redirect_url, get_next_url, is_super_id, OauthUser
from oauth.providers.discord import DiscordOauth
from oauth.models import CustomUser

log = logging.getLogger('app')


@csrf_exempt
def oauth_show(request):
    """
    View  /oauth/
    """
    if request.method == 'POST':
        request.session['login_redirect_url'] = get_next_url(request)
        form = LoginForm(request.POST)
        if not form.is_valid():
            log.debug(form.errors)
            return HttpResponse(status=400)
        user = authenticate(request,
                            username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])
        if not user:
            return HttpResponse(status=401)

        if SiteSettings.objects.get(pk=1).duo_auth:
            # if config('DUO_CLIENT_ID', False):
            #     pass
            log.info('--- DUO DETECTED - REDIRECTING ---')
            log.debug('username: %s', user.username)
            request.session['username'] = user.username
            url = duo_redirect(request, user.username)
            log.debug('url: %s', url)
            return JsonResponse({'redirect': url})

        login(request, user)
        messages.info(request, f'Successfully logged in as {user.username}.')
        return HttpResponse()

    if request.user.is_authenticated:
        next_url = get_next_url(request)
        return HttpResponseRedirect(next_url)
    else:
        return render(request, 'login.html')


def oauth_discord(request):
    """
    View  /oauth/discord/
    """
    request.session['login_redirect_url'] = get_next_url(request)
    return DiscordOauth.redirect_login(request)


def oauth_callback(request):
    """
    View  /oauth/callback/
    """
    log.debug('oauth_callback: login_next_url: %s', request.session.get('login_next_url'))
    if 'code' not in request.GET:
        messages.warning(request, 'User aborted or no code in response...')
        return HttpResponseRedirect(get_login_redirect_url(request))
    try:
        log.debug('code: %s', request.GET['code'])
        if request.session['oauth_provider'] == 'discord':
            user: OauthUser = DiscordOauth.get_user(request.GET['code'])
        else:
            messages.error(request, 'Unknown Provider: %s' % request.session['oauth_provider'])
            return HttpResponseRedirect(get_login_redirect_url(request))

        if not user:
            messages.error(request, 'User Not Found or Already Taken.')
            return HttpResponseRedirect(get_login_redirect_url(request))

        update_profile(user.user, user.profile)
        login(request, user)
        messages.info(request, f'Successfully logged in. {user.user.first_name}.')

        # if 'webhook' in token_resp:
        #     log.debug('webhook in profile')
        #     webhook = add_webhook(request, token_resp)
        #     messages.info(request, f'Webhook successfully added: {webhook.id}')
        # else:
        #     messages.info(request, f'Successfully logged in. {user.first_name}.')
    except Exception as error:
        log.exception(error)
        messages.error(request, f'Exception during login: {error}')
    return HttpResponseRedirect(get_login_redirect_url(request))


# def get_or_create_user(request, profile: dict) -> Optional[CustomUser]:
#     # user, _ = CustomUser.objects.get_or_create(username=profile['id'])
#     user = CustomUser.objects.filter(oauth_id=profile['oauth_id'])
#     if user:
#         if 'oauth_claim_username' in request.session:
#             del request.session['oauth_claim_username']
#             log.warning('OAuth ID Already Claimed!')
#             return None
#         log.debug('oauth user found by oauth_id: %s', user[0].oauth_id)
#         return user[0]
#     if 'oauth_claim_username' in request.session:
#         username = request.session['oauth_claim_username']
#         del request.session['oauth_claim_username']
#         log.warning('used oauth_claim_username: %s', username)
#         return CustomUser.objects.filter(username=username)[0]
#     user = CustomUser.objects.filter(username=profile['username'])
#     if user:
#         if not user[0].last_login:
#             log.warning('%s claimed by oauth_id: %s', profile['username'], profile['oauth_id'])
#             return user[0]
#         log.warning('Hijacking Attempt BLOCKED! Connect account via Settings page.')
#         return None
#     if SiteSettings.objects.get(pk=1).oauth_reg or is_super_id(profile['oauth_id']):
#         log.warning('%s created by oauth_reg with oauth_id: %s', profile['username'], profile['oauth_id'])
#         return CustomUser.objects.create(
#             username=profile['username'], oauth_id=profile['oauth_id'])
#     log.debug('User does not exist locally and oauth_reg is off: %s', profile['oauth_id'])
#     return None


def duo_callback(request):
    """
    View  /oauth/duo/
    """
    log.debug('%s - duo_callback', request.method)
    try:
        duo_client = get_duo_client(request)
        state = request.GET.get('state')
        log.debug('state: %s', state)
        code = request.GET.get('duo_code')
        log.debug('code: %s', code)
        if state != request.session['state']:
            messages.warning(request, 'State Check Failed. Try Again!')
            return HttpResponseRedirect(get_login_redirect_url(request))
        username = request.session['username']
        log.debug('username: %s', username)
        decoded_token = duo_client.exchange_authorization_code_for_2fa_result(code, username)
        log.debug('decoded_token: %s', decoded_token)
        user = CustomUser.objects.get(username=username)
        login(request, user)

        if 'profile' in request.session:
            log.debug('profile in session, updating oauth profile')
            update_profile(user, json.loads(request.session['profile']))
            del request.session['profile']

        log.debug('duo_callback: login_next_url: %s', request.session.get('login_next_url'))
        messages.success(request, f'Congrats, You Authenticated Twice, {username}!')
        return HttpResponseRedirect(get_login_redirect_url(request))

    except Exception as error:
        log.exception(error)
        return HttpResponse(status=401)


def duo_redirect(request, username):
    log.debug('duo_redirect: username: %s', username)
    duo_client = get_duo_client(request)
    try:
        duo_client.health_check()
    except duo_universal.DuoException as error:
        log.exception(error)
        raise ValueError('Duo Health Check Failed: %s', error)

    state = duo_client.generate_state()
    log.debug('state: %s', state)
    request.session['state'] = state

    prompt_uri = duo_client.create_auth_url(username, state)
    log.debug('prompt_uri: %s', prompt_uri)
    return prompt_uri


def get_duo_client(request):
    log.debug('request.build_absolute_uri: %s', request.build_absolute_uri())
    site_url = SiteSettings.objects.get(pk=1).site_url
    log.debug('site_url: %s', site_url)
    redirect_uri = site_url.rstrip('/') + reverse('oauth:duo')
    log.debug('redirect_uri: %s', redirect_uri)
    return duo_universal.Client(
        config('DUO_CLIENT_ID'),
        config('DUO_CLIENT_SECRET'),
        config('DUO_API_HOST'),
        redirect_uri,
    )


@csrf_exempt
@require_http_methods(['POST'])
def oauth_logout(request):
    """
    View  /oauth/logout/
    """
    next_url = get_next_url(request)
    log.debug('oauth_logout: next_url: %s', next_url)
    logout(request)
    request.session['login_next_url'] = next_url
    messages.info(request, 'Successfully logged out.')
    log.debug('oauth_logout: login_next_url: %s', request.session.get('login_next_url'))
    return redirect(next_url)


def oauth_webhook(request):
    """
    View  /oauth/webhook/
    """
    return DiscordOauth.redirect_webhook(request)
    # request.session['login_redirect_url'] = get_next_url(request)
    # log.debug('oauth_webhook: login_redirect_url: %s', request.session.get('login_redirect_url'))
    # params = {
    #     'redirect_uri': config('OAUTH_REDIRECT_URL'),
    #     'client_id': config('DISCORD_CLIENT_ID'),
    #     'response_type': config('OAUTH_RESPONSE_TYPE', 'code'),
    #     'scope': config('OAUTH_SCOPE', 'identify') + ' webhook.incoming',
    # }
    # url_params = urllib.parse.urlencode(params)
    # url = f'https://discord.com/api/oauth2/authorize?{url_params}'
    # return HttpResponseRedirect(url)


def add_webhook(request, profile):
    """
    Add webhook
    """
    log.debug('add_webhook')
    webhook = Webhooks(
        hook_id=profile['webhook']['id'],
        guild_id=profile['webhook']['guild_id'],
        channel_id=profile['webhook']['channel_id'],
        url=profile['webhook']['url'],
        owner=request.user,
    )
    webhook.save()
    return webhook


def update_profile(user: CustomUser, profile: dict) -> None:
    """
    Update Django user profile with provided data
    """
    log.debug('update_profile')
    log.debug('user.username: %s', user.username)
    log.debug('profile.username: %s', profile['username'])
    del profile['username']
    for key, value in profile.items():
        setattr(user, key, value)
    if is_super_id(profile['oauth_id']):
        log.info('Super user login: %s', profile['oauth_id'])
        user.is_staff, user.is_admin, user.is_superuser = True, True, True
    user.save()


# log.debug('user.username: %s', user.username)
# if SiteSettings.objects.get(pk=1).duo_auth:
#     log.info('--- DUO DETECTED - REDIRECTING ---')
#     request.session['username'] = user.username
#     request.session['profile'] = json.dumps(profile, default=str)
#     url = duo_redirect(request, user.username)
#     log.debug('url: %s', url)
#     return HttpResponseRedirect(url)
