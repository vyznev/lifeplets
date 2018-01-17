#!/usr/bin/perl
use strict;
use warnings;
use feature qw(say);

$/ = "";                                           # tell <> to read up to next blank line
my @sizes;                                         # array of hashes to store patterns grouped by size
while (<>) {
    s/\n+$//;                                      # remove trailing linefeed for symmetry
    my $n = tr/#*/##/;                             # count number of live cells (and normalize symbol)
    my @pat = transpose($_);                       # transpose tall and narrow patterns
    push @pat, map scalar reverse, @pat;           # add 180 mirrored versions of pattern(s) to @pat
    push @pat, map s/(\S+)/reverse $1/egr, @pat;   # add horizontally mirrored versions to @pat
    @pat = sort @pat;                              # sort lexicographically to find canonical mirror version
    $sizes[$n]{$pat[0]}++;                         # add canonical version to collection for later printing
}

# print out the patterns sorted by size (and then lexicographically)
for my $n (0..$#sizes) {
    $sizes[$n] or next;
    my @patterns = sort keys %{$sizes[$n]};
    say num($n, "cell"), " (", num(scalar @patterns, "pattern"), "):\n";
    say "$_\n" for @patterns;
}

# transpose a pattern if it is taller than it is wide; for square
# patterns, returns both the original and the transposed version
# XXX: assumes that all rows in the pattern have the same length!
sub transpose {
    my $orig = shift;
    my @rows = split /\n/, $orig;
    my $cols = length($rows[0]);
    return $orig if @rows < $cols;
    my @trans;
    for my $col (0..$cols-1) {
	push @trans, join "", map substr($_, $col, 1), @rows;
    }
    my $trans = join "\n", @trans;
    return (@rows == $cols ? ($orig, $trans) : $trans);
}

# helper function for pluralization
sub num {
    my ($n, $word) = @_;
    $word .= "s" if $n != 1;
    return "$n $word";
}
