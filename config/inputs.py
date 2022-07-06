import tcod

MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    tcod.event.K_HOME: (-1, -1),
    tcod.event.K_END: (-1, 1),
    tcod.event.K_PAGEUP: (1, -1),
    tcod.event.K_PAGEDOWN: (1, 1),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # Vi keys.
    tcod.event.K_h: (-1, 0),
    tcod.event.K_j: (0, 1),
    tcod.event.K_k: (0, -1),
    tcod.event.K_l: (1, 0),
    tcod.event.K_y: (-1, -1),
    tcod.event.K_u: (1, -1),
    tcod.event.K_b: (-1, 1),
    tcod.event.K_n: (1, 1),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}

CURSOR_Y_KEYS = {
    tcod.event.K_UP: -1,
    tcod.event.K_DOWN: 1,
    tcod.event.K_PAGEUP: -10,
    tcod.event.K_PAGEDOWN: 10,
}

CONFIRM_KEYS = {
    tcod.event.K_RETURN,
    tcod.event.K_KP_ENTER,
}

YESNO_KEYS = {
    tcod.event.K_y,
    tcod.event.K_RETURN,
    tcod.event.K_SPACE,
    tcod.event.K_n,
    tcod.event.K_ESCAPE
}

USERNAME_KEYS = {
    tcod.event.K_a,
    tcod.event.K_b,
    tcod.event.K_c,
    tcod.event.K_d,
    tcod.event.K_e,
    tcod.event.K_f,
    tcod.event.K_g,
    tcod.event.K_h,
    tcod.event.K_i,
    tcod.event.K_j,
    tcod.event.K_k,
    tcod.event.K_l,
    tcod.event.K_m,
    tcod.event.K_n,
    tcod.event.K_o,
    tcod.event.K_p,
    tcod.event.K_q,
    tcod.event.K_r,
    tcod.event.K_s,
    tcod.event.K_t,
    tcod.event.K_u,
    tcod.event.K_v,
    tcod.event.K_w,
    tcod.event.K_x,
    tcod.event.K_y,
    tcod.event.K_z,
}
