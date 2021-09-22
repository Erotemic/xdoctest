__doc__="
Development script for updating secrets when they rotate
"

cd $HOME/code/xdoctest

# Load or generate secrets
source $(secret_loader.sh)
echo $PYUTILS_TWINE_USERNAME
CI_SECRET=$EROTEMIC_CI_SECRET
echo "CI_SECRET = $CI_SECRET"

# ADD RELEVANT VARIABLES TO THE CI SECRET VARIABLES

# HOW TO ENCRYPT YOUR SECRET GPG KEY
# You need to have a known public gpg key for this to make any sense
IDENTIFIER="=Erotemic-CI <erotemic@gmail.com>"
GPG_KEYID=$(gpg --list-keys --keyid-format LONG "$IDENTIFIER" | head -n 2 | tail -n 1 | awk '{print $1}')
echo "GPG_KEYID = $GPG_KEYID"

# Export plaintext gpg public keys, private keys, and trust info
mkdir -p dev
gpg --armor --export-options export-backup --export-secret-subkeys ${GPG_KEYID} > dev/ci_secret_gpg_subkeys.pgp
gpg --armor --export ${GPG_KEYID} > dev/ci_public_gpg_key.pgp

# Encrypt gpg keys and trust with CI secret
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/ci_public_gpg_key.pgp > dev/ci_public_gpg_key.pgp.enc
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -e -a -in dev/ci_secret_gpg_subkeys.pgp > dev/ci_secret_gpg_subkeys.pgp.enc
echo $GPG_KEYID > dev/public_gpg_key

# Test decrpyt
cat dev/public_gpg_key
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_public_gpg_key.pgp.enc | gpg --list-packets --verbose
GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_secret_gpg_subkeys.pgp.enc  | gpg --list-packets --verbose

source $(secret_unloader.sh)

# Look at what we did, clean up, and add it to git
ls dev/*.enc
rm dev/*.pgp
git status
git add dev/*.enc
git add dev/public_gpg_key


_test_gnu(){

    export GNUPGHOME=$HOME/tmp-gpg-testbed3
    mkdir -p $GNUPGHOME
    ls -al $GNUPGHOME
    chmod 700 -R $GNUPGHOME

    gpg -k
    source $(secret_loader.sh)
    CI_SECRET=$EROTEMIC_CI_SECRET
    echo "CI_SECRET = $CI_SECRET"

    cat dev/public_gpg_key
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_public_gpg_key.pgp.enc 
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_secret_gpg_subkeys.pgp.enc

    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_public_gpg_key.pgp.enc | gpg --import
    GLKWS=$CI_SECRET openssl enc -aes-256-cbc -pbkdf2 -md SHA512 -pass env:GLKWS -d -a -in dev/ci_secret_gpg_subkeys.pgp.enc | gpg --import

    gpg -k
    # | gpg --import
    # | gpg --list-packets --verbose

}
