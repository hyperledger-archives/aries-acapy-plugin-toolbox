from typing import Any, Dict, List, Optional, Union

import httpx

from ...client import Client
from ...models.http_validation_error import HTTPValidationError
from ...models.retrieve_messages_response_200_item import RetrieveMessagesResponse200Item
from ...types import Response


def _get_kwargs(
    *,
    client: Client,
    connection_id: str,
) -> Dict[str, Any]:
    url = "{}/retrieve/{connection_id}".format(client.base_url, connection_id=connection_id)

    headers: Dict[str, Any] = client.get_headers()
    cookies: Dict[str, Any] = client.get_cookies()

    return {
        "url": url,
        "headers": headers,
        "cookies": cookies,
        "timeout": client.get_timeout(),
    }


def _parse_response(
    *, response: httpx.Response
) -> Optional[Union[HTTPValidationError, List[RetrieveMessagesResponse200Item]]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = RetrieveMessagesResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    return None


def _build_response(
    *, response: httpx.Response
) -> Response[Union[HTTPValidationError, List[RetrieveMessagesResponse200Item]]]:
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
) -> Response[Union[HTTPValidationError, List[RetrieveMessagesResponse200Item]]]:
    kwargs = _get_kwargs(
        client=client,
        connection_id=connection_id,
    )

    response = httpx.get(
        **kwargs,
    )

    return _build_response(response=response)


def sync(
    *,
    client: Client,
    connection_id: str,
) -> Optional[Union[HTTPValidationError, List[RetrieveMessagesResponse200Item]]]:
    """Retrieve all received messages for recipient key."""

    return sync_detailed(
        client=client,
        connection_id=connection_id,
    ).parsed


async def asyncio_detailed(
    *,
    client: Client,
    connection_id: str,
) -> Response[Union[HTTPValidationError, List[RetrieveMessagesResponse200Item]]]:
    kwargs = _get_kwargs(
        client=client,
        connection_id=connection_id,
    )

    async with httpx.AsyncClient() as _client:
        response = await _client.get(**kwargs)

    return _build_response(response=response)


async def asyncio(
    *,
    client: Client,
    connection_id: str,
) -> Optional[Union[HTTPValidationError, List[RetrieveMessagesResponse200Item]]]:
    """Retrieve all received messages for recipient key."""

    return (
        await asyncio_detailed(
            client=client,
            connection_id=connection_id,
        )
    ).parsed
