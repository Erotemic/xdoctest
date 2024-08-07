Doctests with async code
------------------------

Python 3.5 introduced `async` functions.  These are functions that run within an "event loop" that is not blocked if those functions perform blocking IO. It's similar to writing multi-threaded code but with the advantage of not having to worry about thread safety.  For more information see `the python docs <https://peps.python.org/pep-0492/>`__.

Asynchronous python code examples using `asyncio <https://docs.python.org/3/library/asyncio.html>`__ are supported at the top level by xdoctest.
This means that your code examples do not have to wrap every small snippet in a function and call `asyncio.run`.
xdoctest handles that for you keeping the examples simple and easy to follow.

For example **without xdoctest** your code example would have to be written like this:

.. code:: python

    >>> import yourlibrary
    >>> import asyncio
    >>> async def connect_and_get_running_info_wrapper():
    ...     server = await yourlibrary.connect_to_server("example_server_url")
    ...     running_info = await server.get_running_info()
    ...     return server, running_info
    ...
    >>> server, running_info = asyncio.run(connect_and_get_running_info_wrapper())
    >>> running_info.restarted_at
    01:00

    >>> async def restart_and_get_running_info_wrapper(server):
    ...     await server.restart()
    ...     return await server.get_running_info()
    ...
    >>> running_info = asyncio.run(restart_and_get_running_info_wrapper(server))
    >>> running_info.restarted_at
    13:15

Now **with xdoctest** this can now be written like this:

.. code:: python

    >>> import yourlibrary
    >>> server = await yourlibrary.connect_to_server("example_server_url")
    >>> running_info = await server.get_running_info()
    >>> running_info.restarted_at
    01:00

    >>> await server.restart()
    >>> running_info = await server.get_running_info()
    >>> running_info.restarted_at
    13:15

The improvement in brevity is obvious but even more so if you are writing longer examples where you want to maintain and reuse variables between each test output step.

.. note::

    If you don't want to utilise this feature for your async examples you don't have to.  Just don't write code examples with top level awaits.

Caveats
=======

* Consumers reading your documentation may not be familiar with async concepts. It could be helpful to mention in your docs that the code examples should be run in an event loop or in a REPL that supports top-level ``await``. (IPython supports this by default. For the standard Python REPL, use ``python -m asyncio``.)
* Using top level awaits in tests that are already running in an event loop is not supported.
* Only python's native asyncio library is supported for top level awaits.