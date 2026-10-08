/*
 * espiao_serial.c - grava a conversa serial entre o TR-1000 App e a TR-1000
 *
 * Por que existe (REFERENCIA 2.1b): o App NAO fala MIDI com a maquina - fala
 * por uma porta serial USB (CDC ACM, /dev/tty.usbmodem*). O MIDI Monitor nao
 * enxerga isso. Esta biblioteca entra no processo do App por
 * DYLD_INSERT_LIBRARIES e registra cada byte lido e escrito nessa porta.
 *
 * SO OBSERVA. Nunca muda argumento nem retorno: chama a funcao real e devolve
 * o que ela devolveu. O que vai para a maquina e exatamente o que o App
 * mandaria sem ela.
 *
 * So funciona numa COPIA re-assinada do App (espiao.py preparar): o original
 * tem hardened runtime, e o dyld ignora DYLD_INSERT_LIBRARIES nele.
 *
 * Formato do arquivo (.serlog), little-endian, sem interpretacao aqui - quem
 * interpreta e o tr1000_serial.py:
 *     cabecalho: "TR1KSER1" (8 bytes) + versao u32
 *     registro:  t_ns u64 | tipo u8 | fd u32 | n u32 | n bytes
 *     tipos:     S inicio (caminho do executavel)   O open (caminho)
 *                C close   R read   W write   I ioctl (request u64)
 *                T tcsetattr (struct termios crua)
 *
 * Compilar: clang -dynamiclib -arch arm64 -arch x86_64 -O2 -Wall \
 *               -o espiao/libespiao_serial.dylib espiao/espiao_serial.c
 */
#include <fcntl.h>
#include <mach-o/dyld.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/uio.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#define DYLD_INTERPOSE(_novo, _velho)                                        \
    __attribute__((used)) static struct {                                   \
        const void *novo;                                                   \
        const void *velho;                                                  \
    } _interpose_##_velho __attribute__((section("__DATA,__interpose"))) = \
        {(const void *)(unsigned long)&_novo,                               \
         (const void *)(unsigned long)&_velho};

#define MAX_FD 4096
#define VERSAO 1

static int saida = -1;                         /* o .serlog                 */
static unsigned char vigiado[MAX_FD];          /* fd -> e porta serial?     */
static pthread_mutex_t trava = PTHREAD_MUTEX_INITIALIZER;

/* Dentro desta biblioteca o dyld NAO re-aponta write/open para as versoes
 * daqui (a interposicao vale para as outras imagens), entao escrever no log
 * com write() nao entra em recursao. */
static void gravar(char tipo, int fd, const void *dados, uint32_t n) {
    if (saida < 0) return;
    uint64_t t = clock_gettime_nsec_np(CLOCK_REALTIME);
    uint8_t ti = (uint8_t)tipo;
    uint32_t f = (uint32_t)fd;
    struct iovec v[5] = {
        {&t, 8}, {&ti, 1}, {&f, 4}, {&n, 4}, {(void *)dados, n}};
    pthread_mutex_lock(&trava);
    writev(saida, v, n ? 5 : 4);
    pthread_mutex_unlock(&trava);
}

static int eh_serial(const char *caminho) {
    return caminho && (strstr(caminho, "/dev/tty.") || strstr(caminho, "/dev/cu."));
}

static int vigiando(int fd) {
    return fd >= 0 && fd < MAX_FD && vigiado[fd];
}

__attribute__((constructor)) static void iniciar(void) {
    const char *destino = getenv("ESPIAO_SAIDA");
    if (!destino) return;
    saida = open(destino, O_WRONLY | O_CREAT | O_APPEND | O_CLOEXEC, 0644);
    if (saida < 0) return;
    if (lseek(saida, 0, SEEK_END) == 0) {
        uint32_t versao = VERSAO;
        write(saida, "TR1KSER1", 8);
        write(saida, &versao, 4);
    }
    char exe[1024] = {0};
    uint32_t tam = sizeof(exe);
    if (_NSGetExecutablePath(exe, &tam) != 0) strcpy(exe, "?");
    gravar('S', getpid(), exe, (uint32_t)strlen(exe));
}

static void depois_de_abrir(int fd, const char *caminho) {
    if (fd >= 0 && fd < MAX_FD && eh_serial(caminho)) {
        vigiado[fd] = 1;
        gravar('O', fd, caminho, (uint32_t)strlen(caminho));
    }
}

static int espiao_open(const char *caminho, int flags, ...) {
    mode_t modo = 0;
    if (flags & O_CREAT) {
        va_list ap;
        va_start(ap, flags);
        modo = (mode_t)va_arg(ap, int);
        va_end(ap);
    }
    int fd = open(caminho, flags, modo);
    depois_de_abrir(fd, caminho);
    return fd;
}
DYLD_INTERPOSE(espiao_open, open)

static int espiao_openat(int dir, const char *caminho, int flags, ...) {
    mode_t modo = 0;
    if (flags & O_CREAT) {
        va_list ap;
        va_start(ap, flags);
        modo = (mode_t)va_arg(ap, int);
        va_end(ap);
    }
    int fd = openat(dir, caminho, flags, modo);
    depois_de_abrir(fd, caminho);
    return fd;
}
DYLD_INTERPOSE(espiao_openat, openat)

static int espiao_close(int fd) {
    if (vigiando(fd)) {
        gravar('C', fd, NULL, 0);
        vigiado[fd] = 0;
    }
    return close(fd);
}
DYLD_INTERPOSE(espiao_close, close)

static ssize_t espiao_read(int fd, void *buf, size_t n) {
    ssize_t r = read(fd, buf, n);
    if (r > 0 && vigiando(fd)) gravar('R', fd, buf, (uint32_t)r);
    return r;
}
DYLD_INTERPOSE(espiao_read, read)

static ssize_t espiao_write(int fd, const void *buf, size_t n) {
    ssize_t r = write(fd, buf, n);
    if (r > 0 && vigiando(fd)) gravar('W', fd, buf, (uint32_t)r);
    return r;
}
DYLD_INTERPOSE(espiao_write, write)

/* readv/writev: junta os pedacos ate o total que a chamada REALMENTE moveu */
static void gravar_iov(char tipo, int fd, const struct iovec *iov, int n, ssize_t total) {
    if (total <= 0) return;
    char *junto = malloc((size_t)total);
    if (!junto) return;
    size_t feito = 0;
    for (int i = 0; i < n && feito < (size_t)total; i++) {
        size_t pedaco = iov[i].iov_len;
        if (pedaco > (size_t)total - feito) pedaco = (size_t)total - feito;
        memcpy(junto + feito, iov[i].iov_base, pedaco);
        feito += pedaco;
    }
    gravar(tipo, fd, junto, (uint32_t)feito);
    free(junto);
}

static ssize_t espiao_readv(int fd, const struct iovec *iov, int n) {
    ssize_t r = readv(fd, iov, n);
    if (vigiando(fd)) gravar_iov('R', fd, iov, n, r);
    return r;
}
DYLD_INTERPOSE(espiao_readv, readv)

static ssize_t espiao_writev(int fd, const struct iovec *iov, int n) {
    ssize_t r = writev(fd, iov, n);
    if (vigiando(fd)) gravar_iov('W', fd, iov, n, r);
    return r;
}
DYLD_INTERPOSE(espiao_writev, writev)

static int espiao_ioctl(int fd, unsigned long req, ...) {
    va_list ap;
    va_start(ap, req);
    void *arg = va_arg(ap, void *);
    va_end(ap);
    int r = ioctl(fd, req, arg);
    if (vigiando(fd)) {
        uint64_t q = req;
        gravar('I', fd, &q, 8);
    }
    return r;
}
DYLD_INTERPOSE(espiao_ioctl, ioctl)

static int espiao_tcsetattr(int fd, int acao, const struct termios *t) {
    int r = tcsetattr(fd, acao, t);
    if (vigiando(fd) && t) gravar('T', fd, t, (uint32_t)sizeof(*t));
    return r;
}
DYLD_INTERPOSE(espiao_tcsetattr, tcsetattr)
