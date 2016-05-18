---
cleveref: On
fignos-plus-name: FIG.
fignos-star-name: FIGURE
fignos-caption-name: FiG.
eqnos-plus-name: EQ.
eqnos-star-name: EQUATION
tablenos-plus-name: TAB.
tablenos-star-name: TABLE
xnos-cleveref-fake: Off
...

*@fig:1, +@fig:1, figure !@fig:1, and {@fig:1}.

![A simple figure. Refs to +@eq:1 and +@tbl:1.][Fig]

[Fig]: plot.png {#fig:1}

*@eq:1, +@eq:1, equation !@eq:1, and {@eq:1}.

$$ y = f(x) $$ {#eq:1}

*@tbl:1, +@tbl:1, table !@tbl:1, and {@tbl:1}.

  Right     Left     Center     Default
-------     ------ ----------   -------
     12     12        12            12
    123     123       123          123
      1     1          1             1

Table: A simple table. Refs to +@fig:1 and +@eq:1. {#tbl:1}
