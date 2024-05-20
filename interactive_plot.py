from dash import Dash, dcc, html, Input, Output, callback
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import dash_mantine_components as dmc
import flask
import dash


def get_palette(string=False):
    palette = {
        'p1': (111, 99, 171),  # pursuit
        'p2': (123, 195, 183),  # pursuit 2
        'bg': (200, 180, 100),  # background
        'g': (195, 123, 183),  # global rate
        'sv': (87, 159, 111),
        'opp': (204, 85, 0),
        'app': (100, 50, 50),
        # 'tc': (136, 34, 85),
        'tc': (165, 78, 134),
    }
    for key, vals in palette.items():
        if string:
            palette[key] = f'rgb{vals}'
        else:
            palette[key] = tuple([v / 255 for v in vals])
    return palette


def calc_values(outside_reward, outside_time, inside_reward, inside_time):
    accept_rate = (inside_reward + outside_reward) / (inside_time + outside_time + .00001)
    oc_accept = accept_rate * inside_time
    forgo_rate = outside_reward / (outside_time + .000001)
    oc_forgo = forgo_rate * inside_time
    total_reward = (inside_reward + outside_reward) + .000001
    total_time = inside_time + outside_time
    subjective_value = total_reward * (inside_reward / total_reward - inside_time / total_time)
    policy_cost = oc_accept - oc_forgo
    return subjective_value, oc_accept, oc_forgo, policy_cost


def make_fig(starting_values, limits, selections, selection_values=None, transition_duration=100):
    line_width = 4
    [outside_reward, outside_time, inside_reward, inside_time] = starting_values
    subjective_value, oc_accept, oc_forgo, policy_cost = calc_values(*starting_values)
    palette = get_palette(string=True)
    if selection_values is None:
        selection_values = []
    new_fig = go.Figure()

    # new_fig.add_hline(y=0, line_width=.8, line_color='black')
    # new_fig.add_vline(x=0, line_width=.8, line_color='black')
    new_fig.add_trace(
        go.Scatter(x=[0, 0], y=[-100, 100], line_color='rgb(0,0,0)', mode='lines', showlegend=False,
                   line=dict(width=1)))
    new_fig.add_trace(
        go.Scatter(x=[-100, 100], y=[0, 0], line_color='rgb(0,0,0)', mode='lines', showlegend=False,
                   line=dict(width=1)))

    # inside line
    new_fig.add_trace(
        go.Scatter(x=[0, inside_time], y=[0, inside_reward], line_color=palette['p1'], name='Inside', mode='lines',
                   line_width=line_width))

    # outside line
    new_fig.add_trace(
        go.Scatter(x=[-outside_time, 0], y=[-outside_reward, 0], line_color=palette['bg'], name='Outside',
                   mode='lines', line_width=line_width))

    # global reward rate line
    new_fig.add_trace(
        go.Scatter(x=[-outside_time, inside_time], y=[-outside_reward, inside_reward], line_color=palette['g'],
                   name='Global Reward Rate    ', mode='lines', line_width=line_width))

    sv = selections[0] in selection_values
    tc = selections[1] in selection_values
    opp = selections[2] in selection_values
    app = selections[3] in selection_values

    sv_mid = go.Scatter(x=[0, 0], y=[0, subjective_value],
                        line_color=palette['sv'], mode='lines', name="Subjective Value", line_width=line_width,
                        line=dict(dash='solid'))
    sv_side = go.Scatter(x=[inside_time, inside_time], y=[inside_reward, inside_reward - subjective_value],
                         line_color=palette['sv'], mode='lines', showlegend=False, line_width=line_width,
                         line=dict(dash='solid'))
    opp_diag = go.Scatter(x=[0, inside_time], y=[0, oc_forgo],
                          line_color=palette['bg'], mode='lines', showlegend=False, line_width=line_width,
                          line=dict(dash='dash'))
    tc_diag = go.Scatter(x=[0, inside_time], y=[0, oc_accept],
                         line_color=palette['g'], mode='lines', showlegend=False, line_width=line_width,
                         line=dict(dash='dash'))
    tc_solid = go.Scatter(x=[inside_time, inside_time], y=[0, oc_accept],
                          line_color=palette['tc'], mode='lines', name="Time's Cost", line_width=line_width,
                          line=dict(dash='solid'))
    tc_dash = go.Scatter(x=[inside_time, inside_time], y=[0, oc_accept],
                         line_color=palette['tc'], mode='lines', name="Time's Cost", line_width=line_width,
                         line=dict(dash='4, 4'))
    opp_solid = go.Scatter(x=[inside_time, inside_time], y=[0, oc_forgo],
                           line_color=palette['opp'], mode='lines', name="Opportunity Cost", line_width=line_width,
                           line=dict(dash='solid'))
    opp_dash = go.Scatter(x=[inside_time, inside_time], y=[0, oc_forgo],
                          line_color=palette['opp'], mode='lines', name="Opportunity Cost", line_width=line_width,
                          line=dict(dash='dot'))
    app_solid = go.Scatter(x=[inside_time, inside_time], y=[oc_accept, oc_forgo],
                           line_color=palette['app'], mode='lines', name="Apportionment Cost", line_width=line_width,
                           line=dict(dash='solid'))
    app_dash = go.Scatter(x=[inside_time, inside_time], y=[oc_accept, oc_forgo],
                          line_color=palette['app'], mode='lines', name="Apportionment Cost", line_width=line_width,
                          line=dict(dash='dot'))

    if sv:
        new_fig.add_trace(sv_mid)
        if tc or opp or app:
            new_fig.add_trace(sv_side)

    if opp or app:
        new_fig.add_trace(opp_diag)

    if tc or app:
        new_fig.add_trace(tc_diag)

    if tc:
        if opp or app:
            new_fig.add_trace(tc_solid)
            # new_fig.add_trace(tc_dash)
        else:
            new_fig.add_trace(tc_solid)

    if opp:
        if tc:
            new_fig.add_trace(opp_dash)
        else:
            new_fig.add_trace(opp_solid)

    if app:
        if tc:
            new_fig.add_trace(app_dash)
        else:
            new_fig.add_trace(app_solid)

    new_fig.update_layout(
        transition_duration=transition_duration,
        xaxis_title="Outside Time" + " " * 100 + "Inside Time",
        yaxis_title="Outside Reward" + " " * 30 + "Inside Reward",
        plot_bgcolor='white'
    )
    new_fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=[-10, -5, 0, 5, 10],
            ticktext=[10, 5, 0, 5, 10]
        )
    )
    new_fig.update_layout(
        yaxis=dict(
            tickmode='array',
            tickvals=[-4, -2, 0, 2, 4],
            ticktext=[4, 2, 0, 2, 4]
        )
    )
    new_fig.update_xaxes(
        range=(-limits[1] * 1.05, limits[1] * 1.05),
        constrain='domain',
    )
    new_fig.update_yaxes(
        range=(-limits[0] + 2, limits[0] - 2),
        constrain='domain'
    )

    return new_fig


def make_text(text):
    text_elements = [html.H2(s, className='text-center') for s in text]
    return dbc.Card(children=text_elements, style={"height": "90px", "width": "300px", 'textAlign': 'center'},
                    className="border-0 bg-transparent")


def increase_button(button_id):
    return dmc.ActionIcon(DashIconify(icon="teenyicons:up-outline", width=100), size='lg', id=button_id,
                          style={"height": "80px", "width": "300px"})


def decrease_button(button_id):
    return dmc.ActionIcon(DashIconify(icon="teenyicons:down-outline", width=100), size='lg', id=button_id,
                          style={"height": "80px", "width": "300px"})


def input_box(input_id, val):
    return dbc.Card(children=[dcc.Input(id=input_id, type='text', value=val, placeholder=0, debounce=True)],
                    style={"height": "40px", "width": "300px", 'textAlign': 'center'},
                    className="border-0 bg-transparent")


def make_button(text, inc_button_id, dec_button_id, input_id, val):
    return dbc.Card(children=[increase_button(inc_button_id), make_text(text), decrease_button(dec_button_id),
                              input_box(input_id, val)],
                    className="border-0 bg-transparent")


def value_card_row(selections, values, selected):
    palette = get_palette(string=True)
    subjective_value, oc_accept, oc_forgo, policy_cost = calc_values(*values)
    cards = []
    if selections[0] in selected:
        cards.append(dbc.Col(make_value_card(selections[0], 'subjective-value', subjective_value, palette['sv'])))
    if selections[1] in selected:
        cards.append(dbc.Col(make_value_card(selections[1], 'oc-accept', oc_accept, palette['tc'])))
    if selections[2] in selected:
        cards.append(dbc.Col(make_value_card(selections[2], 'oc-reject', oc_forgo, palette['opp'])))
    if selections[3] in selected:
        cards.append(dbc.Col(make_value_card(selections[3], 'policy-cost', policy_cost, palette['app'])))
    return dbc.Row(cards + [dbc.Col(make_blank_card()) for _ in range(5 - len(cards))])
    # return dbc.Row([
    #     dbc.Col(make_value_card(selections[0], 'subjective-value', subjective_value, palette['p2'])
    #             if selections[0] in selected else make_blank_card()),
    #     dbc.Col(make_value_card(selections[1], 'oc-accept', oc_accept, palette['g'])
    #             if selections[1] in selected else make_blank_card()),
    #     dbc.Col(make_value_card(selections[2], 'oc-reject', oc_forgo, palette['bg'])
    #             if selections[2] in selected else make_blank_card()),
    #     dbc.Col(make_value_card(selections[3], 'policy-cost', policy_cost, palette['p3'])
    #             if selections[3] in selected else make_blank_card()),
    #     dbc.Col(make_blank_card())
    # ])


def make_value_card(name, card_id, value, color):
    light_color = color[:-1] + ', .5)'
    print(light_color)
    return dbc.Card([
        dbc.CardHeader(name, style={'background-color': color, 'color': 'rgb(255,255,255)'}),
        dbc.CardBody([html.P(round(value, 3), className="card-text", id=card_id)],
                     style={'background-color': light_color}),
    ])


def make_blank_card():
    return dbc.Card(className="border-0 bg-transparent")


def build_app(app):
    # app.layout = html.Div("This is the Dash app.")

    starting = [1.0, 6.0, 3.0, 2.0]  # background reward, background time, pursuit reward, pursuit time
    limits = [7, 10]  # reward, time
    step_size = max(limits) / 20  # reward, time

    selections = ["Subjective Value",
                  "Time's Cost",
                  "Opportunity Cost",
                  "Apportionment Cost"]

    fig = make_fig(starting, limits, selections)
    app.position = starting
    app.clicks = [[0, 0, 0, 0], [0, 0, 0, 0]]
    app.layout = dbc.Container([
        html.Br(),
        dbc.Row(
            html.H1('Interactive Optimality Plot')
        ),
        html.Br(),
        dbc.Row(
            dbc.Col(
                dmc.ChipGroup(multiple=True,
                              children=[dmc.Chip(x, value=x) for x in selections],
                              id="chips-values", value=[]))
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(figure=fig, id='graph', style={'width': '150vh', 'height': '60vh'}))
        ),
        dbc.Row([
            dbc.Col(make_button(['Outside', 'Reward'], 'background-reward-increase', 'background-reward-decrease',
                                'background-reward-number', starting[0])),
            dbc.Col(make_button(['Outside', 'Time'], 'background-time-increase', 'background-time-decrease',
                                'background-time-number', starting[1])),
            dbc.Col(make_button(['Inside', 'Reward'], 'pursuit-reward-increase', 'pursuit-reward-decrease',
                                'pursuit-reward-number', starting[2])),
            dbc.Col(make_button(['Inside', 'Time'], 'pursuit-time-increase', 'pursuit-time-decrease',
                                'pursuit-time-number', starting[3]))
        ]),
        html.Br(),
        dbc.Row([value_card_row(selections, starting, [])], id='values-row'),
        html.Br(),
    ])

    @app.callback(
        Output("graph", "figure"),
        Output("background-reward-number", "value"),
        Output("background-time-number", "value"),
        Output("pursuit-reward-number", "value"),
        Output("pursuit-time-number", "value"),
        Output("values-row", "children"),

        Input("background-reward-increase", "n_clicks"),
        Input("background-time-increase", "n_clicks"),
        Input("pursuit-reward-increase", "n_clicks"),
        Input("pursuit-time-increase", "n_clicks"),
        Input("background-reward-decrease", "n_clicks"),
        Input("background-time-decrease", "n_clicks"),
        Input("pursuit-reward-decrease", "n_clicks"),
        Input("pursuit-time-decrease", "n_clicks"),
        Input("background-reward-number", "value"),
        Input("background-time-number", "value"),
        Input("pursuit-reward-number", "value"),
        Input("pursuit-time-number", "value"),
        Input("chips-values", "value"),
    )
    def update(background_reward_increase, background_time_increase, pursuit_reward_increase, pursuit_time_increase,
               background_reward_decrease, background_time_decrease, pursuit_reward_decrease, pursuit_time_decrease,
               background_reward_number, background_time_number, pursuit_reward_number, pursuit_time_number,
               selection_values):
        nums = [background_reward_number, background_time_number, pursuit_reward_number,
                pursuit_time_number]
        upper_limits = [limits[0], limits[1], limits[0], limits[1]]
        lower_limits = [-limits[0], 0, -limits[0], 0]
        if app.position != nums:
            nums = [str(num) for i, num in enumerate(nums)]
            nums = [float(num) if num.replace(".", "").isnumeric() else starting[i] for i, num in enumerate(nums)]
            nums = [num if num <= upper_limits[i] else upper_limits[i] for i, num in enumerate(nums)]
            nums = [num if num >= lower_limits[i] else lower_limits[i] for i, num in enumerate(nums)]
            app.position = nums
            transition_duration = 100
        else:
            increases = [background_reward_increase, background_time_increase, pursuit_reward_increase,
                         pursuit_time_increase]
            decreases = [background_reward_decrease, background_time_decrease, pursuit_reward_decrease,
                         pursuit_time_decrease]
            increases = [x if x is not None else 0 for x in increases]
            decreases = [x if x is not None else 0 for x in decreases]

            changes_up = [b - a for a, b in zip(app.clicks[0], increases)]
            changes_down = [b - a for a, b in zip(app.clicks[1], decreases)]
            app.clicks = [increases, decreases]
            new_position = [a + step_size * (b - c) if (a + step_size * (b - c) <= upper_limits[i]) & (
                    a + step_size * (b - c) >= lower_limits[i]) else a for i, (a, b, c) in
                            enumerate(zip(app.position, changes_up, changes_down))]
            transition_duration = 100 if new_position != app.position else 0
            app.position = new_position
        app.position = [round(num, 3) for num in app.position]
        return make_fig(app.position, limits, selections, selection_values=selection_values,
                        transition_duration=transition_duration), \
               app.position[0], app.position[1], app.position[2], app.position[3], \
               value_card_row(selections, app.position, selection_values)

    return app


# server = flask.Flask(__name__)
#
#
# @server.route("/")
# def home():
#     return "Flask App"


app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN])
# app = dash.Dash(external_stylesheets=[dbc.themes.CERULEAN], server=server, routes_pathname_prefix="/interactive/")
server = app.server
app = build_app(app)


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=False)
