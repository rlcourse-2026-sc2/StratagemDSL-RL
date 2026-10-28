/* Resolve fstat64 against the pre-2.33 glibc ABI so libstorm.so loads on
   glibc 2.17+ (Ubuntu 18.04/20.04, CentOS 7). */
struct stat64;
extern int __fxstat64(int ver, int fd, struct stat64 *buf);
__asm__(".symver __fxstat64,__fxstat64@GLIBC_2.2.5");
__attribute__((visibility("hidden"))) int fstat64(int fd, struct stat64 *buf)
{
    return __fxstat64(1 /* _STAT_VER_LINUX */, fd, buf);
}

/* glibc 2.38 headers redirect strtoul to __isoc23_strtoul; send it back to
   the classic symbol (identical behaviour for the decimal input used here). */
extern unsigned long __classic_strtoul(const char *, char **, int);
__asm__(".symver __classic_strtoul,strtoul@GLIBC_2.2.5");
__attribute__((visibility("hidden"))) unsigned long __isoc23_strtoul(const char *s, char **end, int base)
{
    return __classic_strtoul(s, end, base);
}
