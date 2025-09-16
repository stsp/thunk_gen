flex = find_program('flex', required: true)
bison = find_program('bison', required: true)

lgen = generator(flex,
  output : '@PLAINNAME@.yy.c',
  arguments : ['-o', '@OUTPUT@', '@INPUT@'])
lfiles = lgen.process('thunk_gen.l')

pgen = generator(bison,
  output : ['@BASENAME@.tab.c', '@BASENAME@.tab.h'],
  arguments : ['@INPUT@', '--defines=@OUTPUT1@', '--output=@OUTPUT0@'])
pfiles = pgen.process('thunk_gen.y')

exe = executable('thunk_gen', lfiles, pfiles,
  c_args: ['-Wno-unused-function',
           '-DVERSION="@0@"'.format(meson.project_version())],
  install: true,
  install_dir: get_option('prefix') / get_option('libexecdir') /
    meson.project_name())
