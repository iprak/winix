"""Winix cloud authentication and session helpers."""

from __future__ import annotations

from binascii import crc32
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from jose import jwt
from warrant_lite import WarrantLite

COGNITO_APP_CLIENT_ID = "5rjk59c5tt7k9g8gpj0vd2qfg9"
COGNITO_USER_POOL_ID = "us-east-1_Ofd50EosD"
COGNITO_REGION = "us-east-1"
IDENTITY_POOL_ID = "us-east-1:84008e15-d6af-4698-8646-66d05c1abe8b"
MOBILE_APP_VERSION = "1.5.7"
MOBILE_MODEL = "SM-G988B"
COGNITO_LOGINS_PROVIDER = (
    f"cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
)


@dataclass
class WinixAuthResponse:
    """Authentication data persisted by the integration."""

    user_id: str
    access_token: str
    refresh_token: str
    id_token: str
    identity_id: str | None = None
    expires_at: float | None = None

    def __post_init__(self) -> None:
        """Populate expiration when it is missing."""
        if self.expires_at is None and self.access_token:
            self.expires_at = _token_expiration(self.access_token)

    def as_dict(self) -> dict[str, Any]:
        """Convert the dataclass into a JSON-serializable dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> WinixAuthResponse | None:
        """Create an auth response from stored dict data."""
        if not data:
            return None
        return cls(**data)


def login(username: str, password: str) -> WinixAuthResponse:
    """Authenticate against the current Winix Cognito user pool."""
    client = _cognito_idp_client()
    warrant = WarrantLite(
        username=username,
        password=password,
        pool_id=COGNITO_USER_POOL_ID,
        client_id=COGNITO_APP_CLIENT_ID,
        client=client,
    )
    response = warrant.authenticate_user()
    auth_result = response["AuthenticationResult"]
    access_token = auth_result["AccessToken"]
    return WinixAuthResponse(
        user_id=jwt.get_unverified_claims(access_token)["sub"],
        access_token=access_token,
        refresh_token=auth_result["RefreshToken"],
        id_token=auth_result["IdToken"],
        expires_at=_expires_at(auth_result.get("ExpiresIn"), access_token),
    )


def refresh(user_id: str, refresh_token: str) -> WinixAuthResponse:
    """Refresh an existing Winix session."""
    response = _cognito_idp_client().initiate_auth(
        ClientId=COGNITO_APP_CLIENT_ID,
        AuthFlow="REFRESH_TOKEN",
        AuthParameters={
            "REFRESH_TOKEN": refresh_token,
        },
    )
    auth_result = response["AuthenticationResult"]
    access_token = auth_result["AccessToken"]
    return WinixAuthResponse(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=auth_result.get("IdToken", ""),
        expires_at=_expires_at(auth_result.get("ExpiresIn"), access_token),
    )


def resolve_identity_id(id_token: str) -> str:
    """Resolve the Cognito identity pool id needed by the Winix device API."""
    response = _cognito_identity_client().get_id(
        IdentityPoolId=IDENTITY_POOL_ID,
        Logins={COGNITO_LOGINS_PROVIDER: id_token},
    )
    identity_id = response.get("IdentityId")
    if not identity_id:
        raise RuntimeError("Cognito GetId returned no IdentityId")
    return identity_id


def generate_uuid(access_token: str) -> str:
    """Construct the fake Android secure id expected by Winix."""
    if not access_token:
        return ""

    user_id_bytes = jwt.get_unverified_claims(access_token)["sub"].encode()
    part1 = crc32(b"github.com/regaw-leinad/winix-api" + user_id_bytes)
    part2 = crc32(b"HGF" + user_id_bytes)
    return f"{part1:08x}{part2:08x}"


def _cognito_idp_client():
    """Return a Cognito IDP client without AWS credentials."""
    return boto3.client(
        "cognito-idp",
        region_name=COGNITO_REGION,
        config=Config(signature_version=UNSIGNED),
    )


def _cognito_identity_client():
    """Return a Cognito Identity client without AWS credentials."""
    return boto3.client(
        "cognito-identity",
        region_name=COGNITO_REGION,
        config=Config(signature_version=UNSIGNED),
    )


def _expires_at(expires_in: int | None, access_token: str) -> float:
    """Compute token expiration from the login response or JWT fallback."""
    if expires_in is not None:
        return (
            datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        ).timestamp()
    return _token_expiration(access_token)


def _token_expiration(access_token: str) -> float:
    """Read expiration from JWT claims and fall back to one hour."""
    claims = jwt.get_unverified_claims(access_token)
    exp = claims.get("exp")
    if exp is not None:
        return float(exp)
    return (datetime.now(timezone.utc) + timedelta(hours=1)).timestamp()
