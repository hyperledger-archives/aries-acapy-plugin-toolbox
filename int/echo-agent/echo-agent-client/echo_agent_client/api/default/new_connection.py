from typing import Any, Dict, Optional, Union

import httpx

from ...client import Client
from ...models.connection import Connection
from ...models.http_validation_error import HTTPValidationError
from ...models.new_connection import NewConnection
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    json_body: NewConnection,
) -> Dict[str, Any]:
    url = "{}/connection".format(client.base_url)

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


def _parse_response(*, response: httpx.Response) -> Optional[Union[Connection, HTTPValidationError]]:
    if response.status_code == 200:
        response_200 = Connection.from_dict(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    return None


def _build_response(*, response: httpx.Response) -> Response[Union[Connection, HTTPValidationError]]:
    return Response(
        status_code=response.status_code,
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(response=response),
    )


def sync_detailed(
    *,
    client: Client,
    json_body: NewConnection,
) -> Response[Union[Connection, HTTPValidationError]]:
    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    response = httpx.post(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    json_body: NewConnection,
) -> Optional[Union[Connection, HTTPValidationError]]:
    """Create a new static connection."""

    return sync_detailed(
        client=client,
        json_body=json_body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    json_body: NewConnection,
) -> Response[Union[Connection, HTTPValidationError]]:
    kwargs = _get_kwargs(
        client=client,
        json_body=json_body,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.post(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    json_body: NewConnection,
) -> Optional[Union[Connection, HTTPValidationError]]:
    """Create a new static connection."""

    return (
        await asyncio_detailed(
            client=client,
            json_body=json_body,
        )
    ).parsed
