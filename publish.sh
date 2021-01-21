#!/bin/bash
__heredoc__='''
Script to publish a new version of this library on PyPI. 

If your script has binary dependencies then we assume that you have built a
proper binary wheel with auditwheel and it exists in the wheelhouse directory.
Otherwise, for source tarballs and universal wheels this script runs the
setup.py script to create the wheels as well.

Running this script with the default arguments will perform any builds and gpg
signing, but nothing will be uploaded to pypi unless the user explicitly sets
TAG_AND_UPLOAD=True or answers yes to the prompts.

Args:
    # These environment variables must / should be set
    TWINE_USERNAME : username for pypi
    TWINE_PASSWORD : password for pypi
    USE_GPG : defaults to True

Requirements:
     twine >= 1.13.0
     gpg2 >= 2.2.4
     OpenSSL >= 1.1.1c

Notes:
    # NEW API TO UPLOAD TO PYPI
    # https://docs.travis-ci.com/user/deployment/pypi/
    # https://packaging.python.org/tutorials/distributing-packages/
    # https://stackoverflow.com/questions/45188811/how-to-gpg-sign-a-file-that-is-built-by-travis-ci

Usage:
    cd <YOUR REPO>

    # Set your variables or load your secrets
    export TWINE_USERNAME=<pypi-username>
    export TWINE_PASSWORD=<pypi-password>

    source $(secret_loader.sh)

    MB_PYTHON_TAG=cp38-cp38m 
    MB_PYTHON_TAG=cp37-cp37m 
    MB_PYTHON_TAG=cp36-cp36m 
    MB_PYTHON_TAG=cp35-cp35m 
    MB_PYTHON_TAG=cp27-cp27mu

    echo "MB_PYTHON_TAG = $MB_PYTHON_TAG"
    MB_PYTHON_TAG=$MB_PYTHON_TAG ./run_multibuild.sh
    DEPLOY_REMOTE=ibeis MB_PYTHON_TAG=$MB_PYTHON_TAG ./publish.sh yes

    MB_PYTHON_TAG=py3-none-any ./publish.sh
'''

check_variable(){
    KEY=$1
    HIDE=$2
    VAL=${!KEY}
    if [[ "$HIDE" == "" ]]; then
        echo "[DEBUG] CHECK VARIABLE: $KEY=\"$VAL\""
    else
        echo "[DEBUG] CHECK VARIABLE: $KEY=<hidden>"
    fi
    if [[ "$VAL" == "" ]]; then
        echo "[ERROR] UNSET VARIABLE: $KEY=\"$VAL\""
        exit 1;
    fi
}

# Options
DEPLOY_REMOTE=${DEPLOY_REMOTE:=origin}
NAME=${NAME:=$(python -c "import setup; print(setup.NAME)")}
VERSION=$(python -c "import setup; print(setup.VERSION)")
MB_PYTHON_TAG=${MB_PYTHON_TAG:py3-none-any}

# The default should change depending on the application
#DEFAULT_MODE_LIST=("sdist" "universal" "bdist")
DEFAULT_MODE_LIST=("sdist" "native" "universal")
#DEFAULT_MODE_LIST=("sdist" "bdist")

check_variable DEPLOY_REMOTE
check_variable VERSION || exit 1

TAG_AND_UPLOAD=${TAG_AND_UPLOAD:=$1}
TWINE_USERNAME=${TWINE_USERNAME:=""}
TWINE_PASSWORD=${TWINE_PASSWORD:=""}

USE_GPG=${USE_GPG:="True"}

if [[ "$(which gpg2)" != "" ]]; then
    GPG_EXECUTABLE=${GPG_EXECUTABLE:=gpg2}
else
    GPG_EXECUTABLE=${GPG_EXECUTABLE:=gpg}
fi

GPG_KEYID=${GPG_KEYID:=$(git config --local user.signingkey)}
GPG_KEYID=${GPG_KEYID:=$(git config --global user.signingkey)}


echo "
=== PYPI BUILDING SCRIPT ==
VERSION='$VERSION'
TWINE_USERNAME='$TWINE_USERNAME'
GPG_KEYID = '$GPG_KEYID'
MB_PYTHON_TAG = '$MB_PYTHON_TAG'
"


echo "
=== <BUILD WHEEL> ===
"



echo "LIVE BUILDING"
# Build wheel and source distribution

MODE=${MODE:=all}

if [[ "$MODE" == "all" ]]; then
    MODE_LIST=("${DEFAULT_MODE_LIST[@]}")
else
    MODE_LIST=("$MODE")
fi

MODE_LIST_STR=$(printf '"%s" ' "${MODE_LIST[@]}")

WHEEL_PATHS=()
for _MODE in "${MODE_LIST[@]}"
do
    echo "_MODE = $_MODE"
    if [[ "$_MODE" == "sdist" ]]; then
        python setup.py sdist || { echo 'failed to build sdist wheel' ; exit 1; }
        WHEEL_PATH=$(ls dist/$NAME-$VERSION*.tar.gz)
        WHEEL_PATHS+=($WHEEL_PATH)
    elif [[ "$_MODE" == "native" ]]; then
        python setup.py bdist_wheel || { echo 'failed to build native wheel' ; exit 1; }
        WHEEL_PATH=$(ls dist/$NAME-$VERSION*.whl)
        WHEEL_PATHS+=($WHEEL_PATH)
    elif [[ "$_MODE" == "universal" ]]; then
        python setup.py bdist_wheel --universal || { echo 'failed to build universal wheel' ; exit 1; }
        UNIVERSAL_TAG="py3-none-any"
        WHEEL_PATH=$(ls dist/$NAME-$VERSION-$UNIVERSAL_TAG*.whl)
        WHEEL_PATHS+=($WHEEL_PATH)
    elif [[ "$_MODE" == "bdist" ]]; then
        echo "Assume wheel has already been built"
        WHEEL_PATH=$(ls wheelhouse/$NAME-$VERSION-$MB_PYTHON_TAG*.whl)
        WHEEL_PATHS+=($WHEEL_PATH)
    else
        echo "bad mode"
        exit 1
    fi
    echo "WHEEL_PATH = $WHEEL_PATH"
done

WHEEL_PATHS_STR=$(printf '"%s" ' "${WHEEL_PATHS[@]}")

echo "
MODE=$MODE
VERSION='$VERSION'
WHEEL_PATHS='$WHEEL_PATHS_STR'
"

echo "
=== <END BUILD WHEEL> ===
"

echo "
=== <GPG SIGN> ===
"


for WHEEL_PATH in "${WHEEL_PATHS[@]}"
do
    echo "WHEEL_PATH = $WHEEL_PATH"
    check_variable WHEEL_PATH
    if [ "$USE_GPG" == "True" ]; then
        # https://stackoverflow.com/questions/45188811/how-to-gpg-sign-a-file-that-is-built-by-travis-ci
        # secure gpg --export-secret-keys > all.gpg

        # REQUIRES GPG >= 2.2
        check_variable GPG_EXECUTABLE || { echo 'failed no gpg exe' ; exit 1; }
        check_variable GPG_KEYID || { echo 'failed no gpg key' ; exit 1; }

        echo "Signing wheels"
        GPG_SIGN_CMD="$GPG_EXECUTABLE --batch --yes --detach-sign --armor --local-user $GPG_KEYID"
        echo "GPG_SIGN_CMD = $GPG_SIGN_CMD"
        $GPG_SIGN_CMD --output $WHEEL_PATH.asc $WHEEL_PATH

        echo "Checking wheels"
        twine check $WHEEL_PATH.asc $WHEEL_PATH || { echo 'could not check wheels' ; exit 1; }

        echo "Verifying wheels"
        $GPG_EXECUTABLE --verify $WHEEL_PATH.asc $WHEEL_PATH || { echo 'could not verify wheels' ; exit 1; }
    else
        echo "USE_GPG=False, Skipping GPG sign"
    fi
done
echo "
=== <END GPG SIGN> ===
"

# Verify that we want to publish
if [[ "$TAG_AND_UPLOAD" == "yes" ]]; then
    echo "About to publish VERSION='$VERSION'" 
else
    if [[ "$TAG_AND_UPLOAD" == "no" ]]; then
        echo "We are NOT about to publish VERSION='$VERSION'" 
    else
        read -p "Are you ready to publish version='$VERSION'? (input 'yes' to confirm)" ANS
        echo "ANS = $ANS"
        TAG_AND_UPLOAD="$ANS"
    fi
fi


if [[ "$TAG_AND_UPLOAD" == "yes" ]]; then
    check_variable TWINE_USERNAME
    check_variable TWINE_PASSWORD "hide"

    #git tag $VERSION -m "tarball tag $VERSION"
    #git push --tags $DEPLOY_REMOTE $DEPLOY_BRANCH

    for WHEEL_PATH in "${WHEEL_PATHS[@]}"
    do
        if [ "$USE_GPG" == "True" ]; then
            twine upload --username $TWINE_USERNAME --password=$TWINE_PASSWORD --sign $WHEEL_PATH.asc $WHEEL_PATH  || { echo 'failed to twine upload' ; exit 1; }
        else
            twine upload --username $TWINE_USERNAME --password=$TWINE_PASSWORD $WHEEL_PATH  || { echo 'failed to twine upload' ; exit 1; }
        fi
    done
    echo """
        !!! FINISH: LIVE RUN !!!
    """
else
    echo """
        DRY RUN ... Skiping tag and upload

        DEPLOY_REMOTE = '$DEPLOY_REMOTE'
        TAG_AND_UPLOAD = '$TAG_AND_UPLOAD'
        WHEEL_PATH = '$WHEEL_PATH'
        WHEEL_PATHS_STR = '$WHEEL_PATHS_STR'
        MODE_LIST_STR = '$MODE_LIST_STR'

        VERSION='$VERSION'
        NAME='$NAME'
        TWINE_USERNAME='$TWINE_USERNAME'
        GPG_KEYID = '$GPG_KEYID'
        MB_PYTHON_TAG = '$MB_PYTHON_TAG'

        To do live run set TAG_AND_UPLOAD=yes and ensure deploy and current branch are the same

        !!! FINISH: DRY RUN !!!
    """
fi
