#ifndef REMOTE_CONTROL_H
#define REMOTE_CONTROL_H

#define SC_MOUSE_BUTTON_LEFT (1)
#define SDL_MOUSEBUTTONDOWN (1025)
#define SDL_MOUSEBUTTONUP (1026)
#define SDL_MOUSEMOTION (1024)
#define LONG_PRESS_TIME (2500000)
#define MIN_TIME_DURATION_MILLISECONDAS (10)


int press_screen(int x, int y);
int long_press_screen(int x, int y, unsigned int pressMilliseconds);

int release_screen(int x, int y);

int long_click_screen(int x, int y, unsigned int pressMilliseconds);

int move_finger(int x, int y);

int long_press_move_finger(int beginX, int beginY, int endX, int endY, unsigned int pressMilliseconds, unsigned int durationMilliseconds);

int begin_session();
int end_session();

#endif