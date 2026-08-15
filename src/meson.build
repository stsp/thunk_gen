install_data('thunk_gen.py',
  rename: 'thunk_gen',
  install_mode: 'rwxr-xr-x',
  install_dir: get_option('prefix') / get_option('libexecdir') /
    meson.project_name())

exe = find_program('thunk_gen.py', required: false)
if not exe.found()
  exe = find_program(meson.current_source_dir() / 'thunk_gen.py')
endif
