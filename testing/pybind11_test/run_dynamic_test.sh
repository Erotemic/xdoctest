#./setup.py build
#(cd _skbuild/*/cmake-install/ && python -c "import my_ext")
#(cd _skbuild/*/cmake-install/ && xdoctest -m my_ext)


pip install --target="$(pwd)" .
xdoctest -m my_ext

python -c "import my_ext"
