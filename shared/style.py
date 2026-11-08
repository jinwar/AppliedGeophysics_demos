import panel as pn
from bokeh.plotting import figure

NAVY = '#12344a'
TEAL = '#008c95'
ORANGE = '#d16b33'

def plot(title, xlabel, ylabel='Amplitude', height=290):
    p = figure(title=title, x_axis_label=xlabel, y_axis_label=ylabel,
               height=height, sizing_mode='stretch_width',
               tools='pan,wheel_zoom,box_zoom,reset,save', active_scroll=None)
    p.background_fill_color = '#f8fafc'
    p.border_fill_color = '#ffffff'
    p.grid.grid_line_alpha = .25
    p.toolbar.logo = None
    return p

def template(title, main, sidebar=None):
    return pn.template.FastListTemplate(
        title=title, site='Applied Geophysics II', site_url='/',
        header_background=NAVY, accent_base_color=TEAL,
        main=main, sidebar=sidebar or [], main_layout=None,
        sidebar_width=310, theme_toggle=False)
