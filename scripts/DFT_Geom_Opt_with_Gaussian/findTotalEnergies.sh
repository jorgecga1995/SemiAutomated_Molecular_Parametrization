#!/bin/bash

find . -type f -name "*.log" -exec perl -0777 -ne '
    my $content = $_;
    $content =~ s/\s+//g; 
    while ($content =~ /\\(ETot=[^\\]+)\\/g) { 
        my @path = split("/", $ARGV); 
        print $path[-1] . ": " . $1 . "\n"; 
    }
' {} +