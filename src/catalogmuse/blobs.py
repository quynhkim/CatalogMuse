"""Store job images in S3 and hand out a fresh download URL.

The agents still read the local file while a step is running. When
CATALOGMUSE_S3_BUCKET is set, each saved image is copied to
jobs/{job_id}/{name}. The object stays in the bucket. The URL on a job is
a presigned GET, signed again every time the job is read.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_CLIENT: Any = None
_URL_SECONDS = 12 * 60 * 60


def bucket() -> str:
    return os.environ.get("CATALOGMUSE_S3_BUCKET", "").strip()


def object_key(job_id: str, name: str) -> str:
    prefix = os.environ.get("CATALOGMUSE_S3_PREFIX", "jobs").strip("/")
    safe = Path(name).name
    return f"{prefix}/{job_id}/{safe}" if prefix else f"{job_id}/{safe}"


def put_file(job_id: str, path: Path) -> None:
    name = bucket()
    if not name:
        return
    content = "image/png" if path.suffix == ".png" else "image/jpeg"
    client().upload_file(
        str(path),
        name,
        object_key(job_id, path.name),
        ExtraArgs={"ContentType": content},
    )


def signed_url(job_id: str, name: str) -> str | None:
    store = bucket()
    if not store:
        return None
    return client().generate_presigned_url(
        "get_object",
        Params={"Bucket": store, "Key": object_key(job_id, name)},
        ExpiresIn=_URL_SECONDS,
    )


def file_url(public_url: str, job_id: str, name: str) -> str:
    signed = signed_url(job_id, name)
    if signed:
        return signed
    url = f"{public_url}/v1/jobs/{job_id}/files/{name}"
    version = _file_version(job_id, name)
    if version:
        url += f"?v={version}"
    return url


def _file_version(job_id: str, name: str) -> str:
    path = Path(os.environ.get("CATALOGMUSE_DATA", "data")) / "jobs" / job_id / Path(name).name
    try:
        return str(path.stat().st_mtime_ns)
    except OSError:
        return ""


def client() -> Any:
    global _CLIENT
    if _CLIENT is None:
        from botocore.config import Config

        region = os.environ.get("AWS_REGION", "us-east-2")
        # The global s3.amazonaws.com host rejects a us-east-2 signature.
        _CLIENT = _session(region).client(
            "s3",
            region_name=region,
            endpoint_url=f"https://s3.{region}.amazonaws.com",
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )
    return _CLIENT


def _session(region: str) -> Any:
    import boto3

    role = os.environ.get("AWS_ROLE_ARN", "").strip()
    token_file = os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE", "").strip()
    if not role or not token_file:
        return boto3.Session()

    from datetime import datetime

    from botocore.credentials import AssumeRoleWithWebIdentityCredentialFetcher, DeferredRefreshableCredentials
    from botocore.session import Session
    from dateutil.tz import tzlocal

    core = Session()
    sts = Session()

    def client_creator(service_name: str, **kwargs: Any) -> Any:
        return sts.create_client(service_name, region_name=region, **kwargs)

    fetcher = AssumeRoleWithWebIdentityCredentialFetcher(
        client_creator=client_creator,
        web_identity_token_loader=lambda: Path(token_file).read_text(),
        role_arn=role,
        extra_args={"RoleSessionName": "catalogmuse-engine", "DurationSeconds": _URL_SECONDS},
    )
    core._credentials = DeferredRefreshableCredentials(
        method="assume-role-with-web-identity",
        refresh_using=fetcher.fetch_credentials,
        time_fetcher=lambda: datetime.now(tzlocal()),
    )
    core.set_config_variable("region", region)
    return boto3.Session(botocore_session=core)
