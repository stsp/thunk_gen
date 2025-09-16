project('thunk_gen', 'c', version: '1.7', meson_version: '>= 1.3.0')

subdir('src')
pkg = import('pkgconfig')
if meson.version().version_compare('>=0.56')
UV = ['binary=' + meson.project_build_root() / 'src' /
       meson.project_name(),
      'tgscript=' + meson.project_source_root() / 'scripts/tg_m4',
      'pdscript=' + meson.project_source_root() / 'scripts/parse_decls.sh',
      'mkadscript=' + meson.project_source_root() / 'scripts/mkasmdefs.sh',
      'm4script=' + meson.project_source_root() / 'scripts/thunks.m4',
      'makeinc=' + meson.project_source_root() / 'scripts/thunk_gen.mk'
     ]
else
UV = []
endif
pkg.generate(
  name: meson.project_name(),
  description: 'thunk generator',
  # we need sdkdir as buildroot prefixes it with sysroot path
  variables: [
              'sdkdir=${prefix}',
              'binary=${sdkdir}' / get_option('libexecdir') /
               meson.project_name() / meson.project_name(),
              'tgscript=${sdkdir}' / get_option('libexecdir') /
               meson.project_name() / 'tg_m4',
              'pdscript=${sdkdir}' / get_option('libexecdir') /
               meson.project_name() / 'parse_decls.sh',
              'mkadscript=${sdkdir}' / get_option('libexecdir') /
               meson.project_name() / 'mkasmdefs.sh',
              'm4script=${sdkdir}' / get_option('datadir') /
               meson.project_name() / 'thunks.m4',
              'makeinc=${sdkdir}' / get_option('datadir') /
               meson.project_name() / 'thunk_gen.mk'
             ],
  uninstalled_variables: UV,
  install_dir: get_option('datadir') / 'pkgconfig'
)
install_data(['scripts/thunks.m4', 'scripts/thunk_gen.mk'])
install_data(['scripts/tg_m4', 'scripts/parse_decls.sh',
              'scripts/mkasmdefs.sh'],
  install_dir: get_option('prefix') / get_option('libexecdir') /
    meson.project_name())
