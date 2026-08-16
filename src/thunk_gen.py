#!/usr/bin/env python3
"""
function prototype parser
Author: Stas Sergeev / ported to PLY
"""

import getopt
import sys

from ply import lex, yacc

VERSION = "1.11"

# Lexer tokens
tokens = (
    'NUM',
    'LB',
    'RB',
    'SEMIC',
    'COMMA',
    'ASMCFUNC',
    'ASMPASCAL',
    'INITTEXT',
    'SEGM',
    'FAR',
    'ASTER',
    'LBR',
    'RBR',
    'VOID',
    'WORD',
    'UWORD',
    'CHAR',
    'BYTE',
    'UBYTE',
    'DWORD',
    'UDWORD',
    'QWORD',
    'UQWORD',
    'FLOAT',
    'DOUBLE',
    'LDOUBLE',
    'STRUCT',
    'UNION',
    'CONST',
    'OUT',
    'NORETURN',
    'V_FW',
    'V_BW',
    'STRING',
)

# Multi-word types/keywords
def t_MULTIWORD(t):
    r'unsigned\s+long\s+long|long\s+long|unsigned\s+short|unsigned\s+char|unsigned\s+int|unsigned\s+long|long\s+double'
    val = " ".join(t.value.split())
    if val == "unsigned long long":
        t.type = 'UQWORD'
    elif val == "long long":
        t.type = 'QWORD'
    elif val == "unsigned short":
        t.type = 'UWORD'
    elif val == "unsigned char":
        t.type = 'UBYTE'
    elif val == "unsigned int" or val == "unsigned long":
        t.type = 'UDWORD'
    elif val == "long double":
        t.type = 'LDOUBLE'
    return t

def t_COMMENT(t):
    r'/\*.*?\*/'

def t_ASMFUNC(t):
    r'ASMFUNC'

t_ignore = ' \t\r\n'

t_LB = r'\('
t_RB = r'\)'
t_SEMIC = r';'
t_COMMA = r','
t_ASTER = r'\*'
t_LBR = r'\['
t_RBR = r'\]'

reserved = {
    'ASMCFUNC': 'ASMCFUNC',
    'ASMPASCAL': 'ASMPASCAL',
    'INITTEXT': 'INITTEXT',
    'SEGM': 'SEGM',
    'FAR': 'FAR',
    'far': 'FAR',
    'VOID': 'VOID',
    'void': 'VOID',
    'WORD': 'WORD',
    'COUNT': 'WORD',
    'BOOL': 'WORD',
    'char': 'CHAR',
    'short': 'WORD',
    'UCOUNT': 'UWORD',
    'UWORD': 'UWORD',
    'BYTE': 'BYTE',
    'UBYTE': 'UBYTE',
    'int': 'DWORD',
    'unsigned': 'UDWORD',
    'long': 'DWORD',
    'size_t': 'UDWORD',
    'ssize_t': 'DWORD',
    'int16_t': 'WORD',
    'uint16_t': 'UWORD',
    'int32_t': 'DWORD',
    'uint32_t': 'UDWORD',
    'LONG': 'DWORD',
    'LONG32': 'DWORD',
    'ULONG': 'UDWORD',
    'ULONG32': 'UDWORD',
    'DWORD': 'DWORD',
    'UDWORD': 'UDWORD',
    'float': 'FLOAT',
    'double': 'DOUBLE',
    'struct': 'STRUCT',
    'union': 'UNION',
    'const': 'CONST',
    '__out': 'OUT',
    'NORETURN': 'NORETURN',
    '_V_FW': 'V_FW',
    '_V_BW': 'V_BW',
}

def t_NUM(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'[_A-Za-z][_A-Za-z0-9]*'
    t.type = reserved.get(t.value, 'STRING')
    return t

def t_error(t):
    sys.stderr.write(f"Illegal character '{t.value[0]}'\n")
    t.lexer.skip(1)

lexer = lex.lex()

# State variables
tg_abi = 3
thunk_type = 0
ptr_size = 0
align = 0

arg_num = 0
arg_offs = 0
arg_size = 0
al_arg_size = 0
arr_sz = 0
is_ptr = 0
is_arr = 0
is_rptr = 0
is_far = 0
is_rfar = 0
is_ffar = 0
is_cbk = 0
is_void = 0
is_rvoid = 0
is_const = 0
is_out = 0
is_pas = 0
is_init = 0
is_noret = 0
ref_inc = 0
ref_mult = 0
rlen = 0
abuf = ""
atype = ""
atype2 = ""
atype3 = ""
rtbuf = ""

CVTYPE_OTHER, CVTYPE_VOID, CVTYPE_CHAR, CVTYPE_ARR, CVTYPE_CHAR_ARR = range(5)
cvtype = CVTYPE_OTHER


def yyerror(s):
    sys.stderr.write(f"Parse error: {s}\n")
    sys.exit(1)

def beg_arg():
    global is_far, is_ptr, is_arr, is_cbk, is_void, is_const, is_out
    global cvtype, arr_sz, atype, atype2, atype3, arg_size, ref_inc, ref_mult
    is_far = 0
    is_ptr = 0
    is_arr = 0
    is_cbk = 0
    is_void = 0
    is_const = 0
    is_out = 0
    cvtype = CVTYPE_OTHER
    arr_sz = 0
    atype = ""
    atype2 = ""
    atype3 = ""
    arg_size = 0
    ref_inc = 0
    ref_mult = 0

def init_line():
    global is_init, is_pas, is_rvoid, is_rptr, is_rfar, is_ffar, is_noret, rlen
    is_init = 0
    is_pas = 0
    is_rvoid = 0
    is_rptr = 0
    is_rfar = 0
    is_ffar = 0
    is_noret = 0
    rlen = 0
    beg_arg()

def get_pref():
    if is_const:
        return "C"
    if is_out:
        return "O"
    return ""

def do_start_arg(anum):
    global abuf
    if thunk_type == 1 or thunk_type == 2:
        abuf += "_"
    if is_ptr:
        if is_far:
            if anum == 0:
                abuf += "_ARG_PTR_FAR("
            elif anum == 1:
                abuf += "_ARG_PTR_FAR_A("
            elif anum == 2:
                abuf += "_CNV_PTR_FAR, _L_NONE"
        else:
            if anum == 0:
                abuf += "_ARG_PTR("
            elif anum == 1:
                abuf += "_ARG_PTR_A("
            elif anum == 2:
                if cvtype == CVTYPE_VOID:
                    if ref_inc:
                        abuf += f"_CNV_PTR_{get_pref()}VOID, _L_REF({arg_num + 1 + ref_inc}, {ref_mult})"
                    else:
                        abuf += f"_CNV_PTR_{get_pref()}PVOID, _L_NONE"
                elif cvtype == CVTYPE_CHAR:
                    if is_const:
                        abuf += "_CNV_PTR_CCHAR, _L_NONE"
                    else:
                        abuf += "_CNV_PTR_CHAR, _L_UNIMP"
                elif cvtype == CVTYPE_CHAR_ARR:
                    if is_const:
                        if arr_sz == -1:
                            abuf += "_CNV_PTR_CCHAR_ARR, _L_UNIMP"
                        else:
                            abuf += f"_CNV_PTR_CCHAR_ARR, _L_IMM({arg_num + 1}, {arr_sz})"
                    else:
                        abuf += "_CNV_PTR_CHAR_ARR, _L_UNIMP"
                elif cvtype == CVTYPE_ARR:
                    abuf += f"_CNV_PTR_{get_pref()}ARR, _L_IMM({arg_num + 1}, {arr_sz})"
                elif cvtype == CVTYPE_OTHER:
                    abuf += f"_CNV_{get_pref()}PTR, _L_SZ({arg_num + 1})"
    elif is_cbk:
        if anum == 0:
            abuf += "_ARG_CBK("
        elif anum == 1:
            abuf += "_ARG_CBK_A("
        elif anum == 2:
            abuf += "_CNV_CBK, _L_NONE"
    elif is_arr:
        if anum == 0:
            abuf += "_ARG_ARR("
        elif anum == 1:
            abuf += "_ARG_ARR_A("
        elif anum == 2:
            if cvtype == CVTYPE_CHAR_ARR:
                if is_const:
                    if arr_sz == -1:
                        abuf += "_CNV_CCHAR_ARR, _L_UNIMP"
                    else:
                        abuf += f"_CNV_CCHAR_ARR, _L_IMM({arg_num + 1}, {arr_sz})"
                else:
                    abuf += f"_CNV_CHAR_{get_pref()}ARR, _L_IMM({arg_num + 1}, {arr_sz})"
            elif cvtype == CVTYPE_ARR:
                abuf += f"_CNV_{get_pref()}ARR, _L_IMM({arg_num + 1}, {arr_sz})"
            elif cvtype == CVTYPE_OTHER:
                abuf += f"_CNV_{get_pref()}PTR, _L_SZ({arg_num + 1})"
    else:
        if anum == 0:
            abuf += "_ARG("
        elif anum == 1:
            abuf += "_ARG_A("
        elif anum == 2:
            abuf += "_CNV_SIMPLE, _L_NONE"

def fin_arg(last):
    global abuf, arg_offs, arg_num
    if not atype:
        return
    if not is_ptr and is_void:
        return
    do_start_arg(0)
    if thunk_type == 0:
        const_str = "const " if is_const else ""
        arr_str = " *" if is_arr else ""
        abuf += f"{arg_offs}, {const_str}{atype}{arr_str}, _SP)"
    elif thunk_type == 1 or thunk_type == 2:
        if is_const:
            abuf += "const "
        abuf += f"{atype}), "
        if is_arr:
            if arr_sz != -1:
                abuf += f"[{arr_sz}], "
            else:
                abuf += "[], "
        else:
            abuf += ", "
        do_start_arg(1)
        if is_const:
            abuf += "const "
        t2 = atype2 if atype2 else atype
        abuf += f"{t2}), "
        do_start_arg(1)
        if is_const:
            abuf += "const "
        if is_ptr:
            abuf += f"{t2}), "
        else:
            t3 = atype3 if atype3 else t2
            abuf += f"{t3}), "
        do_start_arg(2)

    if is_ptr:
        real_arg_size = ptr_size
        if is_far:
            real_arg_size *= 2
    else:
        if arg_size <= 0:
            if arg_size == 0 and arg_num:
                yyerror("parse error, void argument?")
            if arg_size == -1 and not last:
                yyerror("unknown argument size")
            arg_num += 1
            return
        real_arg_size = al_arg_size
    assert real_arg_size > 0
    arg_offs += real_arg_size
    arg_num += 1

def add_flg(buf, flg, num):
    if not num:
        return flg
    else:
        return buf + " | " + flg

def get_flags():
    buf = ""
    flg = 0
    if is_ffar:
        buf = add_flg(buf, "_TFLG_FAR", flg)
        flg += 1
    if is_noret:
        buf = add_flg(buf, "_TFLG_NORET", flg)
        flg += 1
    if is_init:
        buf = add_flg(buf, "_TFLG_INIT", flg)
        flg += 1
    if not flg:
        buf = add_flg(buf, "_TFLG_NONE", flg)
        flg += 1
    return buf

def AL(x):
    return ((x) + (align - 1)) & ~(align - 1)

def al_s_type():
    return "WORD" if align == 2 else "DWORD"

def al_u_type():
    return "UWORD" if align == 2 else "UDWORD"

def ATYPE3(stype):
    global atype3
    if al_arg_size > arg_size:
        atype3 += al_s_type() if stype == 's' else al_u_type()

# Parser rules

def p_input(p):
    '''input : lines'''

def p_lines(p):
    '''lines : lines line
             | empty'''

def p_line(p):
    '''line : lnum rdecls fname lb args rb attrs SEMIC'''
    global rlen
    num_val = p[1]
    fname_val = p[3]

    if is_rptr:
        rt = "_RET_PTR"
        rv = "_ARG_RPTR"
        rlen = ptr_size
        if is_rfar:
            rlen *= 2
            rt = "_RET_PTR_FAR"
            rv = "_ARG_RPTR_FAR"
    else:
        rt = "_RET"
        rv = "_ARG_R"

    if thunk_type == 0:
        if not is_rvoid:
            if abuf:
                print(f"\tcase {num_val}:\n\t\t_DISPATCH({rlen}, {rv}({rtbuf}), {rt}, {fname_val}, {abuf});\n\t\tbreak;")
            else:
                print(f"\tcase {num_val}:\n\t\t_DISPATCH({rlen}, {rv}({rtbuf}), {rt}, {fname_val});\n\t\tbreak;")
        else:
            if abuf:
                print(f"\tcase {num_val}:\n\t\t_DISPATCH_v({fname_val}, {abuf});\n\t\tbreak;")
            else:
                print(f"\tcase {num_val}:\n\t\t_DISPATCH_v({fname_val});\n\t\tbreak;")
    elif thunk_type == 1:
        is_v = 1 if (is_rvoid and not is_rptr) else 0
        if not is_v and is_noret:
            yyerror("non-void noret?")
        elif is_noret:
            is_v += 1
        pas_str = "_P" if is_pas else ""
        v_str = "_v" if is_v else ""
        nr_str = "_nr" if is_noret else ""
        print(f"THUNK({arg_num}, {is_v}, {is_pas}, {pas_str}{v_str}{nr_str})")
    elif thunk_type == 2:
        pas_str = "_P" if is_pas else ""
        if not is_rvoid or is_rptr:
            if is_rptr:
                arg_type_str = "__ARG_PTR_FAR" if is_rfar else "__ARG_PTR"
                ret_type_str = "__RET_PTR_FAR" if is_rfar else "__RET_PTR"
            else:
                arg_type_str = "__ARG"
                ret_type_str = "__RET"
            sys.stdout.write(f"_THUNK{arg_num}{pas_str}({num_val}, {arg_type_str}({rtbuf}), {ret_type_str}, {fname_val}")
        else:
            nr_str = "_nr" if is_noret else ""
            noret_str = "__NORET " if is_noret else ""
            sys.stdout.write(f"_THUNK{arg_num}{pas_str}_v{nr_str}({num_val}, {noret_str}void, {fname_val}")
        if arg_num:
            sys.stdout.write(f", {abuf}")
        sys.stdout.write(f", {get_flags()})\n")

def p_lb(p):
    '''lb : LB'''
    global arg_offs, arg_num
    arg_offs = 0
    arg_num = 0
    beg_arg()

def p_rb(p):
    '''rb : RB'''
    fin_arg(1)

def p_lnum(p):
    '''lnum : num'''
    init_line()
    p[0] = p[1]

def p_num(p):
    '''num : NUM'''
    p[0] = p[1]

def p_fname(p):
    '''fname : STRING'''
    p[0] = p[1]

def p_sname(p):
    '''sname : STRING'''
    p[0] = p[1]

def p_tname(p):
    '''tname : STRING'''
    p[0] = p[1]

def p_cname(p):
    '''cname : STRING'''
    p[0] = p[1]

def p_rquals(p):
    '''rquals : FAR ASTER
              | ASTER'''
    global is_rfar, is_rptr
    if len(p) == 3:
        is_rfar = 1
        is_rptr = 1
    else:
        is_rptr = 1

def p_quals(p):
    '''quals : FAR quals
             | ASTER quals
             | empty'''
    global is_far, is_ptr
    if len(p) == 3:
        tok = p[1]
        if tok == 'FAR' or tok == 'far':
            is_far = 1
        elif tok == '*':
            is_ptr = 1

def p_arr(p):
    '''arr : LBR num RBR
           | LBR RBR'''
    global cvtype, is_arr, arr_sz
    cvtype = CVTYPE_CHAR_ARR if cvtype == CVTYPE_CHAR else CVTYPE_ARR
    is_arr = 1
    if len(p) == 4:
        arr_sz = p[2]
    else:
        arr_sz = -1

def p_fatr(p):
    '''fatr : ASMCFUNC
            | ASMPASCAL
            | INITTEXT
            | NORETURN
            | FAR
            | SEGM LB STRING RB'''
    global is_pas, is_init, is_noret, is_ffar
    tok = p[1]
    if tok == 'ASMPASCAL':
        is_pas = 1
    elif tok == 'INITTEXT':
        is_init = 1
    elif tok == 'NORETURN':
        is_noret = 1
    elif tok == 'FAR' or tok == 'far':
        is_ffar = 1

def p_fatrs(p):
    '''fatrs : fatr fatrs
             | fatr'''

def p_attr(p):
    '''attr : NORETURN'''
    global is_noret
    is_noret = 1

def p_attrs(p):
    '''attrs : attr attrs
             | empty'''

def p_rq_fa(p):
    '''rq_fa : rquals fatrs
             | rquals
             | fatrs
             | empty'''

def p_rtype(p):
    '''rtype : VOID
             | WORD
             | UWORD
             | DWORD
             | UDWORD
             | QWORD
             | UQWORD
             | FLOAT
             | DOUBLE
             | LDOUBLE
             | BYTE
             | CHAR
             | UBYTE'''
    global rlen, rtbuf, is_rvoid
    tok_type = p.slice[1].type
    if tok_type == 'VOID':
        rlen = 0
        rtbuf = "void"
        is_rvoid = 1
    elif tok_type == 'WORD':
        rlen = 2
        rtbuf = "WORD"
    elif tok_type == 'UWORD':
        rlen = 2
        rtbuf = "UWORD"
    elif tok_type == 'DWORD':
        rlen = 4
        rtbuf = "DWORD"
    elif tok_type == 'UDWORD':
        rlen = 4
        rtbuf = "UDWORD"
    elif tok_type == 'QWORD':
        rlen = 8
        rtbuf = "QWORD"
    elif tok_type == 'UQWORD':
        rlen = 8
        rtbuf = "UQWORD"
    elif tok_type == 'FLOAT':
        rlen = 4
        rtbuf = "float"
    elif tok_type == 'DOUBLE':
        rlen = 8
        rtbuf = "double"
    elif tok_type == 'LDOUBLE':
        rlen = 12
        rtbuf = "long double"
    elif tok_type == 'BYTE':
        rlen = 1
        rtbuf = "BYTE"
    elif tok_type == 'CHAR':
        rlen = 1
        rtbuf = "char"
    elif tok_type == 'UBYTE':
        rlen = 1
        rtbuf = "UBYTE"

def p_vref(p):
    '''vref : V_FW LB NUM RB
            | V_BW LB NUM RB'''
    global ref_inc, ref_mult
    if p[1] == '_V_FW':
        ref_inc = 1
    else:
        ref_inc = -1
    ref_mult = p[3]

def p_atype(p):
    '''atype : VOID vref
             | VOID
             | CHAR
             | WORD
             | UWORD
             | DWORD
             | UDWORD
             | QWORD
             | UQWORD
             | FLOAT
             | DOUBLE
             | LDOUBLE
             | BYTE
             | UBYTE
             | VOID LB ASTER cname RB LB VOID RB
             | STRUCT sname
             | UNION sname
             | tname'''
    global arg_size, cvtype, atype, al_arg_size, is_void, is_cbk
    tok_type = p.slice[1].type
    if tok_type == 'VOID':
        if len(p) == 9: # VOID ( * cname ) ( VOID )
            arg_size = 4
            is_cbk = 1
            atype += "VOID"
            al_arg_size = AL(arg_size)
        elif len(p) == 3: # VOID vref
            arg_size = 0
            cvtype = CVTYPE_VOID
            atype += "VOID"
            al_arg_size = AL(arg_size)
            is_void = 1
        else: # VOID
            arg_size = 0
            cvtype = CVTYPE_VOID
            atype += "VOID"
            al_arg_size = AL(arg_size)
            is_void = 1
    elif tok_type == 'CHAR':
        arg_size = 1
        cvtype = CVTYPE_CHAR
        atype += "char"
        al_arg_size = AL(arg_size)
        ATYPE3('s')
    elif tok_type == 'WORD':
        arg_size = 2
        atype += "WORD"
        al_arg_size = AL(arg_size)
        ATYPE3('s')
    elif tok_type == 'UWORD':
        arg_size = 2
        atype += "UWORD"
        al_arg_size = AL(arg_size)
        ATYPE3('u')
    elif tok_type == 'DWORD':
        arg_size = 4
        atype += "DWORD"
        al_arg_size = AL(arg_size)
    elif tok_type == 'UDWORD':
        arg_size = 4
        atype += "UDWORD"
        al_arg_size = AL(arg_size)
    elif tok_type == 'QWORD':
        arg_size = 8
        atype += "QWORD"
        al_arg_size = AL(arg_size)
    elif tok_type == 'UQWORD':
        arg_size = 8
        atype += "UQWORD"
        al_arg_size = AL(arg_size)
    elif tok_type == 'FLOAT':
        arg_size = 4
        atype += "float"
        al_arg_size = AL(arg_size)
    elif tok_type == 'DOUBLE':
        arg_size = 8
        atype += "double"
        al_arg_size = AL(arg_size)
    elif tok_type == 'LDOUBLE':
        arg_size = 12
        atype += "long double"
        al_arg_size = AL(arg_size)
    elif tok_type == 'BYTE':
        arg_size = 1
        atype += "BYTE"
        al_arg_size = AL(arg_size)
        ATYPE3('s')
    elif tok_type == 'UBYTE':
        arg_size = 1
        atype += "UBYTE"
        al_arg_size = AL(arg_size)
        ATYPE3('u')
    elif tok_type == 'STRUCT':
        arg_size = -1
        atype += f"struct {p[2]}"
    elif tok_type == 'UNION':
        arg_size = -1
        atype += f"union {p[2]}"
    else:
        arg_size = -1
        atype += f"{p[1]}"

def p_rdecls(p):
    '''rdecls : rtype rq_fa'''
    global abuf
    abuf = ""

def p_adecls(p):
    '''adecls : atype quals
              | CONST atype quals
              | OUT atype quals'''
    global is_const, is_out
    if p[1] == 'CONST' or p[1] == 'const':
        is_const = 1
    elif p[1] == 'OUT' or p[1] == '__out':
        is_out = 1

def p_argsep(p):
    '''argsep : COMMA'''
    global abuf
    fin_arg(0)
    abuf += ", "
    beg_arg()

def p_args(p):
    '''args : args argsep arg
            | arg'''

def p_arg(p):
    '''arg : adecls STRING arr
           | adecls STRING
           | adecls'''

def p_empty(p):
    '''empty :'''

def p_error(p):
    if p:
        sys.stderr.write(f"Parse error near '{p.value}'\n")
    else:
        sys.stderr.write("Parse error at EOF\n")
    sys.exit(1)

parser = yacc.yacc(write_tables=False, debug=False)

def main():
    global align, ptr_size, thunk_type
    yydebug = 0

    try:
        opts, args = getopt.getopt(sys.argv[1:], "dp:a:")
    except getopt.GetoptError as err:
        sys.stderr.write(f"unknown option {err}\n")
        sys.exit(1)

    for o, a in opts:
        if o == "-a":
            align = int(a)
        elif o == "-p":
            ptr_size = int(a)
        elif o == "-d":
            yydebug = 1

    if args:
        thunk_type = int(args[0])

    if not align or not ptr_size:
        sys.stderr.write("Set alignment and ptr size\n")
        sys.exit(1)

    if thunk_type == 1:
        sys.stdout.write(
            f"/* generated with thunk-gen v{VERSION} */"
            f"nl()"
            f"sp_num(define TG_ABI {tg_abi})"
            f"sp_num(ifndef __CALL_v)"
            f"sp_num(define __CALL_v __CALL)"
            f"sp_num(endif)"
            f"sp_num(ifndef __CALL_v_nr)"
            f"sp_num(define __CALL_v_nr __CALL)"
            f"sp_num(endif)"
            f"sp_num(ifndef __CALL_P)"
            f"sp_num(define __CALL_P __CALL)"
            f"sp_num(endif)"
            f"sp_num(ifndef __CALL_P_v)"
            f"sp_num(define __CALL_P_v __CALL)"
            f"sp_num(endif)"
            f"sp_num(ifndef __NORET)"
            f"sp_num(define __NORET)"
            f"sp_num(endif)"
            f"\n"
        )

    data = sys.stdin.read()
    if data:
        parser.parse(data, lexer=lexer, debug=yydebug)

if __name__ == '__main__':
    main()
