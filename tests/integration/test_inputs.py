# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
test.integration.test_inputs
============================
'''
import unittest

from yalp.config import settings
from yalp import scripts

try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock


def _side_effect_open(path, *args):
    if path.startswith('/dev/null'):
        mocked_file = MagicMock()
        mocked_file.readline.side_effect = ['test message\n', None]
        return mocked_file
    else:
        return MagicMock()


class TestInputEntryPoint(unittest.TestCase):
    '''
    Test scripts.InputsEntryPoint.
    '''
    def setUp(self):
        settings.inputs = [{
            'file': {
                'path': '/dev/null',
            }
        }]
        try:
            import socket
            import amqp
            self.connection = amqp.Connection()
            self.channel = self.connection.channel()
        except socket.error:
            from nose.plugins.skip import SkipTest
            raise SkipTest('Unable to connect to rabbitmq')

    def tearDown(self):
        self.channel.queue_delete(queue='outputs')
        self.channel.close()
        self.connection.close()

    @patch('yalp.inputs.file.open', create=True)
    def test_entry_point(self, mock_open):
        mock_open.side_effect = _side_effect_open
        entrypoint = scripts.InputsEntryPoint(max_iterations=2, interval=0.2)
        entrypoint.execute()
        message = self.channel.basic_get(queue='outputs')
        self.assertIsNotNone(message)
        self.assertTrue('test message' in str(message.body))
