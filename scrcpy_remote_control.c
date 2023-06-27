
#include <assert.h>
#include <SDL2/SDL_keycode.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <math.h>
#include <time.h>
#include "scrcpy_remote_control.h"

#define INJECT_SOCKET_PATH "/tmp/remote_inject.sock"
#define MAXI_SOCKET_CONN (5)
#define BUFFER_SIZE (255)
#define MAX_RETRY_TIMES_ON_FAILURE (3)
#define SDL_SESSION_END (UINT32_MAX)

static int cmdSocketFd;
static struct sockaddr_un socketAddr;

struct RemoteInputCmd
{
    Uint32 eventType;
    Uint32 buttonState;
    Sint32 x;
    Sint32 y;
};

typedef struct RemoteInputCmd RemoteInputCmd;

int main()
{
    int cmd = 0;
    int x = 0, y = 0, endX = 0, endY = 0;
    begin_session();
    int bx = 423, by = 1338;
    int ex = 392, ey = 2121;
    long_press_move_finger(bx, by, ex, ey, 1500, 1000);
    end_session();
    return 0;
}

int press_screen(int x, int y)
{
    RemoteInputCmd cmd = {
        .buttonState = SC_MOUSE_BUTTON_LEFT,
        .eventType = SDL_MOUSEBUTTONDOWN,
        .x = x,
        .y = y};
    // press
    if (write(cmdSocketFd, (void *)(&cmd), sizeof(RemoteInputCmd)) != sizeof(RemoteInputCmd))
    {
        return -1;
    }
    return 0;
}

int release_screen(int x, int y)
{
    RemoteInputCmd cmd = {
        .buttonState = SC_MOUSE_BUTTON_LEFT,
        .eventType = SDL_MOUSEBUTTONUP,
        .x = x,
        .y = y};
    // release
    if (write(cmdSocketFd, (void *)(&cmd), sizeof(RemoteInputCmd)) != sizeof(RemoteInputCmd))
    {
        return -1;
    }
    return 0;
}

int move_finger(int x, int y)
{
    RemoteInputCmd cmd = {
        .buttonState = SC_MOUSE_BUTTON_LEFT,
        .eventType = SDL_MOUSEMOTION,
        .x = x,
        .y = y};
    // move to specific position
    if (write(cmdSocketFd, (void *)(&cmd), sizeof(RemoteInputCmd)) != sizeof(RemoteInputCmd))
    {
        return -1;
    }
    return 0;
}

int long_press_screen(int x, int y, unsigned int pressMilliseconds)
{
    // long press
    if (press_screen(x, y) < 0)
    {
        return -1;
    }
    usleep(pressMilliseconds * 1000);
    return 0;
}

int long_click_screen(int x, int y, unsigned int pressMilliseconds)
{
    // long press
    if (long_press_screen(x, y, pressMilliseconds) < 0)
    {
        return -1;
    }
    // release
    if (release_screen(x, y) < 0)
    {
        return -1;
    }

    return 0;
}

int long_press_move_finger(int beginX, int beginY, int endX, int endY, unsigned int pressMilliseconds, unsigned int durationMilliseconds)
{
    // long press
    if (long_press_screen(beginX, beginY, pressMilliseconds) < 0)
    {
        return -1;
    }

    // smooth movement
    int durationCount = (int)(round((double)(durationMilliseconds) / MIN_TIME_DURATION_MILLISECONDAS)) + 1;
    double dx = (double)(endX - beginX) / durationCount;
    double dy = (double)(endY - beginY) / durationCount;
    for (int i = 0; i < durationCount; i++)
    {
        if (i != 0)
        {
            usleep(MIN_TIME_DURATION_MILLISECONDAS * 1000);
        }

        int interX = (int)(round(beginX + (i + 1) * dx));
        int interY = (int)(round(beginY + (i + 1) * dy));
        // move
        if (move_finger(interX, interY) < 0)
        {
            return -1;
        }
    }

    // release
    if (release_screen(endX, endY) < 0)
    {
        return -1;
    }

    return 0;
}

int begin_session()
{
    cmdSocketFd = socket(AF_UNIX, SOCK_STREAM, 0);
    // Create serever socket failed
    if (cmdSocketFd == -1)
    {
        printf("Create cmd socket failed\n");
        return -1;
    }

    // socket path to long
    if (strlen(INJECT_SOCKET_PATH) > sizeof(socketAddr.sun_path) - 1)
    {
        printf("Server socket path too long: %s\n", INJECT_SOCKET_PATH);
    }

    memset(&socketAddr, 0, sizeof(struct sockaddr_un));
    socketAddr.sun_family = AF_UNIX;
    strncpy(socketAddr.sun_path, INJECT_SOCKET_PATH, sizeof(socketAddr.sun_path) - 1);

    // connect to socket
    int ret = connect(cmdSocketFd, (const struct sockaddr *)&socketAddr,
                      sizeof(struct sockaddr_un));
    if (ret == -1)
    {
        printf("Connect to server socket failed\n");
        return -1;
    }
    printf("Socket connected!\n");
}

int end_session()
{
    printf("Ending session...\n");
    RemoteInputCmd cmd = {
        .buttonState = SDL_SESSION_END,
        .eventType = SDL_SESSION_END,
        .x = 0,
        .y = 0};
    // end session
    if (write(cmdSocketFd, (void *)(&cmd), sizeof(RemoteInputCmd)) != sizeof(RemoteInputCmd))
    {
        return -1;
    }
    usleep(500000);
    close(cmdSocketFd);
    printf("Session ended!\n");
    return 0;
}