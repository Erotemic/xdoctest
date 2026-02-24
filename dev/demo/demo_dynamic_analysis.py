"""
CommandLine:
    xdoctest ~/code/xdoctest/dev/demo/demo_dynamic_analysis.py --analysis=auto

    xdoctest ~/code/xdoctest/dev/demo/demo_dynamic_analysis.py --analysis=dynamic

    xdoctest ~/code/xdoctest/dev/demo/demo_dynamic_analysis.py --xdoc-force-dynamic
"""


def func() -> None:
    r"""Dynamic doctest
    >>> %s
    %s
    """
    return


func.__doc__ %= ('print(1)', '1')
