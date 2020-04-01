Title 
=====

Developing With Doctests - using Xdoctest as a backend

Description 
===========

This talk is about doctests --- a way to embed examples and unit tests in docstrings. I describe what they are, how to write them, and interesting ways in which they can be used. Doctests make it easy to interactively develop code by defining “demo” inputs which can be copied into IPython. The side effect is a unit test. This is test-driven-development at its best. I explain the technical details of doctest syntax, directives, parsing, and execution.

Unfortunately, Python’s builtin doctest module has a restrictive syntax, which makes it difficult to use. In the second part of the talk I introduce an alternative: Xdoctest, a new, but stable package for parsing and running doctests (with optional pytest integration). I explain why doctest’s regex-based parser is fundamentally limited and how xdoctest’s ast-based parser is the remedy. I demonstrate how to use xdoctest and discuss its advantages and disadvantages. By the end of this talk you feel confident in writing, running, and developing with doctests.

https://us.pycon.org/2020/speaking/talks/

Who and Why (Audience)
======================

1. Who is this talk for?:
   * Python developers wishing to master test-driven-design
   * People who have been burnt by the doctest module
   * People who want to learn an interesting way to test Python code

2. What background knowledge or experience do you expect the audience to have?:
   * The ability to read and write Python code (required)
   * What a docstring is (nice to have)
   * Some familiarity with IPython (nice to have)

3. What do you expect the audience to learn after watching the talk?: 
   * Why doctests are awesome
   * How to write a doctest
   * How to run a test with the builtin doctest module and where issues arise
   * How to fix these issues with xdoctest
   * A little math trivia about how you can’t parse a context-free language with the re module


References:
    https://pythontesting.net/framework/doctest/doctest-introduction/


Developing With Doctests 
========================

## PART 0: INTRODUCTION 

### INTRODUCTION - 1 MINUTE
   * Background
   * Interests
   * Code-ography

## PART 1 - INTRODUCTION TO DOCTESTS

### WHAT ARE DOCTESTS - 2 MINUTES
   * Prefixed code in a docstring
   * Documentation
      * Demonstrates your code
   * Testing
      * Coverage
      * Correctness
      * Continuous Integration / Distribution (CI / CD) 

   *shows an example of a doctest in a function with a zoomed in view of the doctest itself*

### WHAT CAN DOCTESTS DO? - 2 MINUTES
   * Encourage you to create “demo data”
   * Let you “play” with the code
      * Similar to Jupyter notebooks (but they help you publish packages instead of papers)
   * Show "ENTRYPOINTS - ENTRYPOINTS EVERYWHERE" meme

   *shows a more complex example where I use doctests to create an entrypoint that lets me play with my code in IPython* 

### HOW TO WRITE A DOCTEST - 1 MINUTE
   * Write a test / example function
   * Simply prefix it with >>>
   * Stick it in the docstring

   *shows a toy example for each bullet point*

### CASE STUDY #1 - 3 MINUTES

   * Write a doctest for the `paragraph` function

   *shows as the paragraph function and the test we are doing to "doctest-ify"*

   *shows what the doctest looks like inside the function*

   * Runs our doctest using the builtin doctest module and runs into errors
   * Discuss those errors

   *shows errors and zooms into a relevant region of the output*

   * Fix those errors

   * Rerun doctest and show the errors are fixed

   *shows the fixed doctest syntax and the result of a successful run*

### CASE STUDY #2 - 3 MINUTES

   * Write a doctest for the `allsame` function

   * Run the `allsame` doctest and run into errors

   * Discuss these errors

   *shows a doctest inside this function and demonstrates using "got/want" checks*

   *shows error output and a zoomed in view to the relevant region*

   * Attempt to fix those errors

   * Talk about doctest directives

   * Attempt to fix those errors (this wont go well to demonstrate how frustrating)

   *shows "fixed" doctest where we use directives to modify "got/want" behavior*

### WHY AREN’T DOCTESTS EVERYWHERE? - 1 MINUTE

   * They are… somewhat, but they aren’t always working
   * The builtin doctest module is… lacking
       * Syntax issues
       * Difficult error messages
       * Slightly overcomplicated
   * Don’t worry I have a solution

   *shows an image foreshadowing that xdoctest is the solution*

## PART 2 - XDOCTEST

### THE XDOCTEST MODULE - 1 MINUTE

   * Mostly backwards compatible
   * Simpler syntax
   * One golden rule: “>>>”

   *image is the xdoctest logo*

### QUICK ASIDE ON FORMAL LANGUAGES - 2 MINUTES

   * Chomsky Hierarchy
   * Briefly introduce recursively enumerable, context sensitive, context free, and regular languages. 
   * Note on the richness of the subject, but don't go too deep into it

   *shows an image of the simple 4-level hierarchy with an image (G)Noam Chomsky and of Alan Turing (next to recursively enumerable languages), the left shows the richer version with 14 levels*

### FORMAL PYTHON - 2 MINUTES
   * Where Python sits on the Chomsky Hierarchy
   * Explain that doctest uses regular expressions to "parse" its code
   * Explain why regular expressions cannot parse code and give balanced parenthesis as an example
   * Discuss why doctests need `ast` not `re`
   * Stress the point that doctests are Python code 

   *shows a different image of the 4-level hierarchy and an example programming language for each level*

### REVISIT CASE STUDY #1 - 1 MINUTE
 
   * Discuss how and why the original syntax will work with xdoctest

   * Discuss how xdoctest can use ast to determine where statements start and end

   * Show leniency of xdoctest syntax with respect to multi-line strings

   *shows an image of the original doctest from case study 1*

   *shows the successful xdoctest output*

### REVISIT CASE STUDY #2 - 1 MINUTE

   * Discuss how and why the original syntax will work with xdoctest
   * Run the original doctest with xdoctest to show that it works

   *shows an image of the original doctest from case study 2*

   *shows the successful xdoctest output*

### XDOCTEST IS EASIER TO RUN - 1 MINUTE
   * Easier to run

   *shows examples of different command line invocations* 

### XDOCTEST HAS BETTER OUTPUT - 1 MINUTE
   * Command to reproduce errors
   * Line numbers
   * Pygments colorized output

   *shows list of failed tests, highlights line numbers in xdoctest output*

### XDOCTEST HAS BETTER DIRECTIVES - 1 MINUTE

   * List which original directives are backwards compatible:
     * DONT_ACCEPT_BLANKLINE
     * ELLIPSIS
     * NORMALIZE_WHITESPACE
     * IGNORE_EXCEPTION_DETAIL
     * NORMALIZE_WHITESPACE
     * REPORT_CDIFF
     * REPORT_NDIFF
     * REPORT_UDIFF

   * List which original directives are not implemented in xdoctest:
     * DONT_ACCEPT_TRUE_FOR_1
     * REPORT_ONLY_FIRST_FAILURE
     * REPORTING_FLAGS
     * COMPARISON_FLAGS

   * Note on tweaked defaults

   * List new directives:
       * SKIP
       * IGNORE_WANT
       * REQUIRES(.)

   * Demo SKIP directive
   * Demo REQUIRES directive

   *this slide is all text*

   * Continue slide showing that xdoctest lets directives be applied to blocks of code instead of just a single line

   *shows an example of "block"-directive* 

   *shows xdoctest output when running the example*

### XDOCTEST HAS A PYTEST PLUGIN - 1 MINUTE

   * Pytest runner
       * Xdoctest ships with pytest integration
       * pip install xdoctest
       * pytest --xdoctest

   *shows the output of running pytest with the xdoctest plugin enabled*

### WHEN YOUR DOCTESTS WORK / FAIL - 1 MINUTE

   * It shows how many tests will run
   * It displays the source code and output of each test that is run
   * It prints a big friendly exit message indicating that everything worked great and you are a wonderful programmer

   *shows zoomed in command line to invoke multiple doctests, the intermediate output, and a zoomed view of the final few lines*

   * Prints how many and what tests failed
       * Provides shell commands to reproduce errors
   * It displays the source code and output of each test that is run. This includes the error message
   * Provides additional information when using got / want tests

   *shows zoomed in command line to invoke multiple doctests, the intermediate output, and a zoomed view of the final few lines*

### MISCELLANEOUS FEATURES IN XDOCTESTS - 1 MINUTE

   * Zero args runner
   * Random utilities
   * How xdoctest was used to obtain 100% test coverage in ubelt

   *shows reprise of ENTRYPOINTS meme, ubelt logo, and the 100% code coverage badge*

### LIMITATIONS - 1 MINUTE
   * It’s a tad slower
   * It’s not 100% backwards compatible
       * Some directives no longer exist

   *this slide is just text*

## PART 3 - WRAPPING UP
### DOCTESTS -VS- XDOCTEST - 1 MINUTE

   * Doctest:
       * Built into the standard library stdlib
       * Uses re (regular expressions)
       * Restrictive syntax
       * Terse output
       * Runs one file at a time
       * Massive inertia

   * Xdoctset:
        * External pip installable module
        * Uses ast ( abstract syntax trees )
        * Relaxed syntax
        * Better directives
        * Colored output
        * Mostly backwards compatible
        * Runs single functions or entire modules
        * Works on CPython 2.7+ and PyPy
        * 34 stars on GitHub 
        * 3.4k downloads / month

   *this slide is just text*

### CONTRIBUTING - 1 MINUTE
   * Submit a pull request to GitHub
   * Areas for contribution
       * Parsing could be better
       * External docs could be better
   * Building on top
       * Xdoctest exposes an easy way to parse doctests and get line numbers. There are cool refactoring tools that could be built on top of its framework

   *shows xdoctest GitHub page with CI badges*

### SUMMARY & CONCLUSION - 1 MINUTE
   * Introduction to Doctests
       * What it was
       * Strengths
       * Weaknesses
   * Xdoctest
       * Improvements
       * Limitations
       * Cool stuff
   * Questions (time permitting)

   *shows image of Noam Chomsky reminding the audience that regular expressions are for tokens and abstract syntax trees are for Python code*
