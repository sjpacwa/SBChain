import pytest

"""

Setup:
    Create a group of nodes with known hosts and ports

Test:
    Connect to multiple nodes that exist
        Send requests to connection
        Send requests that pass JSON parsing
        Send requests that don't pass JSON parsing
        Send requests where we expect a response
    Connect to multiple nodes where some exist and some don't
    Connect to multiple nodes that don't exist

Teardown:
    Nothing is needed

"""

@pytest.fixture
def resource():
    yield "resource"

class SingleConnectionTest():
    
