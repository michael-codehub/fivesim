# Public-domain function injector for The Sims 4 (CPython 3.7).
# Wraps a target method so our code runs around the original.
import inspect
from functools import wraps


def inject(target_object, target_function_name, safe=False):
    if safe and not hasattr(target_object, target_function_name):
        def _self_wrap(wrap_function):
            return wrap_function
        return _self_wrap

    def _wrap_original_function(original_function, new_function):
        @wraps(original_function)
        def _wrapped_function(*args, **kwargs):
            if type(original_function) is property:
                return new_function(original_function.fget, *args, **kwargs)
            return new_function(original_function, *args, **kwargs)

        if inspect.ismethod(original_function):
            return classmethod(_wrapped_function)
        elif type(original_function) is property:
            return property(_wrapped_function)
        return _wrapped_function

    def _injected(wrap_function):
        original_function = getattr(target_object, target_function_name)
        setattr(target_object, target_function_name,
                _wrap_original_function(original_function, wrap_function))
        return wrap_function

    return _injected
