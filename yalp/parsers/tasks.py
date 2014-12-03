# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
yalp.parsers.tasks
==================
'''
from celery import shared_task

from ..exceptions import ImproperlyConfigured


def _get_parser(config):
    '''
    Get the parser class from the config
    '''
    try:
        parser_module_name = config['module']
        parser_class_name = config['class']
        parser_module = __import__(parser_module_name,
                                   fromlist=[parser_class_name])
        parser_class = getattr(parser_module, parser_class_name)
        return parser_class(config)
    except KeyError:
        raise ImproperlyConfigured('Invalid config.')
    except ImportError:
        raise ImproperlyConfigured('Invalid parser module/class.')


@shared_task
def process_message(config, message):
    '''
    Process a message using settings from config.

    config
        Dictionary of config settings defining how to process the message.
    message
        The message to process, generally a string.
    '''
    parser = _get_parser(config)
    return parser.parse(message)
