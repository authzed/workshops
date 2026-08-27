"""spicedb_client.py — construct an async SpiceDB v1 client from the environment."""
import os

from authzed.api.v1 import Client
from grpcutil import insecure_bearer_token_credentials


def make_client() -> Client:
    endpoint = os.getenv("SPICEDB_ENDPOINT", "localhost:50051")
    token = os.getenv("SPICEDB_TOKEN", "devtoken")
    return Client(endpoint, insecure_bearer_token_credentials(token))
