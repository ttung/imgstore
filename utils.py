#!/usr/bin/env python

def get_caller_function_name():
    import inspect

    callerframerecord = inspect.stack()[1]
    frame = callerframerecord[0]
    info = inspect.getframeinfo(frame)

    return info.function


