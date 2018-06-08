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
        ''') + '\n\n')

    ub.cmd('python _doc_version.py', verbout=1, verbose=2)

    print('\n\n' + ub.codeblock(
        '''
        _  _ ___  ____ ____ ___ ____ ____ ___
         \/  |  \ |  | |     |  |___ [__   |
        _/\_ |__/ |__| |___  |  |___ ___]  |
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
