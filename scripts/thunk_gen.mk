TG ?= $(shell pkg-config --variable=binary thunk_gen)
TGS ?= $(shell pkg-config --variable=tgscript thunk_gen)
PDS ?= $(shell pkg-config --variable=pdscript thunk_gen)
MKADS ?= $(shell pkg-config --variable=mkadscript thunk_gen)
TGM4 ?= $(shell pkg-config --variable=m4script thunk_gen)
TGM4_32 ?= $(shell pkg-config --variable=m4_32script thunk_gen)

GEN_TMP = thunk_c.h thunk_p.h plt.inc plt_asmc.h plt_asmp.h thunk_c1.h \
  thunk_p1.h
_pos = $(if $(findstring $1,$2),$(call _pos,$1,\
       $(wordlist 2,$(words $2),$2),x $3),$3)
pos = $(words $(call _pos,$1,$2))
pars = $(PDS) $(call pos,$@,$(GEN_TMP)) $< >$@ || ($(RM) $@ ; false)
# dj64 generates some .h files on its own and doesn't set PDHDR
ifneq ($(PDHDR),)
$(filter thunk_c.h thunk_p.h,$(GEN_TMP)): $(PDHDR)
	$(pars)

thunk_calls.tmp: thunk_c.h
	nl -v0 <$< | sed -E 's/^ *//' >$@
thunk_asms.tmp: thunk_p.h
	nl -v0 <$< | sed -E 's/^ *//' >$@
endif
plt.inc: thunk_calls.tmp
	$(pars)
plt_asmc.h plt_asmp.h: thunk_asms.tmp
	$(pars)
thunk_p1.h: thunk_p.h
	$(pars)
thunk_c1.h: thunk_c.h
	$(pars)

thunk_calls.h: thunk_calls.tmp
	($(TG) $(TFLAGS) <$< >$@) || ($(RM) $@ ; false)

OLDSHELL := $(SHELL)
SHELL := /usr/bin/env bash -o pipefail
thunk_asms.h: thunk_asms.tmp $(TGM4)
	($(TG) $(TFLAGS) 1 <$< | $(TGS) $(TGM4) >$@_) \
		|| ($(RM) $@_ ; false)
	($(TG) $(TFLAGS) 2 <$< >$@__) \
		|| ($(RM) $@__ ; false)
	cat $@_ $@__ >$@
	rm -f $@_ $@__
thunk_p32.h: thunk_asms.tmp $(TGM4_32)
	($(TG) $(TFLAGS) 1 <$< | $(TGS) $(TGM4_32) >$@_) \
		|| ($(RM) $@_ ; false)
	($(TG) $(TFLAGS) 2 <$< >$@__) \
		|| ($(RM) $@__ ; false)
	cat $@_ $@__ >$@
	rm -f $@_ $@__
thunk_c32.h: thunk_calls.tmp $(TGM4_32)
	($(TG) $(TFLAGS) 1 <$< | $(TGS) $(TGM4_32) >$@_) \
		|| ($(RM) $@_ ; false)
	($(TG) $(TFLAGS) 2 <$< >$@__) \
		|| ($(RM) $@__ ; false)
	cat $@_ $@__ >$@
	rm -f $@_ $@__
# restore caller's shell
SHELL := $(OLDSHELL)

ifneq ($(GLOB_ASM),)
glob_asmdefs.h: $(GLOB_ASM)
	$(MKADS) $< >$@
endif
