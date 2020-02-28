#./setup.py build
#(cd _skbuild/*/cmake-install/ && python -c "import my_ext")
#(cd _skbuild/*/cmake-install/ && xdoctest -m my_ext)
pip install --target="$(pwd)" .
python -c "import my_ext"
xdoctest -m my_ext
