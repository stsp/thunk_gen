# thunk template generator for fdpp

m4_define([sp_num], [[#]$1
])
# bison doesn't like m4_ macros (warns), so alias it to nl
m4_define([nl], [m4_newline($@)])

# foru - upcounting loop.
m4_define(foru, [m4_cond(m4_eval($3>=$2), 1, [m4_for([$1],[$2],[$3],,[$4])])])

# generate stack layout
m4_define(G_S0, [foru(i, 1, $1, [aat[]i a[]i; \
m4_if($1, i,, [        ])])])
m4_define(G_S1, [foru(i, 1, $1, [aat[]m4_eval($1-i+1) a[]m4_eval($1-i+1); \
m4_if($1, i,, [        ])])])

# generate initializers
m4_define(G_I0, [foru(i, 1, $1, [_a[]i[]m4_if($1, i,, [, ])])])
m4_define(G_I1, [foru(i, 1, $1, [_a[]m4_eval($1-i+1)[]m4_if($1, i,, [, ])])])

# generate args
m4_define(G_A, [m4_if($1, 0, [NULL, 0], [(UBYTE *)&_args, sizeof(_args)])])

m4_define(THUNK,
[[#]define _THUNK$1$4([n, r], m4_cond($2, 0, [s, ])f, foru(i, 1, $1,
  [t[]i, q[]i, at[]i, aat[]i, c[]i, l[]i, ])z) \
r f(m4_if($1, 0, void, [foru(i, 1, $1,
[t[]i a[]i q[]i[]m4_if($1, i,, [, ])])])) \
{ \
    const uint32_t _flags = z; \
m4_cond($2, 0, [dnl
    uint32_t _ret; \
])dnl
foru(i, 1, $1, [dnl
    _CNV(c[]i, t[]i, at[]i, l[]i, i); \
])dnl
m4_if($1, 0,, [dnl
    struct { \
        G_S$3($1)dnl
    } PACKED _args = { G_I$3($1) }; \
])dnl
m4_if($2, 0, [dnl
    _ret = ], [dnl
    ])__CALL$4(n, G_A($1), _flags); \
m4_if(m4_eval($2<2), 1, [dnl
foru(i, 1, $1, [dnl
    _UCNV(c[]i, l[]i, i); \
])dnl
m4_cond(m4_eval($3==0&&$1>0), 1, [dnl
    __CSTK(sizeof(_args)); \
])dnl
],[dnl
    /* noreturn */ \
])dnl
m4_cond($2, 0, [dnl
    return s(r, _ret); \
])dnl
}dnl
])

# now enable output. Should do it last to not get newlines from
# defines or comments.
m4_define([_m4_divert(STDOUT)], 1)
m4_divert_push([STDOUT])dnl
