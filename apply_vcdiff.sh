#!/bin/bash

total=0
passed=0
failed=0
other=0

for arg in "$@"; do
	echo Applying $(basename "$arg") with default settings...
	result=$(xdelta3 -d "$arg" 2>&1)
	RETVAL=$?
	echo "$result"
	echo ""
	(( total = total + 1 ))
	if [[ $RETVAL == 0 ]]; then
		(( passed = passed + 1 ))
	elif [[ $result == *"to overwrite output file specify -f"* ]]; then
		(( other = other + 1 ))
	elif [[ $result == *"No such file or directory"* ]]; then
		(( failed = failed + 1))
	else
		(( failed = failed + 1))
	fi
#	elif [[ $result == *"gpg: BAD signature from"* ]]; then
#		(( failed = failed + 1 ))
#	else
#		(( other = other + 1 ))
#	fi
done
echo Total: $total. Passed: $passed. Failed: $failed. Other: $other.
echo All done.
