#!/bin/bash
get_page_count() {
	# read file into an array of lines http://mandrivausers.org/index.php?/topic/21998-reading-a-text-file-line-by-line-with-bash/
	local old_IFS=$IFS # save the field separator
	IFS=$'\n' # linux/unix/OSX EOL
	local raw_input=($(pdftk "$1" dumpdata | grep PageMediaNumber:)) # array
	local raw_count=${#raw_input[*]} # line count
	IFS=$old_IFS # restore default field separator
	echo $raw_count
}

total_pages=0
total_files=0

for arg in "$@"; do
	dis_page_count=`get_page_count "$arg"`
	(( total_pages = $total_pages + $dis_page_count))
	fname[total_files]="$arg"
	fpage[total_files]="$dis_page_count"
	(( total_files = total_files + 1 ))
done

echo $total_pages pages in $# files.
echo ""
echo Page_count Filename
# lazy
d="d"
char=1
if (( "$total_pages" > 99 )); then
	char=3
else 
	if (( "$total_pages" > 9 )); then
		char=2
	fi
fi
for (( i=0; i<$total_files; i++ )); do
	echo "$(printf "%0$char$d" ${fpage[$i]})"   $(basename "${fname[$i]}")
done
