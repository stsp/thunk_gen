#!/usr/bin/env bash

set -o pipefail

gen_calls_tmp() {
	grep ASMCFUNC "$1" | grep -v "#define"
}

gen_plt_inc() {
	sed -E 's/([0-9]+).+ ([^ \(]+)*\(.*/asmcfunc_n \2, \1/' "$1"
}

gen_asms_tmp() {
	grep 'ASMFUNC\|ASMPASCAL' "$1" | grep -v "//" | grep -v "#define"
}

gen_plt_asmc() {
	grep ASMFUNC $1 | \
		sed -E 's/([0-9]+)[[:blank:]]+([^[:blank:]\(]+[[:blank:]]+)+([^ \(]+) *\(.+/ASMCSYM\(\3, \1\)/'
}

gen_plt_asmp() {
	grep ASMPASCAL "$1" | tr '[:lower:]' '[:upper:]' | \
		sed -E 's/([0-9]+).+ ([^ \(]+) *\(.+/ASMPSYM\(\3, \1\)/'
}

gen_h1() {
	sed -E -e 's/^([^\(]+ )([^ \(]+)/\1_FUNC\(\2\)/' "$1"
}

case "$1" in
1)
	gen_calls_tmp "$2"
	;;
2)
	gen_asms_tmp "$2"
	;;
3)
	gen_plt_inc "$2"
	;;
4)
	gen_plt_asmc "$2"
	;;
5)
	gen_plt_asmp "$2"
	;;
6|7)
	gen_h1 "$2"
	;;
esac
