"""Linux network denial, process/resource limits. Filesystem access is not confined; reviewed fixtures only."""
import ctypes, errno, os, resource

def confine():
    resource.setrlimit(resource.RLIMIT_CPU,(90,90))
    resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    libc=ctypes.CDLL(None,use_errno=True)
    if libc.prctl(38,1,0,0,0): raise OSError('no_new_privs failed')
    sc=ctypes.CDLL('libseccomp.so.2')
    sc.seccomp_init.argtypes=[ctypes.c_uint32];sc.seccomp_init.restype=ctypes.c_void_p
    sc.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]
    sc.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
    sc.seccomp_load.argtypes=[ctypes.c_void_p]
    ctx=sc.seccomp_init(0x7fff0000)
    for name in ['socket','connect','ptrace','mount','setns','unshare']:
        nr=sc.seccomp_syscall_resolve_name(name.encode())
        if nr>=0 and sc.seccomp_rule_add(ctx,0x50000|errno.EPERM,nr,0): raise OSError('seccomp rule')
    if sc.seccomp_load(ctx): raise OSError('seccomp load')
