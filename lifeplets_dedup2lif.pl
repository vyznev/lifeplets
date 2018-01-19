#!/usr/bin/perl
use strict;
use warnings;
use feature qw(say);

# output parameters:
my $gridwidth = 160;  # arrange patterns in a grid at most this many cells wide
my $padding   = 2;    # leave at least this many empty rows/columns between patterns
my $groupgap  = 4;    # extra empty rows between different size groups

$/ = "";                                           # tell <> to read up to next blank line
my @sizes;                                         # array of hashes to store patterns grouped by size
while (<>) {
    s/\n+$//;                                      # remove trailing linefeed for symmetry
    my $n = tr/#*/**/;                             # count number of live cells (and normalize symbol)
    my @pat = transpose($_);                       # transpose tall and narrow patterns
    push @pat, map scalar reverse, @pat;           # add 180 mirrored versions of pattern(s) to @pat
    push @pat, map s/(\S+)/reverse $1/egr, @pat;   # add horizontally mirrored versions to @pat
    @pat = sort @pat;                              # sort lexicographically to find canonical mirror version
    $sizes[$n]{$pat[0]}++;                         # add canonical version to collection for later printing
}

# print out the patterns sorted by size (and then lexicographically)
say "#Life 1.05";
my $row = 0;
for my $n (0..$#sizes) {
    $sizes[$n] or next;
    my @patterns = sort keys %{$sizes[$n]};

    my $maxwidth = 0;
    $maxwidth < $_ and $maxwidth = $_ for map width($_), @patterns;

    my $col = 0;
    my $rowheight = 0;
    for my $pat (@patterns) {
	if ($col + $maxwidth > $gridwidth) {
	    $row += $rowheight + $padding;
	    $col = $rowheight = 0;
	}
	say "#P $col $row";
	say "$pat\n";
	my $height = height($pat);
	$rowheight = $height if $rowheight < $height;
	$col += $maxwidth + $padding;
    }
    $row += $rowheight + $padding if $col > 0;
    $row += $groupgap;
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

# determine height and width of a pattern
sub height {
    my @rows = split /\n/, shift;
    return scalar @rows;
}
sub width {
    my @rows = split /\n/, shift;
    return length $rows[0];
}
