#!/usr/bin/perl
# T154 LEG 1 sweep: put LC_ALL=C and -a on every load-bearing grep in a file.
# Idempotent: a grep already carrying LC_ALL=C is left alone.
use strict; use warnings;
my $path = shift or die "usage: $0 <file>\n";
open my $in, '<:raw', $path or die $!;
my @lines = <$in>; close $in;
my $n = 0;
for my $l (@lines) {
    next if $l =~ /^\s*#/;                 # comments are prose, not commands
    next if $l =~ /LC_ALL=C\s+grep/;       # already hardened
    # `grep` as a command word: at start of a command position.
    $n += ($l =~ s{(\A|[|(]\s*|\&\&\s*|\|\|\s*|;\s*|\$\(\s*|!\s+)grep\s+-([A-Za-z])}{$1LC_ALL=C grep -a$2}g);
}
open my $out, '>:raw', $path or die $!;
print $out @lines; close $out;
print "hardened $n grep invocation(s) in $path\n";
