#!/usr/bin/env python3
import sys
import argparse
from lark import Lark, Visitor, Token, Tree

VERSION = "1.10"

grammar = r'''
start: (line | COMMENT | WS)+

line: lnum rdecls fname LB [args] RB [attrs] SEMIC

lnum: NUM

rdecls: rtype [rq_fa]

fname: STRING

rq_fa: (rquals | fatr)+

rquals: FAR ASTER -> rqual_far_aster
      | ASTER     -> rqual_aster

fatr: ASMCFUNC          -> fatr_asmcfunc
    | ASMPASCAL         -> fatr_asmpascal
    | INITTEXT          -> fatr_inittext
    | NORETURN          -> fatr_noreturn
    | FAR               -> fatr_far
    | SEGM LB STRING RB -> fatr_segm

attrs: attr+
attr: NORETURN          -> attr_noreturn

rtype: VOID       -> rtype_void
     | WORD       -> rtype_word
     | UWORD      -> rtype_uword
     | DWORD      -> rtype_dword
     | UDWORD     -> rtype_udword
     | QWORD      -> rtype_qword
     | UQWORD     -> rtype_uqword
     | FLOAT      -> rtype_float
     | DOUBLE     -> rtype_double
     | LDOUBLE    -> rtype_ldouble
     | BYTE       -> rtype_byte
     | CHAR       -> rtype_char
     | UBYTE      -> rtype_ubyte

args: arg (COMMA arg)*

arg: adecls [STRING [arr]]

adecls: [CONST] [OUT] atype quals

quals: qual*
qual: FAR   -> qual_far
    | ASTER -> qual_aster

arr: LBR NUM RBR -> arr_num
   | LBR RBR     -> arr_empty

atype: VOID vref                                -> atype_void_vref
     | VOID                                     -> atype_void
     | CHAR                                     -> atype_char
     | WORD                                     -> atype_word
     | UWORD                                    -> atype_uword
     | DWORD                                    -> atype_dword
     | UDWORD                                   -> atype_udword
     | QWORD                                    -> atype_qword
     | UQWORD                                   -> atype_uqword
     | FLOAT                                    -> atype_float
     | DOUBLE                                   -> atype_double
     | LDOUBLE                                  -> atype_ldouble
     | BYTE                                     -> atype_byte
     | UBYTE                                    -> atype_ubyte
     | VOID LB ASTER STRING RB LB VOID RB       -> atype_cbk
     | STRUCT STRING                            -> atype_struct
     | UNION STRING                             -> atype_union
     | STRING                                   -> atype_tname

vref: V_FW LB NUM RB -> v_fw
    | V_BW LB NUM RB -> v_bw

LB: "("
RB: ")"
SEMIC: ";"
COMMA: ","
ASTER: "*"
LBR: "["
RBR: "]"

UQWORD.4: "unsigned long long" | "UQWORD"
LDOUBLE.4: "long double"
UWORD.3: "unsigned short" | "UWORD" | "UCOUNT" | "uint16_t"
UBYTE.3: "unsigned char" | "UBYTE"
UDWORD.3: "unsigned long" | "unsigned int" | "unsigned" | "UDWORD" | "uint32_t" | "ULONG32" | "ULONG" | "size_t"
QWORD.3: "long long" | "QWORD"
DWORD.2: "DWORD" | "int32_t" | "LONG32" | "LONG" | "int" | "long" | "ssize_t"

ASMCFUNC.2: "ASMCFUNC"
ASMPASCAL.2: "ASMPASCAL"
ASMFUNC.2: "ASMFUNC"
INITTEXT.2: "INITTEXT"
SEGM.2: "SEGM"
FAR.2: "FAR" | "far"
VOID.2: "VOID" | "void"
WORD.2: "WORD" | "COUNT" | "BOOL" | "short" | "int16_t"
BYTE.2: "BYTE"
CHAR.2: "char"
FLOAT.2: "float"
DOUBLE.2: "double"
STRUCT.2: "struct"
UNION.2: "union"
CONST.2: "const"
OUT.2: "__out"
NORETURN.2: "NORETURN"
V_FW.2: "_V_FW"
V_BW.2: "_V_BW"

STRING: /[a-zA-Z_][a-zA-Z0-9_]*/
NUM: /[0-9]+/

COMMENT: /\/\*.*?\*\//
%import common.WS
%ignore WS
%ignore COMMENT
%ignore ASMFUNC
'''

# Conversion types for flat pointers
CVTYPE_OTHER = 0
CVTYPE_VOID = 1
CVTYPE_CHAR = 2
CVTYPE_ARR = 3
CVTYPE_CHAR_ARR = 4


def error_exit(msg):
    sys.stderr.write(f"Parse error: {msg}\n")
    sys.exit(1)


class ThunkGenerator:
    def __init__(self, align, ptr_size, thunk_type):
        self.align = align
        self.ptr_size = ptr_size
        self.thunk_type = thunk_type
        self.tg_abi = 3

    def AL(self, x):
        return ((x) + (self.align - 1)) & ~(self.align - 1)

    def al_s_type(self):
        return "WORD" if self.align == 2 else "DWORD"

    def al_u_type(self):
        return "UWORD" if self.align == 2 else "UDWORD"

    def process(self, tree):
        if self.thunk_type == 1:
            sys.stdout.write(
                f"/* generated with thunk-gen v{VERSION} */"
                "nl()"
                f"sp_num(define TG_ABI {self.tg_abi})"
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
                "\n"
            )

        for child in tree.children:
            if isinstance(child, Tree) and child.data == 'line':
                self.process_line(child)

    def process_line(self, line_tree):
        # Reset line state
        self.is_init = 0
        self.is_pas = 0
        self.is_rvoid = 0
        self.is_rptr = 0
        self.is_rfar = 0
        self.is_ffar = 0
        self.is_noret = 0
        self.rlen = 0
        self.rtbuf = ""
        self.abuf = []

        # Reset arg state
        self.beg_arg()

        children = line_tree.children
        # line: lnum rdecls fname LB [args] RB [attrs] SEMIC
        lnum_node = children[0]
        line_num = int(lnum_node.children[0].value)

        rdecls_node = children[1]
        self.process_rdecls(rdecls_node)

        fname_node = children[2]
        func_name = str(fname_node.children[0].value)

        # LB at index 3
        self.arg_offs = 0
        self.arg_num = 0
        self.beg_arg()

        # Check for args, RB, attrs
        idx = 4
        if idx < len(children) and isinstance(children[idx], Tree) and children[idx].data == 'args':
            self.process_args(children[idx])
            idx += 1

        # RB is at idx, then optional attrs
        if idx < len(children) and children[idx].value == ')':
            idx += 1

        self.fin_arg(1)

        if idx < len(children) and isinstance(children[idx], Tree) and children[idx].data == 'attrs':
            self.process_attrs(children[idx])
            idx += 1

        # Now emit output for the line
        self.emit_line(line_num, func_name)

    def beg_arg(self):
        self.is_far = 0
        self.is_ptr = 0
        self.is_arr = 0
        self.is_cbk = 0
        self.is_void = 0
        self.is_const = 0
        self.is_out = 0
        self.cvtype = CVTYPE_OTHER
        self.arr_sz = 0
        self.atype = ""
        self.atype2 = ""
        self.atype3 = ""
        self.arg_size = 0
        self.ref_inc = 0
        self.ref_mult = 0

    def get_pref(self):
        if self.is_const:
            return "C"
        if self.is_out:
            return "O"
        return ""

    def do_start_arg(self, anum):
        if self.thunk_type == 1 or self.thunk_type == 2:
            self.abuf.append("_")

        if self.is_ptr:
            if self.is_far:
                if anum == 0:
                    self.abuf.append("_ARG_PTR_FAR(")
                elif anum == 1:
                    self.abuf.append("_ARG_PTR_FAR_A(")
                elif anum == 2:
                    self.abuf.append("_CNV_PTR_FAR, _L_NONE")
            else:
                if anum == 0:
                    self.abuf.append("_ARG_PTR(")
                elif anum == 1:
                    self.abuf.append("_ARG_PTR_A(")
                elif anum == 2:
                    if self.cvtype == CVTYPE_VOID:
                        if self.ref_inc:
                            self.abuf.append(
                                f"_CNV_PTR_{self.get_pref()}VOID, _L_REF({self.arg_num + 1 + self.ref_inc}, {self.ref_mult})"
                            )
                        else:
                            self.abuf.append(
                                f"_CNV_PTR_{self.get_pref()}PVOID, _L_NONE"
                            )
                    elif self.cvtype == CVTYPE_CHAR:
                        if self.is_const:
                            self.abuf.append("_CNV_PTR_CCHAR, _L_NONE")
                        else:
                            self.abuf.append("_CNV_PTR_CHAR, _L_UNIMP")
                    elif self.cvtype == CVTYPE_CHAR_ARR:
                        if self.is_const:
                            if self.arr_sz == -1:
                                self.abuf.append("_CNV_PTR_CCHAR_ARR, _L_UNIMP")
                            else:
                                self.abuf.append(
                                    f"_CNV_PTR_CCHAR_ARR, _L_IMM({self.arg_num + 1}, {self.arr_sz})"
                                )
                        else:
                            self.abuf.append("_CNV_PTR_CHAR_ARR, _L_UNIMP")
                    elif self.cvtype == CVTYPE_ARR:
                        self.abuf.append(
                            f"_CNV_PTR_{self.get_pref()}ARR, _L_IMM({self.arg_num + 1}, {self.arr_sz})"
                        )
                    elif self.cvtype == CVTYPE_OTHER:
                        self.abuf.append(
                            f"_CNV_{self.get_pref()}PTR, _L_SZ({self.arg_num + 1})"
                        )
        elif self.is_cbk:
            if anum == 0:
                self.abuf.append("_ARG_CBK(")
            elif anum == 1:
                self.abuf.append("_ARG_CBK_A(")
            elif anum == 2:
                self.abuf.append("_CNV_CBK, _L_NONE")
        elif self.is_arr:
            if anum == 0:
                self.abuf.append("_ARG_ARR(")
            elif anum == 1:
                self.abuf.append("_ARG_ARR_A(")
            elif anum == 2:
                if self.cvtype == CVTYPE_CHAR_ARR:
                    if self.is_const:
                        if self.arr_sz == -1:
                            self.abuf.append("_CNV_CCHAR_ARR, _L_UNIMP")
                        else:
                            self.abuf.append(
                                f"_CNV_CCHAR_ARR, _L_IMM({self.arg_num + 1}, {self.arr_sz})"
                            )
                    else:
                        self.abuf.append(
                            f"_CNV_CHAR_{self.get_pref()}ARR, _L_IMM({self.arg_num + 1}, {self.arr_sz})"
                        )
                elif self.cvtype == CVTYPE_ARR:
                    self.abuf.append(
                        f"_CNV_{self.get_pref()}ARR, _L_IMM({self.arg_num + 1}, {self.arr_sz})"
                    )
                elif self.cvtype == CVTYPE_OTHER:
                    self.abuf.append(
                        f"_CNV_{self.get_pref()}PTR, _L_SZ({self.arg_num + 1})"
                    )
        else:
            if anum == 0:
                self.abuf.append("_ARG(")
            elif anum == 1:
                self.abuf.append("_ARG_A(")
            elif anum == 2:
                self.abuf.append("_CNV_SIMPLE, _L_NONE")

    def fin_arg(self, last):
        if not self.atype:
            return
        if not self.is_ptr and self.is_void:
            return

        self.do_start_arg(0)
        if self.thunk_type == 0:
            const_str = "const " if self.is_const else ""
            arr_str = " *" if self.is_arr else ""
            self.abuf.append(f"{self.arg_offs}, {const_str}{self.atype}{arr_str}, _SP)")
        elif self.thunk_type in (1, 2):
            if self.is_const:
                self.abuf.append("const ")
            self.abuf.append(f"{self.atype}), ")
            if self.is_arr:
                if self.arr_sz != -1:
                    self.abuf.append(f"[{self.arr_sz}], ")
                else:
                    self.abuf.append("[], ")
            else:
                self.abuf.append(", ")

            self.do_start_arg(1)
            if self.is_const:
                self.abuf.append("const ")
            a2 = self.atype2 if self.atype2 else self.atype
            self.abuf.append(f"{a2}), ")

            self.do_start_arg(1)
            if self.is_const:
                self.abuf.append("const ")
            if self.is_ptr:
                self.abuf.append(f"{a2}), ")
            else:
                a3 = self.atype3 if self.atype3 else a2
                self.abuf.append(f"{a3}), ")

            self.do_start_arg(2)

        if self.is_ptr:
            real_arg_size = self.ptr_size
            if self.is_far:
                real_arg_size *= 2
        else:
            if self.arg_size <= 0:
                if self.arg_size == 0 and self.arg_num:
                    error_exit("parse error, void argument?")
                if self.arg_size == -1 and not last:
                    error_exit("unknown argument size")
                self.arg_num += 1
                return
            real_arg_size = self.al_arg_size

        assert real_arg_size > 0
        self.arg_offs += real_arg_size
        self.arg_num += 1

    def process_rdecls(self, node):
        # rdecls: rtype [rq_fa]
        rtype_node = node.children[0]
        self.process_rtype(rtype_node)
        if len(node.children) > 1 and node.children[1] is not None:
            self.process_rq_fa(node.children[1])
        self.abuf = []

    def process_rtype(self, node):
        kind = node.data
        if kind == 'rtype_void':
            self.rlen = 0
            self.rtbuf = "void"
            self.is_rvoid = 1
        elif kind == 'rtype_word':
            self.rlen = 2
            self.rtbuf = "WORD"
        elif kind == 'rtype_uword':
            self.rlen = 2
            self.rtbuf = "UWORD"
        elif kind == 'rtype_dword':
            self.rlen = 4
            self.rtbuf = "DWORD"
        elif kind == 'rtype_udword':
            self.rlen = 4
            self.rtbuf = "UDWORD"
        elif kind == 'rtype_qword':
            self.rlen = 8
            self.rtbuf = "QWORD"
        elif kind == 'rtype_uqword':
            self.rlen = 8
            self.rtbuf = "UQWORD"
        elif kind == 'rtype_float':
            self.rlen = 4
            self.rtbuf = "float"
        elif kind == 'rtype_double':
            self.rlen = 8
            self.rtbuf = "double"
        elif kind == 'rtype_ldouble':
            self.rlen = 12
            self.rtbuf = "long double"
        elif kind == 'rtype_byte':
            self.rlen = 1
            self.rtbuf = "BYTE"
        elif kind == 'rtype_char':
            self.rlen = 1
            self.rtbuf = "char"
        elif kind == 'rtype_ubyte':
            self.rlen = 1
            self.rtbuf = "UBYTE"

    def process_rq_fa(self, node):
        for item in node.children:
            if isinstance(item, Tree):
                k = item.data
                if k == 'rqual_far_aster':
                    self.is_rfar = 1
                    self.is_rptr = 1
                elif k == 'rqual_aster':
                    self.is_rptr = 1
                elif k == 'fatr_asmcfunc':
                    pass
                elif k == 'fatr_asmpascal':
                    self.is_pas = 1
                elif k == 'fatr_inittext':
                    self.is_init = 1
                elif k == 'fatr_noreturn':
                    self.is_noret = 1
                elif k == 'fatr_far':
                    self.is_ffar = 1
                elif k == 'fatr_segm':
                    pass

    def process_args(self, node):
        # args: arg (COMMA arg)*
        args_list = [c for c in node.children if isinstance(c, Tree) and c.data == 'arg']
        for i, arg_node in enumerate(args_list):
            if i > 0:
                self.fin_arg(0)
                self.abuf.append(", ")
                self.beg_arg()
            self.process_arg(arg_node)

    def process_arg(self, node):
        # arg: adecls [STRING [arr]]
        children = node.children
        adecls_node = children[0]
        self.process_adecls(adecls_node)

        if len(children) > 1 and children[1] is not None and isinstance(children[1], Token):
            # arg name present
            pass

        if len(children) > 2 and children[2] is not None and isinstance(children[2], Tree):
            arr_node = children[2]
            if arr_node.data == 'arr_num':
                self.cvtype = CVTYPE_CHAR_ARR if self.cvtype == CVTYPE_CHAR else CVTYPE_ARR
                self.is_arr = 1
                self.arr_sz = int(arr_node.children[1].value)
            elif arr_node.data == 'arr_empty':
                self.cvtype = CVTYPE_CHAR_ARR if self.cvtype == CVTYPE_CHAR else CVTYPE_ARR
                self.is_arr = 1
                self.arr_sz = -1

    def process_adecls(self, node):
        # adecls: [CONST] [OUT] atype quals
        for c in node.children:
            if isinstance(c, Token):
                if c.type == 'CONST':
                    self.is_const = 1
                elif c.type == 'OUT':
                    self.is_out = 1
            elif isinstance(c, Tree):
                if c.data.startswith('atype_'):
                    self.process_atype(c)
                elif c.data == 'quals':
                    self.process_quals(c)

    def process_atype(self, node):
        kind = node.data
        if kind == 'atype_void_vref':
            self.arg_size = 0
            self.cvtype = CVTYPE_VOID
            self.atype += "VOID"
            self.al_arg_size = self.AL(self.arg_size)
            self.is_void = 1
            vref_node = node.children[1]
            if vref_node.data == 'v_fw':
                self.ref_inc = 1
                self.ref_mult = int(vref_node.children[2].value)
            elif vref_node.data == 'v_bw':
                self.ref_inc = -1
                self.ref_mult = int(vref_node.children[2].value)
        elif kind == 'atype_void':
            self.arg_size = 0
            self.cvtype = CVTYPE_VOID
            self.atype += "VOID"
            self.al_arg_size = self.AL(self.arg_size)
            self.is_void = 1
        elif kind == 'atype_char':
            self.arg_size = 1
            self.cvtype = CVTYPE_CHAR
            self.atype += "char"
            self.al_arg_size = self.AL(self.arg_size)
            if self.al_arg_size > self.arg_size:
                self.atype3 += self.al_s_type()
        elif kind == 'atype_word':
            self.arg_size = 2
            self.atype += "WORD"
            self.al_arg_size = self.AL(self.arg_size)
            if self.al_arg_size > self.arg_size:
                self.atype3 += self.al_s_type()
        elif kind == 'atype_uword':
            self.arg_size = 2
            self.atype += "UWORD"
            self.al_arg_size = self.AL(self.arg_size)
            if self.al_arg_size > self.arg_size:
                self.atype3 += self.al_u_type()
        elif kind == 'atype_dword':
            self.arg_size = 4
            self.atype += "DWORD"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_udword':
            self.arg_size = 4
            self.atype += "UDWORD"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_qword':
            self.arg_size = 8
            self.atype += "QWORD"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_uqword':
            self.arg_size = 8
            self.atype += "UQWORD"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_float':
            self.arg_size = 4
            self.atype += "float"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_double':
            self.arg_size = 8
            self.atype += "double"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_ldouble':
            self.arg_size = 12
            self.atype += "long double"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_byte':
            self.arg_size = 1
            self.atype += "BYTE"
            self.al_arg_size = self.AL(self.arg_size)
            if self.al_arg_size > self.arg_size:
                self.atype3 += self.al_s_type()
        elif kind == 'atype_ubyte':
            self.arg_size = 1
            self.atype += "UBYTE"
            self.al_arg_size = self.AL(self.arg_size)
            if self.al_arg_size > self.arg_size:
                self.atype3 += self.al_u_type()
        elif kind == 'atype_cbk':
            self.arg_size = 4
            self.is_cbk = 1
            self.atype += "VOID"
            self.al_arg_size = self.AL(self.arg_size)
        elif kind == 'atype_struct':
            self.arg_size = -1
            self.atype += f"struct {node.children[1].value}"
        elif kind == 'atype_union':
            self.arg_size = -1
            self.atype += f"union {node.children[1].value}"
        elif kind == 'atype_tname':
            self.arg_size = -1
            self.atype += str(node.children[0].value)

    def process_quals(self, node):
        for q in node.children:
            if isinstance(q, Tree):
                if q.data == 'qual_far':
                    self.is_far = 1
                elif q.data == 'qual_aster':
                    self.is_ptr = 1

    def process_attrs(self, node):
        for a in node.children:
            if isinstance(a, Tree) and a.data == 'attr_noreturn':
                self.is_noret = 1

    def get_flags(self):
        buf = []
        if self.is_ffar:
            buf.append("_TFLG_FAR")
        if self.is_noret:
            buf.append("_TFLG_NORET")
        if self.is_init:
            buf.append("_TFLG_INIT")
        if not buf:
            return "_TFLG_NONE"
        return " | ".join(buf)

    def emit_line(self, line_num, func_name):
        abuf_str = "".join(self.abuf)

        if self.is_rptr:
            rt = "_RET_PTR"
            rv = "_ARG_RPTR"
            rlen = self.ptr_size
            if self.is_rfar:
                rlen *= 2
                rt = "_RET_PTR_FAR"
                rv = "_ARG_RPTR_FAR"
        else:
            rt = "_RET"
            rv = "_ARG_R"
            rlen = self.rlen

        if self.thunk_type == 0:
            if not self.is_rvoid:
                if abuf_str:
                    sys.stdout.write(
                        f"\tcase {line_num}:\n\t\t_DISPATCH({rlen}, {rv}({self.rtbuf}), {rt}, {func_name}, {abuf_str});\n\t\tbreak;\n"
                    )
                else:
                    sys.stdout.write(
                        f"\tcase {line_num}:\n\t\t_DISPATCH({rlen}, {rv}({self.rtbuf}), {rt}, {func_name});\n\t\tbreak;\n"
                    )
            else:
                if abuf_str:
                    sys.stdout.write(
                        f"\tcase {line_num}:\n\t\t_DISPATCH_v({func_name}, {abuf_str});\n\t\tbreak;\n"
                    )
                else:
                    sys.stdout.write(
                        f"\tcase {line_num}:\n\t\t_DISPATCH_v({func_name});\n\t\tbreak;\n"
                    )

        elif self.thunk_type == 1:
            is_v = 1 if (self.is_rvoid and not self.is_rptr) else 0
            if not is_v and self.is_noret:
                error_exit("non-void noret?")
            elif self.is_noret:
                is_v += 1

            s_pas = "_P" if self.is_pas else ""
            s_v = "_v" if is_v else ""
            s_nr = "_nr" if self.is_noret else ""

            sys.stdout.write(
                f"THUNK({self.arg_num}, {is_v}, {self.is_pas}, {s_pas}{s_v}{s_nr})\n"
            )

        elif self.thunk_type == 2:
            s_pas = "_P" if self.is_pas else ""
            s_nr = "_nr" if self.is_noret else ""

            if not self.is_rvoid or self.is_rptr:
                arg_kind = (
                    "__ARG_PTR_FAR"
                    if (self.is_rptr and self.is_rfar)
                    else ("__ARG_PTR" if self.is_rptr else "__ARG")
                )
                ret_kind = (
                    "__RET_PTR_FAR"
                    if (self.is_rptr and self.is_rfar)
                    else ("__RET_PTR" if self.is_rptr else "__RET")
                )
                sys.stdout.write(
                    f"_THUNK{self.arg_num}{s_pas}({line_num}, {arg_kind}({self.rtbuf}), {ret_kind}, {func_name}"
                )
            else:
                noret_str = "__NORET " if self.is_noret else ""
                sys.stdout.write(
                    f"_THUNK{self.arg_num}{s_pas}_v{s_nr}({line_num}, {noret_str}void, {func_name}"
                )

            if self.arg_num:
                sys.stdout.write(f", {abuf_str}")
            sys.stdout.write(f", {self.get_flags()})\n")


def main():
    parser = argparse.ArgumentParser(description="Function prototype parser and thunk generator")
    parser.add_argument("-a", type=int, help="Alignment (required)")
    parser.add_argument("-p", type=int, help="Pointer size (required)")
    parser.add_argument("-d", action="store_true", help="Debug flag")
    parser.add_argument("thunk_type", type=int, nargs="?", default=0, help="Thunk type (0, 1, or 2)")

    args = parser.parse_args()

    if not args.a or not args.p:
        sys.stderr.write("Set alignment and ptr size\n")
        sys.exit(1)

    input_data = sys.stdin.read()
    lark_parser = Lark(grammar, start='start')
    tree = lark_parser.parse(input_data)

    tg = ThunkGenerator(align=args.a, ptr_size=args.p, thunk_type=args.thunk_type)
    tg.process(tree)


if __name__ == "__main__":
    main()
