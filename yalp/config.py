# vim: set et ts=4 sw=4 fileencoding=utf-8:
'''
yalp.config
===========
'''
import os
import yaml

import logging
logger = logging.getLogger(__name__)


EMPTY = object()


DEFAULT_OPTS = {
    'broker_url': 'amqp://guest:guest@localhost:5672//',
    'parser_queue': 'parsers',
    'output_queue': 'outputs',
    'parser_worker_name': 'parser-workers',
    'output_worker_name': 'output-workers',
    'parser_workers': 5,
    'output_workers': 1,
    'celery_advanced': {},
    'inputs': [],
    'parsers': [],
    'outputs': [],
    'home': None,
    'input_packages': ['yalp.inputs'],
    'parser_packages': ['yalp.parsers'],
    'output_packages': ['yalp.outputs'],
}


def _read_conf_file(path):
    '''
    Parse yaml config file into dictionary.
    '''
    if path is None:
        return {}

    with open(path, 'r') as conf_file:
        try:
            conf_opts = yaml.safe_load(conf_file.read()) or {}
        except yaml.YAMLError as err:
            logger.error(
                'Error parsing configuration file: %s - %s', path, err)
            conf_opts = {}
        return conf_opts


def load_config(path, defaults=None):
    '''
    Read in config file.
    '''
    if defaults is None:
        defaults = DEFAULT_OPTS

    overrides = _read_conf_file(path)
    opts = defaults.copy()
    if overrides:
        opts.update(overrides)
    return opts


# pylint: disable=W0212
def new_method_proxy(func):
    ''' Proxy function call to lazy get attrs '''
    def inner(self, *args):  # pylint: disable=C0111
        if self._wrapped is EMPTY:
            self._setup()
        return func(self._wrapped, *args)
    return inner
# pylint: enable=W0212


class LazyObject(object):
    '''
    Wrapper for another class to delay instantiation.
    '''
    _wrapped = None

    def __init__(self):
        self._wrapped = EMPTY

    __getattr__ = new_method_proxy(getattr)

    def __setattr__(self, name, value):
        if name == '_wrapped':
            self.__dict__['_wrapped'] = value
        else:
            if self._wrapped is EMPTY:
                self._setup()
            setattr(self._wrapped, name, value)

    def __delattr__(self, name):
        if name == '_wrapped':
            raise TypeError('can\'t delete _wrapped.')
        if self._wrapped is EMPTY:
            self._setup()
        delattr(self._wrapped, name)

    def _setup(self):
        '''
        Must be implemented by subclasses to initialize wrapped object.
        '''
        raise NotImplementedError

    __dir__ = new_method_proxy(dir)


class LazySettings(LazyObject):
    '''
    Delay loading of settings.
    '''
    def _setup(self):
        settings_file = os.environ.get('YALP_CONFIG_FILE', None)
        self._wrapped = Settings(settings_file)


class Settings(object):
    '''
    Load settings from yaml into object.
    '''
    def __init__(self, settings_file, defaults=None):
        opts = load_config(settings_file, defaults=defaults)
        for opt, value in opts.items():
            setattr(self, opt, value)


settings = LazySettings()
