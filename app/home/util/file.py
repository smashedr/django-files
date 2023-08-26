import logging
import mimetypes
import os
import tempfile
# from django.conf import settings
from django.core.files import File
# from pathlib import Path
from typing import IO

from home.models import Files
from home.util.image import ImageProcessor
from home.tasks import send_discord_message
from oauth.models import CustomUser

log = logging.getLogger('app')


def process_file(name: str, f: IO, user_id: int, **kwargs) -> Files:
    """
    Process File Uploads
    :param name: String: name of the file
    :param f: File Object: The file to upload
    :param user_id: Integer: user ID
    :param kwargs: Extra Files Object Values
    :return: Files: The created Files object
    """
    log.info('process_file_upload: name: %s', name)
    user = CustomUser.objects.get(id=user_id)
    log.info('user: %s', user)
    # we want to use a temporary local file to support cloud storage cases
    # this allows us to modify the file before upload
    file = Files(user=user, **kwargs)
    with tempfile.NamedTemporaryFile(suffix=os.path.basename(name)) as fp:
        fp.write(f.read())
        fp.seek(0)
        file_mime, _ = mimetypes.guess_type(name, strict=False)
        if not file_mime:
            file_mime, _ = mimetypes.guess_type(name, strict=False)
        file_mime = file_mime or 'application/octet-stream'
        if file_mime in ['image/jpe', 'image/jpg', 'image/jpeg', 'image/webp']:
            processor = ImageProcessor(fp.name, user.remove_exif, user.remove_exif_geo)
            processor.process_file()
            file.meta = processor.meta
            file.exif = processor.exif
        file.file = File(fp, name=name)
        log.info('file.name: %s', file.name)
        file.mime = file_mime
        log.info('file.mime: %s', file.mime)
        file.size = file.file.size
        log.info('file.size: %s', file.size)
        file.save()
    # saving the file will cause the name to change if the file already exists, update filename in model if so
    # TODO: perhaps we should fetch name in the model with a method instead
    file.name = file.file.name
    file.save()
    send_discord_message.delay(file.pk)
    return file
