#!/bin/bash
__heredoc__="""
Script to publish a new version of this library on PyPI

TODO:
    - [ ] Do a digital signature of release

Requirements:
     twine

Notes:
    # NEW API TO UPLOAD TO PYPI
    # https://packaging.python.org/tutorials/distributing-packages/

Usage:
    cd <YOUR REPO>

    git fetch --all
    git checkout release
    git pull 

    gitk --all

    ./publish

    git checkout -b dev/<next>
"""
if [[ "$USER" == "joncrall" ]]; then
    GITHUB_USERNAME=erotemic
fi

# First tag the source-code
VERSION=$(python -c "import setup; print(setup.parse_version())")
BRANCH=${TRAVIS_BRANCH:=$(git branch | grep \* | cut -d ' ' -f2)}
DEPLOY_BRANCH=release
ANS=$1
USE_GPG="True"


echo "
=== PYPI BUILDING SCRIPT ==
BRANCH = $BRANCH
DEPLOY_BRANCH = $DEPLOY_BRANCH
VERSION = '$VERSION'
GITHUB_USERNAME = $GITHUB_USERNAME
"

echo "LIVE BUILDING"
# Build wheel and source distribution
python setup.py bdist_wheel --universal
python setup.py sdist 

BDIST_WHEEL_PATH=$(ls dist/*-$VERSION-*.whl)
SDIST_PATH=$(dir dist/*-$VERSION*.tar.gz)
echo "
SDIST_PATH=$SDIST_PATH
BDIST_WHEEL_PATH=$BDIST_WHEEL_PATH
"

if [ "$USE_GPG" == "True" ]; then
    echo "
    === GPG SIGN ===
    "
    # https://stackoverflow.com/questions/45188811/how-to-gpg-sign-a-file-that-is-built-by-travis-ci
    # secure gpg --export-secret-keys > all.gpg
    rm dist/*.asc
    gpg --detach-sign -a $BDIST_WHEEL_PATH
    gpg --detach-sign -a $SDIST_PATH

    twine check $BDIST_WHEEL_PATH.asc $BDIST_WHEEL_PATH
    twine check $SDIST_PATH.asc $SDIST_PATH

    gpg --verify $BDIST_WHEEL_PATH.asc $BDIST_WHEEL_PATH 
    gpg --verify $SDIST_PATH.asc $SDIST_PATH 
fi


echo "
=== PYPI PUBLISHING SCRIPT ==
BRANCH = $BRANCH
DEPLOY_BRANCH = $DEPLOY_BRANCH
VERSION = '$VERSION'
GITHUB_USERNAME = $GITHUB_USERNAME
"

# Verify that we want to publish
if [[ "$ANS" != "yes" ]]; then
    read -p "Are you ready to publish version=$VERSION on branch=$BRANCH? (input 'yes' to confirm)" ANS
    echo "ANS = $ANS"
else
    echo "publishing version=$VERSION on branch=$BRANCH" 
fi

if [[ "$ANS" == "yes" ]]; then

    if [[ "$BRANCH" == "$DEPLOY_BRANCH" ]]; then
        echo "BRANCH = $BRANCH"
        git tag $VERSION -m "tarball tag $VERSION"
        git push --tags origin $DEPLOY_BRANCH
        if [ "$USE_GPG" == "True" ]; then
            twine upload --username $GITHUB_USERNAME --password=$TWINE_PASSWORD --sign $BDIST_WHEEL_PATH.asc $BDIST_WHEEL_PATH
            twine upload --username $GITHUB_USERNAME --password=$TWINE_PASSWORD --sign $SDIST_PATH.asc $SDIST_PATH
        else
            twine upload --username $GITHUB_USERNAME --password=$TWINE_PASSWORD $BDIST_WHEEL_PATH 
            twine upload --username $GITHUB_USERNAME --password=$TWINE_PASSWORD $SDIST_PATH 
        fi
    else
        echo "ONLY ABLE TO PUBLISH ON DEPLOY BRANCH

        BRANCH = $BRANCH
        DEPLOY_BRANCH = $DEPLOY_BRANCH
        "
    fi

    __notes__="""
    Notes:
        # References: https://docs.travis-ci.com/user/deployment/pypi/
        travis encrypt TWINE_PASSWORD=$TWINE_PASSWORD  
        travis encrypt GITHUB_USERNAME=$GITHUB_USERNAME 
    """
else  
    echo "Dry run"
fi
