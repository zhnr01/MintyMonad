import base64
import json
import ipaddress
import socket
from functools import lru_cache
from urllib.parse import urlparse

import requests

MAX_METADATA_BYTES = 1_048_576
MAX_DATA_URI_BYTES = 1_398_104
ALLOWED_METADATA_HOSTS = {'ipfs.io'}


def normalize_ipfs_url(url: str) -> str:
    if url.startswith('ipfs://'):
        return url.replace('ipfs://', 'https://ipfs.io/ipfs/', 1)
    return url


def validate_public_metadata_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('Unsupported metadata URL')
    if parsed.hostname.lower() not in ALLOWED_METADATA_HOSTS:
        raise ValueError('Metadata host is not allowed')
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Metadata URL is not publicly reachable')
    return url


@lru_cache(maxsize=256)
def load_token_metadata(token_uri: str) -> dict:
    token_uri = normalize_ipfs_url(token_uri)
    if not token_uri:
        return {}
    try:
        if token_uri.startswith('data:application/json;base64,'):
            payload = token_uri.split(',', 1)[1]
            if len(payload) > MAX_DATA_URI_BYTES:
                raise ValueError('Metadata data URI is too large')
            return json.loads(base64.b64decode(payload).decode('utf-8'))
        response = requests.get(
            validate_public_metadata_url(token_uri),
            timeout=(3, 10),
            allow_redirects=False,
            stream=True,
            headers={'Accept': 'application/json'},
        )
        response.raise_for_status()
        if not response.headers.get('Content-Type', '').startswith('application/json'):
            raise ValueError('Metadata response is not JSON')
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_METADATA_BYTES:
            raise ValueError('Metadata response is too large')
        chunks = []
        size = 0
        for chunk in response.iter_content(chunk_size=16_384):
            size += len(chunk)
            if size > MAX_METADATA_BYTES:
                raise ValueError('Metadata response is too large')
            chunks.append(chunk)
        return json.loads(b''.join(chunks).decode('utf-8'))
    except (OSError, requests.RequestException, ValueError, UnicodeDecodeError):
        return {}
