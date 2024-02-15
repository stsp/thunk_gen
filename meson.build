project('thunk_gen', 'c', version: '0.1')

subdir('src')
pkg = import('pkgconfig')
pkg.generate(
  name: meson.project_name(),
  description: 'thunk generator',
  variables: ['bindir=${prefix}' / get_option('libexecdir') /
               meson.project_name(),
              'm4script=${prefix}' / get_option('datadir') /
               meson.project_name() / 'thunks.m4']
)
install_data('scripts/thunks.m4')
install_data('scripts/tg_m4',
  install_dir: get_option('prefix') / get_option('libexecdir') /
    meson.project_name())
