project('thunk_gen', 'c', version: '0.1')

subdir('src')
pkg = import('pkgconfig')
pkg.generate(
  name: meson.project_name(),
  description: 'thunk generator',
  variables: ['binary=${prefix}' / get_option('libexecdir') /
               meson.project_name() / meson.project_name(),
              'tgscript=${prefix}' / get_option('libexecdir') /
               meson.project_name() / 'tg_m4',
              'm4script=${prefix}' / get_option('datadir') /
               meson.project_name() / 'thunks.m4'],
  uninstalled_variables: ['binary=' + meson.project_build_root() / 'src' /
               meson.project_name(),
              'tgscript=' + meson.project_source_root() / 'scripts/tg_m4',
              'm4script=' + meson.project_source_root() / 'scripts/thunks.m4']
)
install_data('scripts/thunks.m4')
install_data('scripts/tg_m4',
  install_dir: get_option('prefix') / get_option('libexecdir') /
    meson.project_name())
