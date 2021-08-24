import os
import asyncio
import functools
import sys
import pkgutil
from collections import Mapping

from sanic.response import HTTPResponse
from mako.lookup import TemplateLookup
from sanic.exceptions import ServerError
from mako.exceptions import TemplateLookupException, text_error_template

__version__ = '0.6.0'

__all__ = ('get_lookup', 'render_template', 'render_template_def',
           'render_string')


APP_KEY = 'sanic_mako_lookup'
APP_CONTEXT_PROCESSORS_KEY = 'sanic_mako_context_processors'
REQUEST_CONTEXT_KEY = 'sanic_mako_context'


def get_root_path(import_name):
    mod = sys.modules.get(import_name)
    if mod is not None and hasattr(mod, '__file__'):
        return os.path.dirname(os.path.abspath(mod.__file__))

    loader = pkgutil.get_loader(import_name)
    if loader is None or import_name == '__main__':
        return os.getcwd()

    __import__(import_name)
    mod = sys.modules[import_name]
    filepath = getattr(mod, '__file__', None)

    if filepath is None:
        raise RuntimeError('No root path can be found for the provided '
                           'module "{import_name}".  This can happen because the '
                           'module came from an import hook that does '
                           'not provide file name information or because '
                           'it\'s a namespace package.  In this case '
                           'the root path needs to be explicitly provided.')

    return os.path.dirname(os.path.abspath(filepath))


class TemplateError(RuntimeError):
    """ A template has thrown an error during rendering. """

    def __init__(self, template):
        super(TemplateError, self).__init__()
        self.einfo = sys.exc_info()
        self.text = text_error_template().render()
        if hasattr(template, 'uri'):
            msg = "Error occurred while rendering template '{0}'"
            msg = msg.format(template.uri)
        else:
            msg = template.args[0]
        super(TemplateError, self).__init__(msg)


class SanicMako:
    def __init__(self, app=None, pkg_path=None, context_processors=(),
                 app_key=APP_KEY):
        self.app = app

        if app:
            self.init_app(app, pkg_path, context_processors)

    def init_app(self, app, pkg_path=None, context_processors=(),
                 app_key=APP_KEY):

        if pkg_path is not None and os.path.isdir(pkg_path):
            paths = [pkg_path]
        else:
            paths = [os.path.join(get_root_path(app.name), 'templates')]

        self.context_processors = context_processors

        if context_processors:
            app[APP_CONTEXT_PROCESSORS_KEY] = context_processors
            app.middlewares.append(context_processors_middleware)

        kw = {
            'input_encoding': app.config.get('MAKO_INPUT_ENCODING', 'utf-8'),
            'module_directory': app.config.get('MAKO_MODULE_DIRECTORY', None),
            'collection_size': app.config.get('MAKO_COLLECTION_SIZE', -1),
            'imports': app.config.get('MAKO_IMPORTS', []),
            'filesystem_checks': app.config.get('MAKO_FILESYSTEM_CHECKS', True),
            'default_filters': app.config.get('MAKO_DEFAULT_FILTERS', ['str', 'h']),  # noqa
            'preprocessor': app.config.get('MAKO_PREPROCESSOR', None),
            'strict_undefined': app.config.get('MAKO_STRICT_UNDEFINED', False),
        }

        setattr(app, app_key, TemplateLookup(directories=paths, **kw))

        return getattr(app, app_key)

    @staticmethod
    def template(template_name, app_key=APP_KEY, status=200):
        def wrapper(func):
            @functools.wraps(func)
            async def wrapped(*args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    coro = func
                else:
                    coro = asyncio.coroutine(func)
                context = await coro(*args, **kwargs)
                request = args[-1]
                response = await render_template(template_name, request, context,
                                                 app_key=app_key)
                response.status = status
                return response
            return wrapped
        return wrapper


def get_lookup(app, app_key=APP_KEY):
    return getattr(app, app_key)


async def render_string(template_name, request, context, *, app_key=APP_KEY):
    lookup = get_lookup(request.app, app_key)

    if lookup is None:
        raise TemplateError(ServerError(
            f"Template engine is not initialized, "
            "call sanic_mako.init_app first", status_code=500))
    try:
        template = lookup.get_template(template_name)
    except TemplateLookupException as e:
        raise TemplateError(ServerError(f"Template '{template_name}' not found",
                                        status_code=500)) from e
    if not isinstance(context, Mapping):
        raise TemplateError(ServerError(
            "context should be mapping, not {type(context)}", status_code=500))
    if request.ctx.__dict__.get(REQUEST_CONTEXT_KEY):
        context = dict(request[REQUEST_CONTEXT_KEY], **context)
    try:
        text = template.render(request=request, app=request.app, **context)
    except Exception:
        translate = request.app.config.get("MAKO_TRANSLATE_EXCEPTIONS", False)
        if translate:
            template.uri = template_name
            raise TemplateError(template)
        else:
            raise

    return text


async def render_template_def(template_name, def_name, request, context, *,
                              app_key=APP_KEY):
    lookup = get_lookup(request.app, app_key)

    if lookup is None:
        raise TemplateError(ServerError(
            f"Template engine is not initialized, "
            "call sanic_mako.init_app first", status_code=500))
    try:
        template = lookup.get_template(template_name)
    except TemplateLookupException as e:
        raise TemplateError(ServerError(f"Template '{template_name}' not found",
                                        status_code=500)) from e
    if not isinstance(context, Mapping):
        raise TemplateError(ServerError(
            "context should be mapping, not {type(context)}", status_code=500))
    if request.ctx.__dict__.get(REQUEST_CONTEXT_KEY):
        context = dict(request[REQUEST_CONTEXT_KEY], **context)
    try:
        text = template.get_def(def_name).render(app=request.app, **context)
    except Exception:
        translate = request.app.config.get("MAKO_TRANSLATE_EXCEPTIONS", True)
        if translate:
            template.uri = template_name
            raise TemplateError(template)
        else:
            raise

    return text


async def render_template(template_name, request, context, *,
                          content_type=None, app_key=APP_KEY):
    text = await render_string(template_name, request, context, app_key=app_key)
    if content_type is None:
        content_type = 'text/html'
    return HTTPResponse(text, content_type=content_type)


async def context_processors_middleware(app, handler):
    async def middleware(request):
        request[REQUEST_CONTEXT_KEY] = {}
        for processor in app[APP_CONTEXT_PROCESSORS_KEY]:
            request[REQUEST_CONTEXT_KEY].update(
                (await processor(request)))
        return (await handler(request))
    return middleware
