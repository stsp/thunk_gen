import sys
import ply.yacc as yacc

from thunk_gen_lexer import tokens, lexer

VERSION = "1.10"

# State variables
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
abuf = ''
atype = ''
atype2 = ''
atype3 = ''
rtbuf = ''

CVTYPE_OTHER = 0
CVTYPE_VOID = 1
CVTYPE_CHAR = 2
CVTYPE_ARR = 3
CVTYPE_CHAR_ARR = 4
cvtype = CVTYPE_OTHER


def beg_arg():
    global is_far, is_ptr, is_arr, is_cbk, is_void
    global is_const, is_out, cvtype, arr_sz
    global atype, atype2, atype3, arg_size, ref_inc, ref_mult
    is_far = 0
    is_ptr = 0
    is_arr = 0
    is_cbk = 0
    is_void = 0
    is_const = 0
    is_out = 0
    cvtype = CVTYPE_OTHER
    arr_sz = 0
    atype = ''
    atype2 = ''
    atype3 = ''
    arg_size = 0
    ref_inc = 0
    ref_mult = 0


def init_line():
    global is_init, is_pas, is_rvoid, is_rptr, is_rfar, is_ffar
    global is_noret, rlen
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
                        abuf += "_CNV_PTR_%sVOID, _L_REF(%i, %i)" % (get_pref(), arg_num + 1 + ref_inc, ref_mult)
                    else:
                        abuf += "_CNV_PTR_%sPVOID, _L_NONE" % get_pref()
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
                            abuf += "_CNV_PTR_CCHAR_ARR, _L_IMM(%i, %i)" % (arg_num + 1, arr_sz)
                    else:
                        abuf += "_CNV_PTR_CHAR_ARR, _L_UNIMP"
                elif cvtype == CVTYPE_ARR:
                    abuf += "_CNV_PTR_%sARR, _L_IMM(%i, %i)" % (get_pref(), arg_num + 1, arr_sz)
                elif cvtype == CVTYPE_OTHER:
                    abuf += "_CNV_%sPTR, _L_SZ(%i)" % (get_pref(), arg_num + 1)
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
                        abuf += "_CNV_CCHAR_ARR, _L_IMM(%i, %i)" % (arg_num + 1, arr_sz)
                else:
                    abuf += "_CNV_CHAR_%sARR, _L_IMM(%i, %i)" % (get_pref(), arg_num + 1, arr_sz)
            elif cvtype == CVTYPE_ARR:
                abuf += "_CNV_%sARR, _L_IMM(%i, %i)" % (get_pref(), arg_num + 1, arr_sz)
            elif cvtype == CVTYPE_OTHER:
                abuf += "_CNV_%sPTR, _L_SZ(%i)" % (get_pref(), arg_num + 1)
    else:
        if anum == 0:
            abuf += "_ARG("
        elif anum == 1:
            abuf += "_ARG_A("
        elif anum == 2:
            abuf += "_CNV_SIMPLE, _L_NONE"


def fin_arg(last):
    global real_arg_size, arg_offs, arg_num, abuf
    if not atype:
        return
    if not is_ptr and is_void:
        return
    do_start_arg(0)
    if thunk_type == 0:
        abuf += "%i, %s%s%s, _SP)" % (arg_offs, "const " if is_const else "", atype, " *" if is_arr else "")
    elif thunk_type == 1 or thunk_type == 2:
        if is_const:
            abuf += "const "
        abuf += "%s)" % atype
        abuf += ", "
        if is_arr:
            if arr_sz != -1:
                abuf += "[%i], " % arr_sz
            else:
                abuf += "[], "
        else:
            abuf += ", "
        do_start_arg(1)
        if is_const:
            abuf += "const "
        abuf += "%s)" % (atype2 if atype2 else atype)
        abuf += ", "
        do_start_arg(1)
        if is_const:
            abuf += "const "
        if is_ptr:
            abuf += "%s)" % atype2 if atype2 else atype
        else:
            abuf += "%s)" % (atype3 if atype3 else (atype2 if atype2 else atype))
        abuf += ", "
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
        buf = flg
    else:
        buf += " | " + flg
    return buf, num + 1


def get_flags():
    buf = ''
    flg = 0
    if is_ffar:
        buf, flg = add_flg(buf, "_TFLG_FAR", flg)
    if is_noret:
        buf, flg = add_flg(buf, "_TFLG_NORET", flg)
    if is_init:
        buf, flg = add_flg(buf, "_TFLG_INIT", flg)
    if not flg:
        buf, flg = add_flg(buf, "_TFLG_NONE", flg)
    return buf


def AL(x):
    return ((x) + (align - 1)) & ~(align - 1)


def al_s_type():
    return "WORD" if align == 2 else "DWORD"


def al_u_type():
    return "UWORD" if align == 2 else "UDWORD"


def ATYPE3(s):
    global atype3
    if al_arg_size > arg_size:
        atype3 += al_s_type() if s == 's' else al_u_type()


def yyerror(s):
    print("Parse error: %s" % s, file=sys.stderr)
    sys.exit(1)


# Parser rules

def p_input(p):
    '''input : input line NEWLINE
             |'''
    pass


def p_line(p):
    '''line : lnum rdecls fname lb args rb attrs SEMIC'''
    global abuf, arg_num, is_noret, is_pas, is_rptr, is_rfar
    global is_rvoid, is_void, is_ffar, rlen, rtbuf, thunk_type
    rt = ''
    rv = ''
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
                print("\tcase %i:\n\t\t_DISPATCH(%i, %s(%s), %s, %s, %s);\n\t\tbreak;\n" %
                      (p[1], rlen, rv, rtbuf, rt, p[3], abuf))
            else:
                print("\tcase %i:\n\t\t_DISPATCH(%i, %s(%s), %s, %s);\n\t\tbreak;\n" %
                      (p[1], rlen, rv, rtbuf, rt, p[3]))
        else:
            if abuf:
                print("\tcase %i:\n\t\t_DISPATCH_v(%s, %s);\n\t\tbreak;\n" % (p[1], p[3], abuf))
            else:
                print("\tcase %i:\n\t\t_DISPATCH_v(%s);\n\t\tbreak;\n" % (p[1], p[3]))
    elif thunk_type == 1:
        is_v = is_rvoid and not is_rptr
        if not is_v and is_noret:
            yyerror("non-void noret?")
        elif is_noret:
            is_v += 1
        print("THUNK(%i, %i, %i, %s%s%s)\n" %
              (arg_num, is_v, is_pas,
               "_P" if is_pas else "",
               "_v" if is_v else "",
               "_nr" if is_noret else ""))
    elif thunk_type == 2:
        if not is_rvoid or is_rptr:
            print("_THUNK%i%s(%i, %s(%s), %s, %s" %
                  (arg_num,
                   "_P" if is_pas else "",
                   p[1],
                   "__ARG_PTR_FAR" if is_rptr and is_rfar else ("__ARG_PTR" if is_rptr else "__ARG"),
                   rtbuf,
                   "__RET_PTR_FAR" if is_rptr and is_rfar else ("__RET_PTR" if is_rptr else "__RET"),
                   p[3]))
        else:
            print("_THUNK%i%s_v%s(%i, %svoid, %s" %
                  (arg_num,
                   "_P" if is_pas else "",
                   "_nr" if is_noret else "",
                   p[1],
                   "__NORET " if is_noret else "",
                   p[3]))
        if arg_num:
            print(", %s" % abuf)
        print(", %s)\n" % get_flags())


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


def p_quals(p):
    '''quals : FAR quals
             | ASTER quals
             |'''
    global is_far, is_ptr
    if len(p) == 3:
        if p.slice[1].type == 'FAR':
            is_far = 1
        elif p.slice[1].type == 'ASTER':
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
    if p.slice[1].type == 'ASMPASCAL':
        is_pas = 1
    elif p.slice[1].type == 'INITTEXT':
        is_init = 1
    elif p.slice[1].type == 'NORETURN':
        is_noret = 1
    elif p.slice[1].type == 'FAR':
        is_ffar = 1


def p_fatrs(p):
    '''fatrs : fatr fatrs
             | fatr'''
    pass


def p_attr(p):
    '''attr : NORETURN'''
    global is_noret
    is_noret = 1


def p_attrs(p):
    '''attrs : attr attrs
             |'''
    pass


def p_rq_fa(p):
    '''rq_fa : rquals fatrs
             | rquals
             | fatrs
             |'''
    pass


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
    if p.slice[1].type == 'VOID':
        rlen = 0
        rtbuf = 'void'
        is_rvoid = 1
    elif p.slice[1].type == 'WORD':
        rlen = 2
        rtbuf = 'WORD'
    elif p.slice[1].type == 'UWORD':
        rlen = 2
        rtbuf = 'UWORD'
    elif p.slice[1].type == 'DWORD':
        rlen = 4
        rtbuf = 'DWORD'
    elif p.slice[1].type == 'UDWORD':
        rlen = 4
        rtbuf = 'UDWORD'
    elif p.slice[1].type == 'QWORD':
        rlen = 8
        rtbuf = 'QWORD'
    elif p.slice[1].type == 'UQWORD':
        rlen = 8
        rtbuf = 'UQWORD'
    elif p.slice[1].type == 'FLOAT':
        rlen = 4
        rtbuf = 'float'
    elif p.slice[1].type == 'DOUBLE':
        rlen = 8
        rtbuf = 'double'
    elif p.slice[1].type == 'LDOUBLE':
        rlen = 12
        rtbuf = 'long double'
    elif p.slice[1].type == 'BYTE':
        rlen = 1
        rtbuf = 'BYTE'
    elif p.slice[1].type == 'CHAR':
        rlen = 1
        rtbuf = 'char'
    elif p.slice[1].type == 'UBYTE':
        rlen = 1
        rtbuf = 'UBYTE'


def p_vref(p):
    '''vref : V_FW LB NUM RB
            | V_BW LB NUM RB'''
    global ref_inc, ref_mult
    ref_inc = 1 if p.slice[1].type == 'V_FW' else -1
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
    if p.slice[1].type == 'VOID' and len(p) == 2:
        arg_size = 0
        cvtype = CVTYPE_VOID
        atype += 'VOID'
        al_arg_size = AL(arg_size)
        is_void = 1
    elif p.slice[1].type == 'CHAR':
        arg_size = 1
        cvtype = CVTYPE_CHAR
        atype += 'char'
        al_arg_size = AL(arg_size)
        ATYPE3('s')
    elif p.slice[1].type == 'WORD':
        arg_size = 2
        atype += 'WORD'
        al_arg_size = AL(arg_size)
        ATYPE3('s')
    elif p.slice[1].type == 'UWORD':
        arg_size = 2
        atype += 'UWORD'
        al_arg_size = AL(arg_size)
        ATYPE3('u')
    elif p.slice[1].type == 'DWORD':
        arg_size = 4
        atype += 'DWORD'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'UDWORD':
        arg_size = 4
        atype += 'UDWORD'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'QWORD':
        arg_size = 8
        atype += 'QWORD'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'UQWORD':
        arg_size = 8
        atype += 'UQWORD'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'FLOAT':
        arg_size = 4
        atype += 'float'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'DOUBLE':
        arg_size = 8
        atype += 'double'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'LDOUBLE':
        arg_size = 12
        atype += 'long double'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'BYTE':
        arg_size = 1
        atype += 'BYTE'
        al_arg_size = AL(arg_size)
        ATYPE3('s')
    elif p.slice[1].type == 'UBYTE':
        arg_size = 1
        atype += 'UBYTE'
        al_arg_size = AL(arg_size)
        ATYPE3('u')
    elif p.slice[1].type == 'VOID' and len(p) == 9:
        arg_size = 4
        is_cbk = 1
        atype += 'VOID'
        al_arg_size = AL(arg_size)
    elif p.slice[1].type == 'STRUCT':
        arg_size = -1
        atype += 'struct %s' % p[2]
    elif p.slice[1].type == 'UNION':
        arg_size = -1
        atype += 'union %s' % p[2]
    elif len(p) == 2:
        arg_size = -1
        atype += '%s' % p[1]


def p_rdecls(p):
    '''rdecls : rtype rq_fa'''
    global abuf
    abuf = ''


def p_adecls(p):
    '''adecls : atype quals
              | CONST atype quals
              | OUT atype quals'''
    global is_const, is_out
    if len(p) == 4:
        if p.slice[1].type == 'CONST':
            is_const = 1
        elif p.slice[1].type == 'OUT':
            is_out = 1


def p_argsep(p):
    '''argsep : COMMA'''
    fin_arg(0)
    global abuf
    abuf += ", "
    beg_arg()


def p_args(p):
    '''args : args argsep arg
            | arg'''
    pass


def p_arg(p):
    '''arg : adecls STRING arr
           | adecls STRING
           | adecls'''
    pass


def p_error(p):
    if p:
        yyerror("syntax error at '%s'" % p.value)
    else:
        yyerror("syntax error at EOF")


parser = yacc.yacc()


def main():
    global thunk_type, align, ptr_size
    optstr = "dp:a:"
    c = None
    argv = sys.argv[1:]
    argc = len(argv)
    optind = 0
    yydebug = 0

    while optind < argc:
        if argv[optind] == '-d':
            yydebug = 1
            optind += 1
        elif argv[optind] == '-p' and optind + 1 < argc:
            ptr_size = int(argv[optind + 1])
            optind += 2
        elif argv[optind] == '-a' and optind + 1 < argc:
            align = int(argv[optind + 1])
            optind += 2
        elif argv[optind].startswith('-'):
            print("unknown option %s" % argv[optind], file=sys.stderr)
            sys.exit(1)
        else:
            break

    if optind < argc:
        thunk_type = int(argv[optind])
        optind += 1

    if not align or not ptr_size:
        print("Set alignment and ptr size", file=sys.stderr)
        sys.exit(1)

    if thunk_type == 1:
        print("/* generated with thunk-gen v%s */" "nl()"
              "sp_num(define TG_ABI %i)"
              "sp_num(ifndef __CALL_v)"
              "sp_num(define __CALL_v __CALL)"
              "sp_num(endif)"
              "sp_num(ifndef __CALL_v_nr)"
              "sp_num(define __CALL_v_nr __CALL)"
              "sp_num(endif)"
              "sp_num(ifndef __CALL_P)"
              "sp_num(define __CALL_P __CALL)"
              "sp_num(endif)"
              "sp_num(ifndef __CALL_P_v)"
              "sp_num(define __CALL_P_v __CALL)"
              "sp_num(endif)"
              "sp_num(ifndef __NORET)"
              "sp_num(define __NORET)"
              "sp_num(endif)"
              "\n" % (VERSION, 3))

    parser.parse(sys.stdin.read(), lexer=lexer, debug=yydebug)


if __name__ == '__main__':
    main()
