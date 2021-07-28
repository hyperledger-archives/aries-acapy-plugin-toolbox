from typing import Any, Dict, Optional, Union

import httpx

from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.wait_for_message_response_wait_for_message_wait_for_connection_id_get import (
    WaitForMessageResponseWaitForMessageWaitForConnectionIdGet,
)
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    client: Client,
    connection_id: str,
    thid: Union[Unset, str] = UNSET,
    msg_type: Union[Unset, str] = UNSET,
) -> Dict[str, Any]:
    url = "{}/wait-for/{connection_id}".format(client.base_url, connection_id=connection_id)

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    params: Dict[str, Any] = {
        "thid": thid,
        "msg_type": msg_type,
    }
    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "params": params,
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[Union[HTTPValidationError, WaitForMessageResponseWaitForMessageWaitForConnectionIdGet]]:
    if response.status_code == 200:
        response_200 = WaitForMessageResponseWaitForMessageWaitForConnectionIdGet.from_dict(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[Union[HTTPValidationError, WaitForMessageResponseWaitForMessageWaitForConnectionIdGet]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
    connection_id: str,
    thid: Union[Unset, str] = UNSET,
    msg_type: Union[Unset, str] = UNSET,
) -> Response[Union[HTTPValidationError, WaitForMessageResponseWaitForMessageWaitForConnectionIdGet]]:
    kwargs = _get_kwargs(
        client=client,
        connection_id=connection_id,
        thid=thid,
        msg_type=msg_type,
    )

    response = httpx.get(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    connection_id: str,
    thid: Union[Unset, str] = UNSET,
    msg_type: Union[Unset, str] = UNSET,
) -> Optional[Union[HTTPValidationError, WaitForMessageResponseWaitForMessageWaitForConnectionIdGet]]:
    """Wait for a message matching criteria."""

    return sync_detailed(
        client=client,
        connection_id=connection_id,
        thid=thid,
        msg_type=msg_type,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    connection_id: str,
    thid: Union[Unset, str] = UNSET,
    msg_type: Union[Unset, str] = UNSET,
) -> Response[Union[HTTPValidationError, WaitForMessageResponseWaitForMessageWaitForConnectionIdGet]]:
    kwargs = _get_kwargs(
        client=client,
        connection_id=connection_id,
        thid=thid,
        msg_type=msg_type,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.get(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    connection_id: str,
    thid: Union[Unset, str] = UNSET,
    msg_type: Union[Unset, str] = UNSET,
) -> Optional[Union[HTTPValidationError, WaitForMessageResponseWaitForMessageWaitForConnectionIdGet]]:
    """Wait for a message matching criteria."""

    return (
        await asyncio_detailed(
            client=client,
            connection_id=connection_id,
            thid=thid,
            msg_type=msg_type,
        )
    ).parsed
