# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
yalp.scripts
============
'''
from celery import Celery
import os
import sys
import argparse

import logging
logger = logging.getLogger(__name__)

from . import version
from .config import settings


def _get_hostname():
    '''
    Get system's hostname for worker process name.
    '''
    import socket
    hostname = socket.gethostname()
    del socket
    return hostname


def get_celery_app(config):
    '''
    Create the parsers celery app.
    '''
    app = Celery()
    app.conf.update(
        BROKER_URL=config.broker_url,
        CELERY_ROUTES={
            'yalp.parsers.tasks.process_message': {
                'queue': config.parser_queue,
            },
            'yalp.outputs.tasks.process_output': {
                'queue': config.output_queue,
            },
        },
    )
    app.autodiscover_tasks(lambda: (
        'yalp.parsers',
        'yalp.outputs',
    ))
    return app


class BaseEntryPoint(object):
    '''
    Main Entry point.
    '''
    def __init__(self, description=None, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        self.description = description or self.prog_name
        self.parser = argparse.ArgumentParser(description='YALP')

    def add_arguments(self):
        '''
        Add arguments to arg parser.
        '''
        self.parser.add_argument('-v', '--version',
                                 action='store_true',
                                 default=False,
                                 help='Display YALP version')
        self.parser.add_argument('-c', '--config',
                                 default=None,
                                 help='Specify alternative config')

    def execute(self):
        '''
        Execute command.
        '''
        self.add_arguments()
        self.options = self.parser.parse_args(self.argv[1:])
        if self.options.version:
            print version.__version__
            sys.exit(0)
        if self.options.config:
            os.environ['YALP_CONFIG_FILE'] = self.options.config
        self.app = get_celery_app(settings)


class ParsersEntryPoint(BaseEntryPoint):
    '''
    Entry point for starting parser workers.
    '''
    def execute(self):
        super(ParsersEntryPoint, self).execute()
        self.app.worker_main([
            'yalp-parsers',
            '--concurrency={0}'.format(settings.parser_workers),
            '--queues={0}'.format(settings.parser_queue),
            '--hostname={0}-{1}'.format(
                _get_hostname(),
                settings.parser_worker_name,
            )
        ])


class OutputersEntryPoint(BaseEntryPoint):
    '''
    Entry point for starting outputers workers.
    '''
    def execute(self):
        super(OutputersEntryPoint, self).execute()
        self.app.worker_main([
            'yalp-outputers',
            '--concurrency={0}'.format(settings.output_workers),
            '--queues={0}'.format(settings.output_queue),
            '--hostname={0}-{1}'.format(
                _get_hostname(),
                settings.output_worker_name,
            )
        ])


class CliEntryPoint(BaseEntryPoint):
    '''
    Entry point for cli.
    '''
    def add_arguments(self):
        super(CliEntryPoint, self).add_arguments()
        self.parser.add_argument('message',
                                 metavar='message',
                                 type=str,
                                 nargs='?',
                                 default='test message',
                                 help='Message to process')

    def execute(self):
        super(CliEntryPoint, self).execute()
        from yalp.parsers import tasks
        tasks.process_message.delay(self.options.message)