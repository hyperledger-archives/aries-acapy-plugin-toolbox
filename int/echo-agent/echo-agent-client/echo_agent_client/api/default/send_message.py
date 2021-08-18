from typing import Any, Dict, Optional, Union

import httpx

from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.send_message_message import SendMessageMessage
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    connection_id: str,
    json_body: SendMessageMessage,
) -> Dict[str, Any]:
    url = "{}/send/{connection_id}".format(client.base_url, connection_id=connection_id)

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    json_json_body = json_body.to_dict()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
        "json": json_json_body,
    }


def _parse_response(*, response: httpx.Response) -> Optional[Union[Any, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = response.json()

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    return None


def _build_response(*, response: httpx.Response) -> Response[Union[Any, HTTPValidationError]]:
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
    json_body: SendMessageMessage,
) -> Response[Union[Any, HTTPValidationError]]:
    kwargs = _get_kwargs(
        client=client,
        connection_id=connection_id,
        json_body=json_body,
    )

    response = httpx.post(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    connection_id: str,
    json_body: SendMessageMessage,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Send a message to connection identified by did."""

    return sync_detailed(
        client=client,
        connection_id=connection_id,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    connection_id: str,
    json_body: SendMessageMessage,
) -> Response[Union[Any, HTTPValidationError]]:
    kwargs = _get_kwargs(
        client=client,
        connection_id=connection_id,
        json_body=json_body,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.post(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    connection_id: str,
    json_body: SendMessageMessage,
) -> Optional[Union[Any, HTTPValidationError]]:
    """Send a message to connection identified by did."""

    return (
        await asyncio_detailed(
            client=client,
            connection_id=connection_id,
            json_body=json_body,
        )
    ).parsed
