"""Common fixtures."""
import pytest

def test_emptytest1():
    assert True

def test_emptytest2():
    assert 1+1 == 2

def test_create_invitation():
    pass

    # {
    #     "@type": "https://github.com/hyperledger/aries-toolbox/tree/master/docs/admin-invitations/0.1/create",
    #     "alias": "Invitation I sent to Alice",
    #     "label": "Bob"
    #     "group": "admin",
    #     "auto_accept": true,
    #     "multi_use": true,
    #     "mediation_id": "42a1f1c9-b463-4f59-8385-2e2f7b70466a"
    # }