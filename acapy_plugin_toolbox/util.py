"""Utility functions."""

# pylint: disable=too-few-public-methods

import sys
from typing import Type, Union, Tuple, cast
import logging
import functools
import json
from datetime import datetime, timezone
from dateutil.parser import isoparse

from aries_cloudagent.connections.models.conn_record import ConnRecord
from aries_cloudagent.protocols.connections.v1_0.manager import ConnectionManager
from aries_cloudagent.storage.base import BaseStorage
from aries_cloudagent.storage.error import StorageNotFoundError
from aries_cloudagent.core.profile import ProfileSession, Profile
from aries_cloudagent.messaging.agent_message import AgentMessage, AgentMessageSchema
from aries_cloudagent.messaging.base_handler import (
    BaseHandler,
    BaseResponder,
    RequestContext,
)
from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport

LOGGER = logging.getLogger(__name__)


def timestamp_utc_iso(timespec: str = "seconds") -> str:
    """Timestamp in UTC in ISO 8601 format.

    See https://docs.python.org/3.7/library/datetime.html for more details.

    Args:
        timespec (str): One of auto, hours, minutes, seconds, milliseconds,
            microseconds. Specifies the precision of the output timestamp.
    """
    return (
        datetime.utcnow()
        .replace(tzinfo=timezone.utc)
        .isoformat(timespec=timespec)
        .replace("+00:00", "Z")
    )


def datetime_from_iso(timestamp: str) -> datetime:
    """Return a datetime from ISO 8601 formatted timestamp."""
    timestamp = timestamp.replace(" ", "T", 1)
    return isoparse(timestamp)


def require_role(role):
    """
    Verify that the current connection has a given role.

    Verify that the current connection has a given role; otherwise, send a
    problem report.
    """

    def _require_role(func):
        @functools.wraps(func)
        async def _wrapped(*args):
            context, *_ = [arg for arg in args if isinstance(arg, RequestContext)]
            responder, *_ = [arg for arg in args if isinstance(arg, BaseResponder)]
            if context.connection_record:
                session = await context.session()
                group = await context.connection_record.metadata_get(session, "group")
                if group == role:
                    return await func(*args)

            report = ProblemReport(
                description={
                    "en": "This connection is not authorized to perform"
                    " the requested action."
                },
                who_retries="none",
            )
            report.assign_thread_from(context.message)
            await responder.send_reply(report)

        return _wrapped

    return _require_role


def admin_only(func):
    """Require admin role."""
    return require_role("admin")(func)


def log_handling(func):
    """Logging decorator for handlers."""
    logger = logging.getLogger(func.__module__)

    @functools.wraps(func)
    async def _logged(*args):
        context, *_ = [arg for arg in args if isinstance(arg, RequestContext)]
        logger.debug("%s called with message: %s", func.__qualname__, context.message)
        return await func(*args)

    return _logged


def expand_message_class(cls):
    """Class decorator for removing boilerplate of AgentMessages."""
    # pylint: disable=protected-access

    if not hasattr(cls, "message_type"):
        raise ValueError(
            "Expected value message_type not found on class {}".format(cls.__name__)
        )
    if not hasattr(cls, "Fields") and not hasattr(cls, "fields_from"):
        raise ValueError(
            "Class {} must have nested class Fields or schema defining"
            "expected fields".format(cls.__name__)
        )

    cls.Meta = type(
        cls.__name__ + ".Meta",
        (),
        {
            "__module__": cls.__module__,
            "message_type": cls.message_type,
            "schema_class": cls.__name__ + ".Schema",
        },
    )

    fields = {}
    if hasattr(cls, "Fields"):
        fields.update(
            {
                var: getattr(cls.Fields, var)
                for var in vars(cls.Fields)
                if not var.startswith("__")
            }
        )
    if hasattr(cls, "fields_from"):
        fields.update(cls.fields_from._declared_fields)

    cls.Schema = type(
        cls.__name__ + ".Schema",
        (AgentMessageSchema,),
        {"__module__": cls.__module__, **fields},
    )
    cls.__slots__ = list(fields.keys())
    cls.Schema.Meta = type(
        cls.Schema.__name__ + ".Meta",
        (),
        {"__module__": cls.__module__, "model_class": cls},
    )
    cls._get_schema_class = lambda: cls.Schema

    if hasattr(cls, "protocol") and cls.protocol:
        cls.Meta.message_type = "{}/{}".format(cls.protocol, cls.message_type)
        cls._type = property(fget=lambda self: self.Meta.message_type)

    if hasattr(cls, "handle"):
        cls.Handler = handler(cls.handle)
        cls._get_handler_class = lambda: cls.Handler
    elif hasattr(cls, "handler"):
        cls.Meta.handler_class = cls.handler
    else:
        cls.Handler = PassHandler
        cls._get_handler_class = lambda: cls.Handler
        cls.Meta.handler_class = PassHandler.load_path

    return cls


def expand_model_class(cls):
    """Class decorator for removing boilerplate from BaseModels."""
    if not hasattr(cls, "Fields") and not hasattr(cls, "fields_from"):
        raise ValueError(
            "Class {} must have nested class Fields or schema defining"
            "expected fields".format(cls.__name__)
        )

    if hasattr(cls, "Meta") and cls.Meta != BaseModel.Meta:
        cls.Meta.schema_class = cls.__name__ + ".Schema"
    else:
        cls.Meta = type(
            cls.__name__ + ".Meta",
            (),
            {"__module__": cls.__module__, "schema_class": cls.__name__ + ".Schema"},
        )

    fields = {}
    if hasattr(cls, "Fields"):
        fields.update({var: getattr(cls.Fields, var) for var in vars(cls.Fields)})
    if hasattr(cls, "fields_from"):
        fields.update(cls.fields_from._declared_fields)

    cls.Schema = type(
        cls.__name__ + ".Schema",
        (BaseModelSchema,),
        {"__module__": cls.__module__, **fields},
    )
    cls.__slots__ = list(fields.keys())
    cls.Schema.Meta = type(
        cls.Schema.__name__ + ".Meta",
        (),
        {"__module__": cls.__module__, "model_class": cls},
    )

    if hasattr(cls, "unknown"):
        cls.Schema.Meta.unknown = cls.unknown

    cls._get_schema_class = lambda: cls.Schema

    return cls


def handler(func):
    """Function decorator for creating Python handler classes."""

    class Handler(BaseHandler):
        __doc__ = func.__doc__
        __name__ = func.__name__
        __module__ = func.__module__

        @property
        @classmethod
        def load_path(cls):
            """Return load path for this handler."""
            return f"{cls.__module__}.{cls.__name__}"

        async def handle(self, context: RequestContext, responder: BaseResponder):
            """Handle message."""
            return await func(context.message, context, responder)

    return Handler


def generic_init(instance, **kwargs):
    """Initialize from kwargs into slots."""
    for slot in instance.__slots__:
        setattr(instance, slot, kwargs.get(slot))
        if slot in kwargs:
            del kwargs[slot]
    super(type(instance), instance).__init__(**kwargs)


def with_generic_init(cls):
    """Class decorator for adding generic init method."""
    cls.__init__ = generic_init
    return cls


def generate_model_schema(  # pylint: disable=protected-access
    name: str, handler: str, msg_type: str, schema: dict, *, init: callable = None
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
    elif hasattr(schema, "_declared_fields"):
        slots = list(schema._declared_fields.keys())
        schema_dict = schema._declared_fields
    else:
        raise TypeError("Schema must be dict or class defining _declared_fields")

    class Model(AgentMessage):
        """Generated Model."""

        __slots__ = slots
        __qualname__ = name
        __name__ = name
        __module__ = sys._getframe(2).f_globals["__name__"]
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

            __qualname__ = name + ".Meta"
            handler_class = handler
            message_type = msg_type
            schema_class = name + "Schema"

    class Schema(AgentMessageSchema):
        """Generated Schema."""

        __qualname__ = name + "Schema"
        __name__ = name + "Schema"
        __module__ = sys._getframe(2).f_globals["__name__"]

        class Meta:
            """Generated Schema Meta."""

            __qualname__ = name + "Schema.Meta"
            model_class = Model

    Schema._declared_fields.update(schema_dict)

    return Model, Schema


class PassHandler(BaseHandler):
    """Handler for messages requiring no handling."""

    @property
    @classmethod
    def load_path(cls):
        """Return the load path of this handler."""
        return f"{cls.__module__}.{cls.__name__}"

    async def handle(self, context: RequestContext, _responder):
        """Handle messages require no handling."""
        # pylint: disable=protected-access
        LOGGER.info("Pass: Not handling message of type %s", context.message._type)


async def admin_connections(session: ProfileSession):
    """Return admin connections."""
    storage = session.inject(BaseStorage)
    admin_metadata_records = [
        record
        for record in await storage.find_all_records(
            ConnRecord.RECORD_TYPE_METADATA, {"key": "group"}
        )
        or []
        if json.loads(record.value) == "admin"
    ]
    admins = []
    for record in admin_metadata_records:
        try:
            admin = await ConnRecord.retrieve_by_id(
                session, record.tags["connection_id"]
            )
            admins.append(admin)
        except StorageNotFoundError:
            # Clean up dangling metadata records of admins
            LOGGER.debug("Deleteing dangling admin metadata record: %s", admins)
            await storage.delete_record(record)

    LOGGER.info("Discovered admins: %s", admins)
    return admins


async def send_to_admins(
    profile: Profile,
    message: AgentMessage,
    responder: BaseResponder,
    to_session_only: bool = False,
):
    """Send a message to all admin connections."""
    LOGGER.info("Sending message to admins: %s", message.serialize())
    async with profile.session() as session:
        admins = await admin_connections(session)
    admins = list(filter(lambda admin: admin.state == "active", admins))
    connection_mgr = ConnectionManager(profile)
    admin_targets = [
        (admin, target)
        for admin in admins
        for target in await connection_mgr.get_connection_targets(connection=admin)
    ]

    for connection, target in admin_targets:
        if not to_session_only:
            await responder.send(
                message,
                connection_id=connection.connection_id,
                reply_to_verkey=target.recipient_keys[0],
                reply_from_verkey=target.sender_key,
            )
        else:
            await responder.send(
                message,
                reply_to_verkey=target.recipient_keys[0],
                reply_from_verkey=target.sender_key,
                to_session_only=to_session_only,
            )


class InvalidConnection(Exception):
    """Raised if no connection or connection is not ready."""


async def get_connection(session: ProfileSession, connection_id: str) -> ConnRecord:
    """Get connection record or raise error if not found or conn is not ready."""
    try:
        conn_record = await ConnRecord.retrieve_by_id(session, connection_id)
        conn_record = cast(ConnRecord, conn_record)
        if not conn_record.is_ready:
            raise InvalidConnection("Connection is not ready.")

        return conn_record
    except StorageNotFoundError as err:
        raise InvalidConnection("Connection not found.") from err


class ExceptionReporter:
    def __init__(
        self,
        responder: BaseResponder,
        exception: Union[Type[Exception], Tuple[Type[Exception], ...]],
        original_message: AgentMessage = None,
    ):
        self.responder = responder
        self.exception = exception
        self.original_message = original_message

    async def __aenter__(self):
        return self

    async def __aexit__(self, err_type, err_value, err_traceback):
        """Exit the context manager."""
        if isinstance(err_value, self.exception):
            report = ProblemReport(description={"en": str(err_value)})
            if self.original_message:
                report.assign_thread_from(self.original_message)
            await self.responder.send_reply(report)
