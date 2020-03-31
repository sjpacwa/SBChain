for i in `find . -path ./venv -prune -o -name '*.py'`; do sed -e 's/\t/    /g' $i > "${i}.bak"; mv "${i}.bak" $i; done
