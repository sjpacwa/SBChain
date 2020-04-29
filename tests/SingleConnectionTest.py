import pytest

"""

Setup:
    Create a node with a known host and port

Test:
    Connect to a node that exist
        Send requests to connection
        Send requests that pass JSON parsing
        Send requests that don't pass JSON parsing
        Send requests where we expect a response
    Connect to a node that doesn't exist

Teardown:
    Nothing is needed

"""

@pytest.fixture
def resource():
    yield "resource"

class SingleConnectionTest():
    
