import hashlib
import logging
import os
import random
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import requests
from requests import Response
from yarl import URL

from experiments.core import stage, experiment, StageIterator

logger = logging.getLogger(__name__)


@dataclass
class Host:
    name: str
    url: URL


@experiment
def experiment(upload_size: int, hosts: List[Host]) -> StageIterator:
    with TemporaryDirectory() as temp_dir:
        path = Path(temp_dir)
        upload_file_path = path / 'upload.bin'
        download_file_path = path / 'download.bin'

        upload_host, download_host = select_peers(hosts)

        response = upload(generate_file(upload_file_path, upload_size).open('rb'), upload_host.url,
                          _info=f'upload: {str(upload_host.name)}, '
                                f'download: {str(download_host.name)}')
        yield response

        cid = response.result.text
        response = download(download_host.url, cid, download_file_path)
        yield response

        upload_md5 = hashlib.md5(upload_file_path.open('rb').read()).hexdigest()
        download_md5 = hashlib.md5(download_file_path.open('rb').read()).hexdigest()

        if upload_md5 != download_md5:
            logger.error(f'MD5 mismatch {upload_md5} != {download_md5}')
        else:
            logger.info(f'MD5 match {upload_md5} == {download_md5}')


def select_peers(hosts: List[Host]) -> (Host, Host):
    random.shuffle(hosts)
    return hosts[0], hosts[1]


def generate_file(path: Path, size: int) -> Path:
    with path.open('wb') as f:
        f.write(os.urandom(size))
    return path


@stage
def upload(buffer: BytesIO, host: URL) -> Response:
    upload_url = host.with_path('/api/codex/v1/data')
    response = requests.post(str(upload_url), data=buffer, headers={'Content-Type': 'application/octet-stream'})
    logger.info(f'Upload status was: {response.status_code}')
    return response


@stage
def download(host: URL, cid: str, path: Path) -> Response:
    download_url = host.with_path(f'/api/codex/v1/data/{cid}/network')
    response = requests.get(str(download_url))
    logger.info(f'Download status was: {response.status_code}')
    with path.open('wb') as f:
        f.write(response.content)
    return response
