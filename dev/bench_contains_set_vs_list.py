

def main():
    import timerit
    ti = timerit.Timerit(1000, bestof=10, verbose=2)

    items = (['state3', 'state4'] * 50 + ['state1', 'state2'] * 500 + ['state1', 'state2', 'state3', 'state4', 'state1'] * 50) * 100

    for timer in ti.reset('list.2 contains'):
        with timer:
            for item in items:
                if item in ['state1', 'state2']:
                    pass

    for timer in ti.reset('set.2 contains'):
        with timer:
            for item in items:
                if item in {'state1', 'state2'}:
                    pass

    LIST_VAR = ['state1', 'state2']
    for timer in ti.reset('list.2 var contains'):
        with timer:
            for item in items:
                if item in LIST_VAR:
                    pass

    SET_VAR = {'state1', 'state2'}
    for timer in ti.reset('set.2 var contains'):
        with timer:
            for item in items:
                if item in SET_VAR:
                    pass

    print('\n----\n')

    for timer in ti.reset('list.1 contains'):
        with timer:

            for item in items:
                if item in ['state1']:
                    pass

    # Yes, there is a meaningful time difference.
    # Using set contains is faster
    for timer in ti.reset('set.1 contains'):
        with timer:

            for item in items:
                if item in {'state1'}:
                    pass


if __name__ == '__main__':
    """
    CommandLine:
        python ~/code/xdoctest/dev/bench_contains_set_vs_list.py
    """
    main()
