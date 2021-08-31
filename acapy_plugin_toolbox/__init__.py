"""Shortcut to group all and rexports."""

import os
import logging

from aries_cloudagent.protocols.problem_report.v1_0.message import ProblemReport
from aries_cloudagent.config.injection_context import InjectionContext

from . import (
    basicmessage,
    connections,
    credential_definitions,
    dids,
    invitations,
    issuer,
    mediator,
    routing,
    schemas,
    static_connections,
    taa,
    trustping,
)
from .holder import v0_1 as holder

MODULES = [
    basicmessage,
    connections,
    credential_definitions,
    dids,
    invitations,
    issuer,
    mediator,
    routing,
    schemas,
    static_connections,
    taa,
    trustping,
    holder,
]


async def setup(context: InjectionContext):
    """Load Toolbox Plugin."""
    log_level = os.environ.get("ACAPY_TOOLBOX_LOG_LEVEL", logging.WARNING)
    logging.getLogger("acapy_plugin_toolbox").setLevel(log_level)
    print("Setting logging level of acapy_plugin_toolbox to", log_level)
    for mod in MODULES:
        await mod.setup(context)


__all__ = ["ProblemReport"]
