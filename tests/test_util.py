"""Test utilities."""

import pytest
from aries_cloudagent.messaging.agent_message import AgentMessage, AgentMessageSchema
from aries_cloudagent.messaging.models.base import BaseModel, BaseModelSchema
from marshmallow import fields

from acapy_plugin_toolbox.util import (
    PassHandler,
    expand_message_class,
    expand_model_class,
)


def test_expand_message_class():
    """Test that expand_message_class is correctly expanding."""

    @expand_message_class
    class TestMessage(AgentMessage):
        message_type = "test_type"
        handler = "handler"

        class Fields:
            test = fields.Str(required=True)

        def __init__(self, test: str = None, **kwargs):
            super().__init__(**kwargs)
            self.test = test

    assert TestMessage.Schema.Meta.model_class == TestMessage
    assert TestMessage.Meta.message_type == "test_type"
    assert TestMessage.Meta.handler_class == "handler"
    assert TestMessage.Meta.schema_class == "TestMessage.Schema"

    test = TestMessage(test="test")
    test2 = TestMessage.deserialize(test.serialize())
    assert test.test == test2.test
    assert test._type == test2._type
    assert test.__slots__ == ["test"]


def test_expand_message_class_with_protocol():
    """Test protocol is prepended to message_type."""

    @expand_message_class
    class TestMessage(AgentMessage):
        protocol = "protocol"
        message_type = "type"
        handler = "handler"

        class Fields:
            test = fields.Str(required=True)

        def __init__(self, test: str = None):
            super().__init__()
            self.test = test

    test = TestMessage("test")
    assert test._type == "protocol/type"


def test_expand_message_class_x_missing_message_type():
    """Test that missing message type raises error."""
    with pytest.raises(ValueError):

        @expand_message_class
        class TestMessage(AgentMessage):
            handler = "handler"

            class Fields:
                test = fields.Str(required=True)


def test_expand_message_class_missing_handler_uses_pass():
    """Test that missing handler raises error."""

    @expand_message_class
    class TestMessage(AgentMessage):
        message_type = "test_type"

        class Fields:
            test = fields.Str(required=True)

    assert TestMessage.Handler == PassHandler


def test_expand_message_class_x_missing_fields():
    """Test that missing Fields and no schema raises error."""
    with pytest.raises(ValueError):

        @expand_message_class
        class TestMessage(AgentMessage):
            message_type = "test_type"
            handler = "handler"


def test_expand_message_class_fields_from():
    """Test that expand message class can reuse another schema."""

    class OtherTestMessage(AgentMessage):
        def __init__(self, one: str = None, **kwargs):
            super().__init__(**kwargs)
            self.one = one

    class TestSchema(AgentMessageSchema):
        one = fields.Str(required=True)

    @expand_message_class
    class TestMessage(OtherTestMessage):
        message_type = "type"
        handler = "handler"
        fields_from = TestSchema

    test = TestMessage("test")
    assert test.one
    assert TestMessage.deserialize(test.serialize())


def test_expand_model_class():
    """Test that models are expanded as expected."""

    @expand_model_class
    class TestModel(BaseModel):
        """Test Model."""

        class Fields:
            test = fields.Str(required=True)

        def __init__(self, test: str = None, **kwargs):
            super().__init__(**kwargs)
            self.test = test

    test = TestModel("test")
    assert test.test == "test"
    assert isinstance(test.Schema(), BaseModelSchema)
    assert test.Meta != BaseModel.Meta
    assert test.test == TestModel.deserialize(test.serialize()).test


def test_expand_model_class_x_missing_fields():
    """Test that missing Fields and no schema raises error."""
    with pytest.raises(ValueError):

        @expand_model_class
        class TestModel(BaseModel):
            pass


def test_expand_model_class_fields_from():
    """Test that expand model class can reuse another schema."""

    class OtherTestModel(BaseModel):
        def __init__(self, one: str = None, **kwargs):
            super().__init__(**kwargs)
            self.one = one

    class TestSchema(BaseModelSchema):
        one = fields.Str(required=True)

    @expand_model_class
    class TestModel(OtherTestModel):
        model_type = "type"
        handler = "handler"
        fields_from = TestSchema

    test = TestModel("test")
    assert test.one
    assert TestModel.deserialize(test.serialize())
