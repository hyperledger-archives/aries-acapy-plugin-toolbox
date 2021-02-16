"""Utility functions."""

# pylint: disable=too-few-public-methods

import sys
import logging
import functools
import json
from datetime import datetime, timezone
from dateutil.parser import isoparse

from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.core.profile import ProfileSession
from aries_cloudagent.messaging.agent_message import (
    AgentMessage, AgentMessageSchema
)
from aries_cloudagent.messaging.base_handler import (
    BaseHandler, BaseResponder, RequestContext
)
from aries_cloudagent.protocols.problem_report.v1_0.message import (
    ProblemReport
)


def timestamp_utc_iso(timespec: str = 'seconds') -> str:
    """Timestamp in UTC in ISO 8601 format.

    See https://docs.python.org/3.7/library/datetime.html for more details.

    Args:
        timespec (str): One of auto, hours, minutes, seconds, milliseconds,
            microseconds. Specifies the precision of the output timestamp.
    """
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(
        timespec=timespec
    ).replace('+00:00', 'Z')


def datetime_from_iso(timestamp: str) -> datetime:
    """Return a datetime from ISO 8601 formatted timestamp."""
    timestamp = timestamp.replace(' ', 'T', 1)
    return isoparse(timestamp)


def require_role(role):
    """
    Verify that the current connection has a given role.

    Verify that the current connection has a given role; otherwise, send a
    problem report.
    """
    def _require_role(func):
        @functools.wraps(func)
        async def _wrapped(
            handler,
            context: RequestContext,
            responder: BaseResponder
        ):
            if context.connection_record:
                session = await context.session()
                group = await context.connection_record.metadata_get(
                    session, 'group'
                )
                if group == role:
                    return await func(handler, context, responder)

            report = ProblemReport(
                explain_ltxt='This connection is not authorized to perform'
                             ' the requested action.',
                who_retries='none'
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)

        return _wrapped
    return _require_role


def admin_only(func):
    """Require admin role."""
    return require_role('admin')(func)


def expand_message_class(cls):
    """Class decorator for removing boilerplate of AgentMessages."""
    if not hasattr(cls, "message_type"):
        raise ValueError(
            "Expected value message_type not found on class {}"
            .format(cls.__name__)
        )
    if not hasattr(cls, "handler"):
        raise ValueError(
            "Expected value handler value not found on class {}"
            .format(cls.__name__)
        )
    if not hasattr(cls, "Fields") and not hasattr(cls, "fields_from"):
        raise ValueError(
            "Class {} must have nested class Fields or schema defining expected fields"
            .format(cls.__name__)
        )

    cls.Meta = type(cls.__name__ + ".Meta", (), {
        "__module__": cls.__module__,
        "handler_class": cls.handler,
        "message_type": cls.message_type,
        "schema_class": cls.__name__ + ".Schema"
    })

    fields = {}
    if hasattr(cls, "Fields"):
        fields.update({var: getattr(cls.Fields, var) for var in vars(cls.Fields)})
    if hasattr(cls, "fields_from"):
        fields.update(cls.fields_from._declared_fields)

    cls.Schema = type(cls.__name__ + ".Schema", (AgentMessageSchema,), {
        "__module__": cls.__module__,
        **fields
    })
    cls.Schema.Meta = type(cls.Schema.__name__ + ".Meta", (), {
        "__module__": cls.__module__,
        "model_class": cls
    })
    cls._get_schema_class = lambda: cls.Schema

    if hasattr(cls, "protocol") and cls.protocol:
        cls.Meta.message_type = "{}/{}".format(cls.protocol, cls.message_type)
        cls._type = property(fget=lambda self: self.Meta.message_type)

    return cls


def generic_init(instance, **kwargs):
    """Initialize from kwargs into slots."""
    for slot in instance.__slots__:
        setattr(instance, slot, kwargs.get(slot))
        if slot in kwargs:
            del kwargs[slot]
    super(type(instance), instance).__init__(**kwargs)


def generate_model_schema(  # pylint: disable=protected-access
        name: str,
        handler: str,
        msg_type: str,
        schema: dict,
        *,
        init: callable = None
        ):
    """Generate a Message model class and schema class programmatically.

    The following would result in a class named XYZ inheriting from
    AgentMessage and XYZSchema inheriting from AgentMessageSchema.

    XYZ, XYZSchema = generate_model_schema(
        name='XYZ',
        handler='aries_cloudagent.admin.handlers.XYZHandler',
        msg_type='{}/xyz'.format(PROTOCOL),
        schema={}
    )

    The attributes of XYZ are determined by schema's keys. The actual
    schema of XYZSchema is defined by the field-value combinations of
    schema_dict, similar to marshmallow's Schema.from_dict() (can't actually
    use that here as the model_class must be set in the Meta inner-class of
    AgentMessageSchemas).
    """
    if isinstance(schema, dict):
        slots = list(schema.keys())
        schema_dict = schema
    elif hasattr(schema, '_declared_fields'):
        slots = list(schema._declared_fields.keys())
        schema_dict = schema._declared_fields
    else:
        raise TypeError(
            'Schema must be dict or class defining _declared_fields'
        )

    class Model(AgentMessage):
        """Generated Model."""
        __slots__ = slots
        __qualname__ = name
        __name__ = name
        __module__ = sys._getframe(2).f_globals['__name__']
        __init__ = init if init else generic_init

        @property
        def _type(self):
            """
            Override default _type method to ensure incorrect DIDComm Prefix
            is not prepended to all our message types.
            """
            return self.Meta.message_type

        class Meta:
            """Generated Meta."""
            __qualname__ = name + '.Meta'
            handler_class = handler
            message_type = msg_type
            schema_class = name + 'Schema'

    class Schema(AgentMessageSchema):
        """Generated Schema."""
        __qualname__ = name + 'Schema'
        __name__ = name + 'Schema'
        __module__ = sys._getframe(2).f_globals['__name__']

        class Meta:
            """Generated Schema Meta."""
            __qualname__ = name + 'Schema.Meta'
            model_class = Model

    Schema._declared_fields.update(schema_dict)

    return Model, Schema


class PassHandler(BaseHandler):
    """Handler for messages requiring no handling."""

    async def handle(self, context: RequestContext, _responder):
        """Handle messages require no handling."""
        # pylint: disable=protected-access
        logger = logging.getLogger(__name__)
        logger.debug(
            "Pass: Not handling message of type %s",
            context.message._type
        )


async def admin_connections(session: ProfileSession):
    """Return admin connections."""
    storage = session.inject(BaseStorage)
    admin_ids = map(
        lambda record: record.tags['connection_id'],
        filter(
            lambda record: json.loads(record.value) == 'admin',
            await storage.find_all_records(
                ConnRecord.RECORD_TYPE_METADATA, {'key': 'group'}
            )
        )
    )
    admins = [
        await ConnRecord.retrieve_by_id(session, id)
        for id in admin_ids
    ]
    return admins


async def send_to_admins(
    session: ProfileSession,
    message: AgentMessage,
    responder: BaseResponder,
    to_session_only: bool = False
):
    """Send a message to all admin connections."""
    admins = await admin_connections(session)
    admins = list(filter(lambda admin: admin.state == 'active', admins))
    connection_mgr = ConnectionManager(session)
    admin_verkeys = [
        target.recipient_keys[0]
        for admin in admins
        for target in await connection_mgr.get_connection_targets(
            connection=admin
        )
    ]

    for verkey in admin_verkeys:
        await responder.send(
            message,
            reply_to_verkey=verkey,
            to_session_only=to_session_only
        )
