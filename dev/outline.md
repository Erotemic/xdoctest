Title 
=====

Developing With Doctests 

Description 
===========

This talk is about is about doctests --- a way to embed unit tests and examples in docstrings. I describe what they are, how to write them, and interesting ways in which they can be used. Doctests make it easy to interactively develop code by defining “demo” inputs which can be copied into IPython. The side effect is a unit test. This is test-driven-development at its best. I explain the technical details of doctest syntax, directives, parsing, and execution.

Unfortunately, Python’s builtin doctest module has a restrictive syntax, which makes it difficult to use. In the second part of the talk I introduce an alternative: XDoctest, a new, but stable package for parsing and running doctests (with optional pytest integration). I explain why doctest’s regex-based parser is fundamentally limited and how xdoctest’s ast-based parser is the remedy. I demonstrate how to use xdoctest and discuss its advantages and disadvantages. By the end of this talk you feel confident in writing, running, and developing with doctests.

https://us.pycon.org/2020/speaking/talks/

Who and Why (Audience)
======================

1. Who is this talk for?:
   1. Python developers wishing to master test-driven-design. 
   2. People who have been burnt by the doctest module.

2. What background knowledge or experience do you expect the audience to have?:
    1. The ability to read and write Python code.  (required)
    2. What a docstring is. (nice to have)
    3. Some familiarity with IPython. (nice to have)

3. What do you expect the audience to learn after watching the talk?: 
   1. Why doctests are awesome
   2. How to write a doctest.
   3. How to run a test with the builtin doctest module and where issues arise.
   4. How to fix these issues with xdoctest.
   5. A little math trivia about how you can’t parse a context-free language with the re module.


References:
    https://pythontesting.net/framework/doctest/doctest-introduction/


Developing With Doctests 
========================

## Part 0: Introduction 

### Introduction - 1 minutes
   * Background
   * Interests
   * Code-ography

## Part 1 - Introduction to Doctests

### What are doctests - 2 minutes
   * Prefixed code in a docstring
   * Documentation
      * demonstrates your code
   * Testing
      * coverage
      * correctness
      * Continuous Integration / Distribution (CI / CD) 

### What can doctests do? - 2 minutes
   * Encourage you to create “demo data”
   * Let you “play” with the code
      * Similar to Jupyter notebooks (but they help you publish packages instead of papers)
   * Show "ENTRYPOINTS - ENTRYPOINTS EVERYWHERE" meme

### How to write a doctest - 1 minutes
   * Write a test / example function
   * Simply prefix it with >>>
   * Stick it in the docstring

### Case Study #1.1 - 1 minutes

   * Write a doctest for the `paragraph` function.

### Case Study #1.2 - 1 minutes

   * Runs our doctest using the builtin doctest module and runs into errors
   * Discuss those errors

### Case Study #1.3 - 1 minutes

   * Fix those errors.

   * Rerun doctest and show the errors are fixed.

### Case Study #2.1 - 1 minutes

   * Write a doctest for the `allsame` function.

   * Run the `allsame` doctest and run into errors.

   * Discuss these errors

### Case Study #2.2 - 1 minutes
   
   * Attempt to fix those errors

   * Talk about doctest directives

   * Attempt to fix those errors

### Why aren’t doctests everywhere? - 1 minutes

   * They are… somewhat, but they aren’t always working
   * The builtin doctest module is… lacking
       * syntax issues
       * difficult error messages
       * slightly overcomplicated
   * Don’t worry I have a solution

## Part 2 - XDoctest

### The xdoctest Module - 1 minutes

   * Mostly backwards compatible
   * Simpler syntax
   * One golden rule: “>>>”

### Quick aside on formal languages - 2 minutes

   * Chomsky Hierarchy

### Formal Python - 2 minutes
   * Where python sits on the Chomsky Hierarchy
   * Why doctests need `ast` not `re`

### Revisit Case Study #1 - 1 minutes
 
   * Discuss how and why the original syntax will work with xdoctest

### Revisit Case Study #1 - 1 minutes

   * Run the original doctest with xdoctest to show that it works

### Revisit Case Study #2 - 1 minutes

   * Discuss how and why the original syntax will work with xdoctest
   * Run the original doctest with xdoctest to show that it works

### XDoctest is easier to run - 1 minute
   * Easier to run

### XDoctest has better output - 1 minute
   * line numbers
   * pygments colorized output
   * command to reproduce errors

### XDoctest has better directives - 1 minute
   * Backwards compatibility 
   * New block based directives
   * New directives invocations
   * New REQUIRES(.) directive

### XDoctest has a pytest plugin - 1 minutes

   * native runner
       * pip install xdoctest
       * xdoctest [-m] <modname>
       * xdoctest -m mymod.py
       * xdoctest -m doctests.
   * pytest runner
       * Xdoctest ships with pytest integration
       * pip install xdoctest
       * pytest --xdoctest

### When your doctests work / fail - 1 minutes

   * It shows how many tests will run
   * It displays the source code and output of each test that is run
   * It prints a big friendly exit message indicating that everything worked great and you are a wonderful programmer

   * Prints how many and what tests failed
       * provides shell commands to reproduce errors
   * It displays the source code and output of each test that is run. This includes the error message
   * Provides additional information when using got / want tests

### Limitations - 1 minutes
   * It’s a tad slower
   * It’s not 100% backwards compatible
       * Some directives no longer exist

### Miscellaneous features in xdoctests - 1 minutes

   * Zero args runner
   * Random utilities

## Part 3 - Wrapping up
### Doctests -vs- Xdoctest - 1 minutes

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

### Contributing - 1 minutes
   * Submit a pull request to github
   * Areas for contribution
       * Parsing could be better
       * External docs could be better
   * Building on top
       * XDoctest exposes an easy way to parse doctests and get line numbers. There are cool refactoring tools that could be built on top of its framework.

### Summary & Conclusion - 1 minute
   * Introduction to Doctests
       * What it was
       * Strengths
       * Weaknesses
   * XDoctest
       * Improvements
       * Limitations
       * Cool stuff
   * Questions (time permitting)
