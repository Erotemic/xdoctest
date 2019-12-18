Title 
=====

Developing With Doctests 

Description 
===========

This talk is about is about doctests --- a way to embed unit tests and examples in docstrings. I describe what they are, how to write them, and interesting ways in which they can be used. Doctests make it easy to interactively develop code by defining “demo” inputs which can be copied into IPython. The side effect is a unit test. This is test-driven-development at its best. 

Unfortunately, Python’s builtin doctest module has a restrictive syntax, which makes it difficult to use. In the second part of the talk I introduce an alternative: XDoctest, a new, but stable package for parsing and running doctests (with optional pytest integration). I explain why doctest’s regex-based parser is fundamentally limited and how xdoctest’s ast-based parser is the remedy. I demonstrate how to use xdoctest and discuss its advantages and disadvantages. By the end of this talk you feel confident in writing, running, and developing with doctests.

https://us.pycon.org/2020/speaking/talks/

Who and Why (Audience)
======================

1. Who is this talk for?:
   1. Python developers wishing to master test-driven-design. 

2. What background knowledge or experience do you expect the audience to have?:
    1. The ability to read and write Python code.
    2. What a docstring is. 
    3. Some familiarity with IPython.

3. What do you expect the audience to learn after watching the talk?: 
   1. How to write a doctest for an existing function and run it
   2. How to interactively design a function and in such a way that a doctest is a by-product. 
   3. A little math trivia about how you can’t parse a context-free language with the re module.


References:
    https://pythontesting.net/framework/doctest/doctest-introduction/


Developing With Doctests 
========================

## Part 0: Introduction 

* Introduction - 1 minutes
   * Background
   * Interests
   * Code-ography

## Part 1 - Introduction to Doctests

* What are doctests - 2 minutes
   * Prefixed code in a docstring
   * Documentation
      * demonstrates your code
   * Testing
      * coverage
      * correctness
      * Continuous Integration / Distribution (CI / CD) 
* How to write a doctest - 2 minutes
   * Write a test / example function
   * Simply prefix it with >>>
   * Stick it in the docstring
* What can doctests do? - 2 minutes
   * Encourage you to create “demo data”
   * Let you “play” with the code
      * Similar to Jupyter notebooks (but they help you publish packages instead of papers)
   * Entrypoints 
* Why aren’t doctests everywhere? - 2 minutes
       * They are… somewhat, but they aren’t always working
       * The builtin doctest module is… lacking
           * syntax issues
           * difficult error messages
           * slightly overcomplicated
       * Don’t worry I have a solution

## Part 2 - XDoctest

   * The xdoctest Module - 2 minutes
       * Mostly backwards compatible
       * Simpler syntax
       * One golden rule: “>>>”
   * Quick aside on formal languages - 1 minutes
       * Chomsky Hierarchy
   * Formal Python - 1 minutes
       * Where python sits on the Chomsky Hierarchy
       * Whey doctests need `ast` not `re`
   * Improvements in xdoctest - 2 minutes
       * Directives
           * inline
           * REQUIRES
       * Easier to run
       * Better output messages
           * line numbers
           * pygments colorized output
           * command to reproduce errors
   * New Directives - 2 minutes
       * Single line directives
       * New directives invocations
       * Backwards compatibility 
       * New standalone directives
       * new REQUIRES(.) directive
   * Limitations - 1 minutes
       * It’s a tad slower
       * It’s not 100% backwards compatible
           * Some directives no longer exist
   * Running doctests - 2 minutes
       * native runner
           * pip install xdoctest
           * xdoctest [-m] <modname>
           * xdoctest -m mymod.py
           * xdoctest -m doctests.
       * pytest runner
           * Xdoctest ships with pytest integration
           * pip install xdoctest
           * pytest --xdoctest
   * When your doctests work - 1 minutes
       * It shows how many tests will run
       * It displays the source code and output of each test that is run
       * It prints a big friendly exit message indicating that everything worked great and you are a wonderful programmer
   * When your tests fail - 2 minutes
       * Prints how many and what tests failed
           * provides shell commands to reproduce errors
       * It displays the source code and output of each test that is run. This includes the error message
       * Provides additional information when using got / want tests
   * Miscellaneous features in xdoctests - 1 minutes
       * Zero args runner
       * Random utilities

## Part 3 - Wrapping up
   * Doctests -vs- Xdoctest - 2 minutes
       * Doctest:
           * built into the standard library stdlib
           * uses re (regular expressions). 
           * restrictive syntax
           * massive inertia
       * Xdoctset:
           * external pip installable module
           * uses ast ( abstract syntax trees )
           * relaxed syntax
           * mostly backwards compatible
           * 32 stars on github
   * Contributing - 2 minutes
       * Submit a pull request to github
       * Areas for contribution
           * Parsing could be better
           * External docs could be better
       * Building on top
           * XDoctest exposes an easy way to parse doctests and get line numbers. There are cool refactoring tools that could be built on top of its framework.
   * Summary & Conclusion 2 minutes 
       * Introduction to Doctests
           * What it was
           * Strengths
           * Weaknesses
       * XDoctest
           * Improvements
           * Limitations
           * Cool stuff
       * Questions (time permitting)
