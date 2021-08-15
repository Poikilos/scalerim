#!/bin/sh
maintainer_dir="$HOME/Downloads/git/amadvance"
mkdir -p "$maintainer_dir"
if [ $? -ne 0 ]; then
    echo "Error: 'mkdir -p \"$maintainer_dir\"' failed."
    exit 1
fi
cd "$maintainer_dir"
if [ $? -ne 0 ]; then
    echo "Error: 'cd \"$maintainer_dir\"' failed."
    exit 1
fi
repo_name="scale2x"
repo_url="https://github.com/amadvance/scale2x"
if [ ! -d "$repo_name" ]; then
    if [ ! -f "`command -v git`" ]; then
        echo "Error: git is required to download $repo_url since the $repo_name directory doesn't exist in \"`pwd`\"."
        exit 1
    fi

    git clone "$repo_url" "$repo_name"
    if [ $? -ne 0 ]; then
        echo "Error: 'git clone \"$repo_url\" \"$repo_name\"' failed in \"`pwd`\"."
        exit 1
    fi
    cd "$repo_name"
    if [ $? -ne 0 ]; then
        echo "Error: 'cd \"$repo_name\"' failed in \"`pwd`\"."
        exit 1
    fi
else
    cd "$repo_name"
    if [ $? -ne 0 ]; then
        echo "Error: 'cd \"$repo_name\"' failed in \"`pwd`\"."
        exit 1
    fi
    git pull
    if [ $? -ne 0 ]; then
        echo "Warning: 'git pull' failed in \"`pwd`\"."
    fi
fi

./configure
if [ $? -ne 0 ]; then
    echo "Error: './configure' failed in \"`pwd`\". See errors above for details."
    exit 1
fi
make
if [ $? -ne 0 ]; then
    echo "Error: 'make' failed in \"`pwd`\". See errors above for details."
    exit 1
fi
echo "* Installing the scalerx command..."
sudo make install
if [ $? -ne 0 ]; then
    echo "Error: 'make' failed in \"`pwd`\". See errors above for details."
    exit 1
fi
echo "(Finished OK)"
exit 0
