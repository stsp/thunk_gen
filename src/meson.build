py = import('python').find_installation('python3')

install_data(['thunk_gen.py', 'thunk_gen_lexer.py', 'thunk_gen_parser.py'],
  install_mode: 'rwxr-xr-x',
  install_dir: get_option('prefix') / get_option('libexecdir') /
    meson.project_name())
