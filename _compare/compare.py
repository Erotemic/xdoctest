"""
Compare xdoctest with doctest

This file autogenreates two files: compare_doctest.py and compare_xdoctset.py
They will have the same body up until the main block as defined in base.py. One
will run doctest and the other will run xdoctest. See the difference.
"""
import ubelt as ub


def generate():
    content = ub.readfrom('base.py') + '\n\n'
    xdoc_version = content + ub.codeblock(
        '''
        if __name__ == '__main__':
            import xdoctest
            xdoctest.doctest_module(__file__)
        ''') + '\n'

    doc_version = content + ub.codeblock(
        '''
        if __name__ == '__main__':
            import doctest
            doctest.testmod()
        ''') + '\n'

    ub.writeto('_doc_version.py', doc_version)
    ub.writeto('_xdoc_version.py', xdoc_version)


def main():
    generate()
    # Run the files

    print('\n\n' + ub.codeblock(
        '''
        ___  ____ ____ ___ ____ ____ ___
        |  \ |  | |     |  |___ [__   |
        |__/ |__| |___  |  |___ ___]  |

        Cant do most of this in doctest, although apparently you can
        use asserts, whereas I previously thought they didnt work
        ''') + '\n\n')

    ub.cmd('python _doc_version.py', verbout=1, verbose=2)

    print('\n\n' + ub.codeblock(
        '''
        _  _ ___  ____ ____ ___ ____ ____ ___
         \/  |  \ |  | |     |  |___ [__   |
        _/\_ |__/ |__| |___  |  |___ ___]  |

        Just run the assert failure to illustrate how failures look
        ''') + '\n\n')
    ub.cmd('python _xdoc_version.py do_asserts_work --demo-failure', verbout=1, verbose=2)

    print('\n\n' + ub.codeblock(
        '''
        _  _ ___  ____ ____ ___ ____ ____ ___
         \/  |  \ |  | |     |  |___ [__   |
        _/\_ |__/ |__| |___  |  |___ ___]  |

        Run all other tests, to show how the ast based xdoctest can deal with
        syntax that regex based doctest cannot handle.
        ''') + '\n\n')
    ub.cmd('python _xdoc_version.py all', verbout=1, verbose=2)


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/_compare/compare.py all
        python xdoc_version.py all
        python doc_version.py
    """
    main()
