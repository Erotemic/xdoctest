

def main():
    flake8_errors = [
        'E126',  # continuation line hanging-indent
        'E127',  # continuation line over-indented for visual indent
        'E201',  # whitespace after '('
        'E202',  # whitespace before ']'
        'E203',  # whitespace before ', '
        'E221',  # multiple spaces before operator  (TODO: I wish I could make an exception for the equals operator. Is there a way to do this?)
        'E222',  # multiple spaces after operator
        'E241',  # multiple spaces after ,
        'E265',  # block comment should start with "# "
        'E271',  # multiple spaces after keyword
        'E272',  # multiple spaces before keyword
        'E301',  # expected 1 blank line, found 0
        'E305',  # expected 1 blank line after class / func
        'E306',  # expected 1 blank line before func
        #'E402',  # moduel import not at top
        'E501',  # line length > 79
        'W602',  # Old reraise syntax
        'E266',  # too many leading '#' for block comment
        'N801',  # function name should be lowercase [N806]
        'N802',  # function name should be lowercase [N806]
        'N803',  # argument should be lowercase [N806]
        'N805',  # first argument of a method should be named 'self'
        'N806',  # variable in function should be lowercase [N806]
        'N811',  # constant name imported as non constant
        'N813',  # camel case
        'W504',  # line break after binary operator
    ]
    flake8_args_list = [
        '--max-line-length 79',
        #'--max-line-length 100',
        '--ignore=' + ','.join(flake8_errors)
    ]
    flake8_args = ' '.join(flake8_args_list)

    import ubelt as ub
    import sys
    loc = ub.expandpath('~/code/xdoctest/xdoctest')
    command = 'flake8 ' + flake8_args + ' ' + loc
    print('command = {!r}'.format(command))
    info = ub.cmd(command, verbose=3)
    sys.exit(info['ret'])


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/dev/run_linter.py
    """
    main()
