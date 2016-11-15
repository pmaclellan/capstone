#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <stdint.h>
#include <inttypes.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

#define SOCK_PATH "/tmp/controller.sock"

int main(void)
{
    int s, t, len;
    struct sockaddr_un remote;
    char str[100];

    if ((s = socket(AF_UNIX, SOCK_STREAM, 0)) == -1) {
        perror("socket");
        exit(1);
    }

    printf("Trying to connect...\n");

    remote.sun_family = AF_UNIX;
    strcpy(remote.sun_path, SOCK_PATH);
    len = strlen(remote.sun_path) + sizeof(remote.sun_family);
    if (connect(s, (struct sockaddr *)&remote, len) == -1) {
        perror("connect");
        exit(1);
    }

    printf("Connected.\n");

    uint64_t input;
    uint64_t output;
    char *ptr;

    printf("Enter 1 for start and 0 for stop\n");
    while(printf("> "), fgets(str, 100, stdin), !feof(stdin)) {
        input = strtol(str, &ptr, 10);
        if (input == 1)
        {
            input = 0x00000000000003e8;
        }
        else
        {
            input = 0x0000000100000000;
        }

        send(s, &input, sizeof(uint64_t), 0);

        recv(s, &output, sizeof(uint64_t), 0);

        printf("received> 0x%" PRIx64 "\n", output);
    }

    close(s);

    return 0;
}