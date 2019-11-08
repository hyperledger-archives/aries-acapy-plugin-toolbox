"""More condensed method of generating a message and its schema."""

import sys
import logging
import functools

import marshmallow

from ..agent_message import AgentMessage, AgentMessageSchema
from ..base_handler import BaseHandler, BaseResponder, RequestContext
from ..problem_report.message import ProblemReport

# pylint: disable=invalid-name
# pylint: disable=too-few-public-methods


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
                responder: BaseResponder):

            if not context.connection_record \
                    or context.connection_record.their_role != role:
                report = ProblemReport(
                    explain_ltxt='This connection is not authorized to perform '
                                 'the requested action.',
                    who_retries='none'
                )
                report.assign_thread_from(context.message)
                await responder.send_reply(report)
                return

            return await func(handler, context, responder)
        return _wrapped
    return _require_role


def admin_only(func):
    """Require admin role."""
    return require_role('admin')(func)


def generic_init(instance, **kwargs):
    """Initialize from kwargs into slots."""
    for slot in instance.__slots__:
        setattr(instance, slot, kwargs.get(slot))
        if slot in kwargs:
            del kwargs[slot]
    super(type(instance), instance).__init__(**kwargs)


def generate_model_schema(
        name: str,
        handler: str,
        msg_type: str,
        schema: dict
        ):
    """
    Generate a Message model class and schema class programmatically.

    The following would result in a class named XYZ inheriting from AgentMessage
    and XYZSchema inheriting from AgentMessageSchema.

    XYZ, XYZSchema = generate_model_schema(
        'XYZ',
        'aries_cludagent.admin.handlers.XYZHandler',
        '{}/xyz'.format(PROTOCOL),
        {}
    )

    The attributes of XYZ are determined by schema_dict's keys. The actual
    schema of XYZSchema is defined by the field-value combinations of
    schema_dict, similar to marshmallow's Schema.from_dict() (can't actually
    use that here as the model_class must be set in the Meta inner-class of
    AgentMessageSchema's).
    """
    if isinstance(schema, dict):
        slots = list(schema.keys())
        schema_dict = schema
    elif hasattr(schema, '_declared_fields'):
        slots = list(schema._declared_fields.keys())
        schema_dict = schema._declared_fields
    else:
        raise TypeError('Schema must be dict or class defining _declared_fields')

    Model = type(
        name,
        (AgentMessage,),
        {
            'Meta': type(
                'Meta', (), {
                    '__qualname__': name + '.Meta',
                    'handler_class': handler,
                    'message_type': msg_type,
                    'schema_class': name + 'Schema',
                }
            ),
            '__init__': generic_init,
            '__slots__': slots
        }
    )
    Model.__module__ = sys._getframe(1).f_globals['__name__']
    Schema = type(
        name + 'Schema',
        (AgentMessageSchema,),
        {
            'Meta': type(
                'Meta', (), {
                    '__qualname__': name + 'Schema.Meta',
                    'model_class': Model,
                }
            ),
            **schema_dict
        }
    )
    Schema.__module__ = sys._getframe(1).f_globals['__name__']
    return Model, Schema


class PassHandler(BaseHandler):
    """Handler for messages requiring no handling."""

    async def handle(self, context: RequestContext, _responder):
        """Handle messages require no handling."""
        logger = logging.getLogger(__name__)
        logger.debug(
            "Pass: Not handling message of type %s",
            context.message._type
        )
