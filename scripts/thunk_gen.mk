TG = $(shell pkg-config --variable=binary thunk_gen)
TGS = $(shell pkg-config --variable=tgscript thunk_gen)
PDS ?= $(shell pkg-config --variable=pdscript thunk_gen)
MKADS = $(shell pkg-config --variable=mkadscript thunk_gen)
TGM4 = $(shell pkg-config --variable=m4script thunk_gen)

GEN_TMP = thunk_calls.tmp thunk_asms.tmp plt.inc plt_asmc.h plt_asmp.h
_pos = $(if $(findstring $1,$2),$(call _pos,$1,\
       $(wordlist 2,$(words $2),$2),x $3),$3)
pos = $(words $(call _pos,$1,$2))
pars = $(PDS) $(call pos,$@,$(GEN_TMP)) $< >$@ || ($(RM) $@ ; false)
# dj64 generates .tmp files on its own and doesn't set PDHDR
ifneq ($(PDHDR),)
$(filter %.tmp,$(GEN_TMP)): $(PDHDR)
	$(pars)
endif
plt.inc: thunk_calls.tmp
	$(pars)
plt_asmc.h plt_asmp.h: thunk_asms.tmp
	$(pars)

thunk_calls.h: thunk_calls.tmp
	$(TG) $(TFLAGS) <$< >$@

thunk_asms.h: thunk_asms.tmp
	$(TG) $(TFLAGS) 1 <$< | $(TGS) $(TGM4) >$@_ \
		|| ($(RM) $@_ ; false)
	$(TG) $(TFLAGS) 2 <$< >$@__ \
		|| ($(RM) $@__ ; false)
	cat $@_ $@__ >$@
	rm -f $@_ $@__

glob_asmdefs.h: $(GLOB_ASM)
	$(MKADS) $< >$@
