"""Small artificial fixtures, deliberately different factors and four pulses."""


def toy_settings():
    return {'wall_seconds':30,'rss_bytes':512*1024**2,'address_space_bytes':2*1024**3,
            'output_bytes':20*1024**2,'terms':200000,'trace_events':200000,'solver_timeout_ms':3000}


def toy_matrices():
    return [[[1,0,0,0],[0,1,0,0],[0,0,0,0],[0,0,0,0]],
            [[0,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,0]]]


def rectangle_fixture():
    return {'purpose':'ARTIFICIAL_ONLY','matrices':toy_matrices(),'particles':2,'order':4,
            'primitives':{'J':[0,'X'],'Q':[0,'P']},'word':['J','Q','J','Q'],
            'boxes':[(1,1),(-1,-1),(-1,-1),(1,1)],'artificial_target_factor':0}
