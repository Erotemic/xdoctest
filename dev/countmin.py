
def main():
    import re
    pat = re.compile(r'.*- (?P<num>\d) minute.*')
    n = 0
    matches = []
    for line in open('outline.md', 'r').read().splitlines():
        match = pat.match(line)
        if match:
            # print('line = {!r}'.format(line))
            print('match = {!r}'.format(match))
            n += int(match.groupdict()['num'])
            matches += [match]
    print('n = {!r}'.format(n))
    print(len(matches))


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/dev/countmin.py
    """
    main()
