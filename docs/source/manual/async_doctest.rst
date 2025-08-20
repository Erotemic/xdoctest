Doctests with async code
------------------------

Python 3.5 introduced `async` functions.  These are functions that run within an "event loop" that is not blocked if those functions perform blocking IO. It's similar to writing multi-threaded code but with the advantage of not having to worry about thread safety.  For more information see `the python docs <https://peps.python.org/pep-0492/>`__.

Asynchronous python code examples using `asyncio <https://docs.python.org/3/library/asyncio.html>`__ are supported at the top level by xdoctest.
This means that your code examples do not have to wrap every small snippet in a function and call :func:`asyncio.run`.
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

.. caution::

    Each code block with top level awaits runs in its own :func:`asyncio.run`. This means that all tasks created in such a block will be cancelled when it finishes. If you want more asyncio REPL-like behavior, see the next section.

``ASYNC`` Directive
===================

By default, xdoctest separates code blocks with top level awaits and blocks without. The former will have a running asyncio event loop, but the latter will not. This can be undesirable when you need to multitask or use the same event loop for all blocks.

.. code:: python

    >>> import yourlibrary
    >>> import asyncio
    >>> task = asyncio.create_task(yourlibrary.send_message())  # fails!
    >>> # ...do something else...
    >>> result = await task  # never be reached

To solve this problem, since 1.3.0 xdoctest has a new basic directive, ``ASYNC``. Just enable the directive at the beginning of your code example and you will get the asyncio REPL behavior.

.. code:: python

    >>> # xdoctest: +ASYNC
    >>> import yourlibrary
    >>> import asyncio
    >>> task = asyncio.create_task(yourlibrary.send_message())  # ok
    >>> # ...do something else...
    >>> result = await task  # will be reached

Of course, you can use the directive to cover certain places in your code too. With this you can demonstrate the behavior of your functions both inside and outside :func:`asyncio.run` in a single example.

.. code:: python

    >>> import yourlibrary
    >>> yourlibrary.in_async_context()  # xdoctest: +ASYNC
    True
    >>> yourlibrary.in_async_context()  # xdoctest: -ASYNC
    False

You may also find it convenient to enable the directive for all tests by default, in order to avoid boilerplate. For this, as with any other basic directive, you can use ``--options ASYNC`` for the native interface and ``--xdoctest-options ASYNC`` for the pytest interface.

Caveats
=======

* Consumers reading your documentation may not be familiar with async concepts. It could be helpful to mention in your docs that the code examples should be run in an event loop or in a REPL that supports top-level :keyword:`await`. (IPython supports this by default. For the standard Python REPL, use ``python -m asyncio``.)
* Using top level awaits in tests that are already running in an event loop is not supported.
* Only python's native asyncio library is supported for top level awaits.
