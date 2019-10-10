import os
import json
from flask import current_app, request
from flask_testing import TestCase
from flask_socketio import SocketIOTestClient, send
from flfm import create_app, socketio
from .config import Config

class SocketIOClientContext(SocketIOTestClient):
    def __init__(self, app, socketio, **kwargs):
        namespace = kwargs.get('namespace', None)
        query_string = kwargs.get('query_string', None)
        headers = kwargs.get('headers', None)
        flask_test_client = kwargs.get('flask_test_client', None)
        super().__init__(app, socketio, namespace, query_string, headers,
                         flask_test_client)
        self.context_namespace = namespace

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.disconnect(self.context_namespace)
        return False

class TestConfig(Config):
    TESTING = True
    PROPAGATE_EXCEPTIONS = True

class SocketsWorkingTest(TestConfig, TestCase):
    def __init__(self, *args, **kwargs):
        super(SocketsWorkingTest, self).__init__(*args, **kwargs)
        self.sio_instance = None

    def setUp(self):
        self.sio_instance = socketio

    def create_app(self):
        return create_app(self)

    def test_sockets_working(self):
        @socketio.on('connect')
        def on_connect():
            send('connected')
            send(json.dumps(request.args.to_dict(flat=False)))

        print("\n\nTEST IF SOCKETIO WORKING")

        with SocketIOClientContext(current_app, self.sio_instance,
                                   flask_test_client=self.client) as sockclient:
            self.assertTrue(sockclient.is_connected())
            sent_data = sockclient.get_received()
            self.assertEqual(len(sent_data), 2)
            self.assertEqual(sent_data[0]['args'], 'connected')
            self.assertEqual(sent_data[1]['args'], '{}')
