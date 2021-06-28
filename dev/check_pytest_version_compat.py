
import os
import ubelt as ub
from distutils.version import LooseVersion

os.chdir(ub.expandpath("$HOME/code/pytest"))

info = ub.cmd('git tag')

tags = [t for t in info['out'].split('\n') if t]
tags = sorted(tags, key=LooseVersion)

has_ispytest = {}
language_classifiers = {}

for tag in ub.ProgIter(tags):
    ub.cmd('git checkout {}'.format(tag))
    info = ub.cmd('grep -I -ER _ispytest')
    has_ispytest[tag] = len(info['out'].strip()) > 0
    info = ub.cmd('grep -I -ER "Programming Language :: Python" setup.cfg')
    language_classifiers[tag] = info['out']


for tag, flag in has_ispytest.items():
    if flag:
        break
print('First tag with _pytest = {!r}'.format(tag))


pythonversion_to_supported = ub.ddict(list)
for tag, clfs in language_classifiers.items():
    if clfs != '':
        for line in clfs.split('\n'):
            pythonversion_to_supported[line.strip()].append(tag)


keys = [
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',

]
for key in keys:
    cands = pythonversion_to_supported[key]
    if cands:
        max_version = max(cands, key=LooseVersion)
        print('key = {} max_version = {!r}'.format(key, max_version))

# key = Programming Language :: Python :: 2.7 max_version = '4.6.11'
# key = Programming Language :: Python :: 3.4 max_version = '4.6.11'
# key = Programming Language :: Python :: 3.5 max_version = '6.2.0.dev0'
# key = Programming Language :: Python :: 3.6 max_version = '6.3.0.dev0'
# key = Programming Language :: Python :: 3.7 max_version = '6.3.0.dev0'
# key = Programming Language :: Python :: 3.8 max_version = '6.3.0.dev0'
# key = Programming Language :: Python :: 3.9 max_version = '6.3.0.dev0'
