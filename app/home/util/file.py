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
from home.util.rand import rand_string

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
        # proper duplication handling in storages is forgone since we assign a name prior to file object creation
        # we must check for a duplicate name and append a random string if it exists in the db
        prop_name = name
        while Files.objects.filter(name=prop_name).exists():
            split = os.path.splitext(name)
            prop_name = split[0] + "-" + rand_string(length=4) + split[1]
        name = prop_name
        file.file = File(fp, name=name)
        file.name = name
        log.info('file.name: %s', file.file.name)
        file.mime = file_mime
        log.info('file.mime: %s', file.mime)
        file.size = file.file.size
        log.info('file.size: %s', file.size)
        file.save()
    send_discord_message.delay(file.pk)
    return file
