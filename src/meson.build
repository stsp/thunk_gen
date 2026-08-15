python = import('python').find_installation()

exe = find_program('thunk_gen.py')

if not meson.is_subproject()
  install_data('thunk_gen.py',
    rename: 'thunk_gen',
    install_mode: 'rwxr-xr-x',
    install_dir: get_option('prefix') / get_option('libexecdir') /
      meson.project_name())
endif
