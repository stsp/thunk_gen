%option noyywrap

%{
/*
 * function prototype parser - lexer
 * Author: Stas Sergeev
 *
 */

#include <stdio.h>

#define YY_DECL int yylex()

#include "thunk_gen.tab.h"

%}

%%

[0-9]+		{
		  yylval.NUM = atoi(yytext);
		  return NUM;
		}
"("		{ return LB; }
")"		{ return RB; }
";"		{ return SEMIC; }
","		{ return COMMA; }
"\n"		{ return NEWLINE; }
"ASMCFUNC"	{ return ASMCFUNC; }
"ASMPASCAL"	{ return ASMPASCAL; }
"ASMFUNC"	{ }
"INITTEXT"	{ return INITTEXT; }
"SEGM"		{ return SEGM; }
"FAR"		{ return FAR; }
"far"		{ return FAR; }
"*"		{ return ASTER; }
"["		{ return LBR; }
"]"		{ return RBR; }
"VOID"		{ return VOID; }
"void"		{ return VOID; }
"WORD"		{ return WORD; }
"COUNT"		{ return WORD; }
"BOOL"		{ return WORD; }
"char"		{ return CHAR; }
"short"		{ return WORD; }
"UCOUNT"	{ return UWORD; }
"UWORD"		{ return UWORD; }
"BYTE"		{ return BYTE; }
"UBYTE"		{ return UBYTE; }
"unsigned char"	{ return UBYTE; }
"unsigned short"	{ return UWORD; }
"int"		{ return DWORD; }
"unsigned"	{ return UDWORD; }
"unsigned int"	{ return UDWORD; }
"long"		{ return DWORD; }
"unsigned long"	{ return UDWORD; }
"long long"	{ return QWORD; }
"unsigned long long"	{ return UQWORD; }
"size_t"	{ return UDWORD; }
"ssize_t"	{ return DWORD; }
"int16_t"	{ return WORD; }
"uint16_t"	{ return UWORD; }
"int32_t"	{ return DWORD; }
"uint32_t"	{ return UDWORD; }
"LONG"		{ return DWORD; }
"LONG32"	{ return DWORD; }
"ULONG"		{ return UDWORD; }
"ULONG32"	{ return UDWORD; }
"DWORD"		{ return DWORD; }
"UDWORD"	{ return UDWORD; }
"float"		{ return FLOAT; }
"double"	{ return DOUBLE; }
"long double"	{ return LDOUBLE; }
"struct"	{ return STRUCT; }
"union"		{ return UNION; }
"const"		{ return CONST; }
"__out"		{ return OUT; }
"NORETURN"	{ return NORETURN; }
"_V_FW"		{ return V_FW; }
"_V_BW"		{ return V_BW; }
"/*".*"*/"	{ /* comments */ }
[\t ]+		{ /* skip spaces */ }
[_A-Za-z][_A-Za-z0-9]*	{
			  yylval.STRING = strdup(yytext);
			  return STRING;
			}

%%
