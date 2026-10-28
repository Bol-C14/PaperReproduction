import pathlib,subprocess,sys,sysconfig,json
root=pathlib.Path('/home/shugu/work/paper-reproduction-april-20261028');tools=root/'tools/abc-rl'
build=tools/'binding-build';(build/'include').mkdir(parents=True,exist_ok=True)

if not (build/'include/abc_src').exists(): (build/'include/abc_src').symlink_to(tools/'abc/src',target_is_directory=True)
includes=subprocess.check_output([sys.executable,'-m','pybind11','--includes'],text=True).split()
sources=[str(p) for part in ['api','interface','util','global','util/thirdparty'] for p in (tools/'abc_py/src'/part).glob('*.cpp')]
output=pathlib.Path(sysconfig.get_paths()['purelib'])/('abc_py'+sysconfig.get_config_var('EXT_SUFFIX'))
cmd=['g++','-O2','-shared','-std=c++14','-fPIC','-fopenmp','-DLIN64','-DSIZEOF_VOID_P=8','-DSIZEOF_LONG=8','-DSIZEOF_INT=4',*includes,'-I'+str(tools/'Python-3.12.12/Include'),'-I'+str(build/'include'),'-I'+str(tools/'abc/src'),'-I'+str(tools/'abc_py/src'),*sources,str(tools/'abc/libabc.a'),'-lz','-l:libbz2.so.1','-ldl','-lpthread','-o',str(output)]
(root/'results/abc-rl/binding-build-command.json').write_text(json.dumps(cmd,indent=2))
print('Build binding',flush=True);subprocess.run(cmd,check=True,timeout=300)
print('BINDING_BUILD_OK',output,flush=True)
