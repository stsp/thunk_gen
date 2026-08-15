import sys
import ply.lex as lex

tokens = [
    'LB', 'RB', 'SEMIC', 'COMMA', 'ASTER', 'NEWLINE', 'STRING', 'NUM',
    'ASMCFUNC', 'ASMPASCAL', 'FAR', 'SEGM', 'INITTEXT',
    'VOID', 'WORD', 'UWORD', 'CHAR', 'BYTE', 'UBYTE',
    'DWORD', 'UDWORD', 'DOUBLE', 'LDOUBLE', 'FLOAT',
    'QWORD', 'UQWORD', 'STRUCT', 'UNION',
    'LBR', 'RBR', 'CONST', 'OUT',
    'NORETURN', 'V_FW', 'V_BW',
]

t_LB = r'\('
t_RB = r'\)'
t_SEMIC = r';'
t_COMMA = r','
t_ASTER = r'\*'
t_NEWLINE = r'\n'
t_LBR = r'\['
t_RBR = r'\]'


def t_ASMCFUNC(t):
    r'ASMCFUNC'
    return t


def t_ASMPASCAL(t):
    r'ASMPASCAL'
    return t


def t_INITTEXT(t):
    r'INITTEXT'
    return t


def t_SEGM(t):
    r'SEGM'
    return t


def t_NORETURN(t):
    r'NORETURN'
    return t


def t_V_FW(t):
    r'_V_FW'
    return t


def t_V_BW(t):
    r'_V_BW'
    return t


def t_UQWORD(t):
    r'unsigned\ long\ long'
    return t


def t_LDOUBLE(t):
    r'long\ double'
    return t


def t_UDWORD_ulong(t):
    r'unsigned\ long'
    t.type = 'UDWORD'
    return t


def t_UDWORD_uint(t):
    r'unsigned\ int'
    t.type = 'UDWORD'
    return t


def t_UWORD_ushort(t):
    r'unsigned\ short'
    t.type = 'UWORD'
    return t


def t_UBYTE_uchar(t):
    r'unsigned\ char'
    t.type = 'UBYTE'
    return t


def t_QWORD(t):
    r'long\ long'
    return t


def t_DWORD_ssize(t):
    r'ssize_t'
    t.type = 'DWORD'
    return t


def t_DWORD_long(t):
    r'long'
    t.type = 'DWORD'
    return t


def t_DWORD_int(t):
    r'int'
    t.type = 'DWORD'
    return t


def t_UWORD_uint16(t):
    r'uint16_t'
    t.type = 'UWORD'
    return t


def t_WORD_int16(t):
    r'int16_t'
    t.type = 'WORD'
    return t


def t_WORD_short(t):
    r'short'
    t.type = 'WORD'
    return t


def t_UWORD_count(t):
    r'UCOUNT'
    t.type = 'UWORD'
    return t


def t_WORD_count(t):
    r'COUNT'
    t.type = 'WORD'
    return t


def t_WORD_bool(t):
    r'BOOL'
    t.type = 'WORD'
    return t


def t_UDWORD_size(t):
    r'size_t'
    t.type = 'UDWORD'
    return t


def t_UDWORD_ulong32(t):
    r'ULONG32'
    t.type = 'UDWORD'
    return t


def t_DWORD_long32(t):
    r'LONG32'
    t.type = 'DWORD'
    return t


def t_DWORD_longkw(t):
    r'LONG'
    t.type = 'DWORD'
    return t


def t_UDWORD_ulongkw(t):
    r'ULONG'
    t.type = 'UDWORD'
    return t


def t_DWORD_dword(t):
    r'DWORD'
    return t


def t_UDWORD_udword(t):
    r'UDWORD'
    return t


def t_UWORD_uword(t):
    r'UWORD'
    return t


def t_WORD_word(t):
    r'WORD'
    return t


def t_UBYTE(t):
    r'UBYTE'
    return t


def t_BYTE(t):
    r'BYTE'
    return t


def t_FLOAT(t):
    r'float'
    return t


def t_DOUBLE(t):
    r'double'
    return t


def t_VOID(t):
    r'VOID|void'
    return t


def t_CHAR(t):
    r'char'
    return t


def t_STRUCT(t):
    r'struct'
    return t


def t_UNION(t):
    r'union'
    return t


def t_CONST(t):
    r'const'
    return t


def t_OUT(t):
    r'__out'
    return t


def t_FAR(t):
    r'FAR|far'
    return t


def t_NUM(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t


def t_STRING(t):
    r'[_A-Za-z][_A-Za-z0-9]*'
    return t


t_ignore = ' \t'


def t_COMMENT(t):
    r'/\*.*?\*/'
    pass


def t_error(t):
    print("Illegal character '%s'" % t.value[0], file=sys.stderr)
    t.lexer.skip(1)


lexer = lex.lex()
