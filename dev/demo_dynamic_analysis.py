"""
CommandLine:
    xdoctest = ~/code/xdoctest/dev/demo_dynamic_analysis.py
"""


def func() -> None:
    r''' Dynamic doctest
    >>> %s
    %s
    '''
    return

func.__doc__ %= ('print(1)', '1')
