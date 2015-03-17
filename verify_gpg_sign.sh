#!/bin/bash

total=0
passed=0
failed=0
other=0

for arg in "$@"; do
	sign="$arg"
	tar="${sign%.*}"
	xz="${sign%.*}.xz"
	echo Decompressing \"$(basename "$xz")\" and verifying it with \"$(basename "$sign")\"...
	echo 
	result=$(xz -cd "$xz" | gpg --verify "$sign" - 2>&1)
	echo "$result" 
	echo  
	(( total = total + 1 ))
	if [[ $result == *"gpg: Good signature from"* ]]; then
		(( passed = passed + 1 ))
	elif [[ $result == *"gpg: BAD signature from"* ]]; then
		(( failed = failed + 1 ))
	else
		(( other = other + 1 ))
	fi
done
echo Total: $total. Passed: $passed. Failed: $failed. Other: $other.
echo Done.
