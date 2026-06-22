#!/bin/bash

find . -type f -name "*.log" -exec perl -0777 -ne 'while (/\\(ETot=[^\\]+)\\/sg) { (my $val = $1) =~ s/\s+//g; my @path = split("/", $ARGV); print $path[-1] . ": " . $val . "\n"; }' {} +

