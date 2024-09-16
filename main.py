import yfinance as yf
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

# Dash uygulaması
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Uygulamanın arayüzü
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Borsa Uygulaması", className='text-center mb-4'), width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Label('Hisse Senedi Sembolü:', style={'color': 'white'}),
            dcc.Input(id='stock-symbol', value='AAPL', type='text', className='form-control', style={'margin-bottom': '20px'}),
        ], width=4),

        dbc.Col([
            html.Label('Tarih Aralığı Seçin:', style={'color': 'white'}),
            # Tarih aralığı seçimi: Hızlı yıl seçimi için dropdown formatında
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date='2023-01-01',
                end_date='2023-09-01',
                display_format='YYYY-MM-DD',
                calendar_orientation='vertical',  # Takvim açılımını dikey yap
                style={'background-color': '#2a2a2a', 'border': '1px solid #555'}
            ),
        ], width=4),

        dbc.Col([
            html.Label('Grafik Türü Seçin:', style={'color': 'white'}),
            dcc.Dropdown(
                id='plot-type',
                options=[
                    {'label': 'Candlestick Grafiği', 'value': 'candlestick'},
                    {'label': 'Çizgi Grafiği', 'value': 'line'},
                    {'label': 'Çubuk Grafiği', 'value': 'bar'},
                    {'label': 'Alan Grafiği', 'value': 'area'}
                ],
                value='candlestick',  # Varsayılan olarak candlestick
                className='form-control'
            )
        ], width=4)
    ], justify='center', className='mb-4'),

    dbc.Row([
        dbc.Col([
            html.Button('Verileri Güncelle', id='submit-button', n_clicks=0, className='btn btn-primary', style={'width': '100%'})
        ], width=2, style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
        
        # Geri Al butonu
        dbc.Col([
            html.Button('Geri Al', id='undo-button', n_clicks=0, className='btn btn-secondary', style={'width': '100%'})
        ], width=2, style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
    ], justify='center', className='mb-4'),

    # Grafik ve durum saklama bileşeni
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='stock-graph'),
            dcc.Store(id='graph-store', data=[])  # Grafik durumlarını saklamak için Store bileşeni
        ], width=12)
    ])
], fluid=True)



@app.callback(
    Output('stock-graph', 'figure'),
    Output('graph-store', 'data'),
    [Input('submit-button', 'n_clicks'),
     Input('undo-button', 'n_clicks')],
    [State('stock-symbol', 'value'),
     State('date-picker-range', 'start_date'),
     State('date-picker-range', 'end_date'),
     State('plot-type', 'value'),
     State('graph-store', 'data')]
)
def update_or_undo_graph(update_clicks, undo_clicks, symbol, start_date, end_date, plot_type, graph_history):
    ctx = dash.callback_context  

    
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle "Verileri Güncelle" button click
    if button_id == 'submit-button':
        if not symbol or not start_date or not end_date:
            return {}, graph_history

        # Hisse senedi verilerini yfinance ile al
        stock = yf.Ticker(symbol)
        data = stock.history(start=start_date, end=end_date)

        # Veri boş mu kontrol et
        if data.empty:
            return {
                'data': [],
                'layout': go.Layout(
                    title=f'{symbol} Hisse Senedi Verisi Bulunamadı',
                    plot_bgcolor='#1f1f1f', paper_bgcolor='#1f1f1f', font=dict(color='white')
                )
            }, graph_history

        # Grafik türüne göre grafik oluştur
        if plot_type == 'candlestick':
            fig = go.Figure(data=[go.Candlestick(x=data.index,
                                                 open=data['Open'],
                                                 high=data['High'],
                                                 low=data['Low'],
                                                 close=data['Close'])])
        elif plot_type == 'line':
            fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Kapanış Fiyatı')])
        elif plot_type == 'bar':
            fig = go.Figure(data=[go.Bar(x=data.index, y=data['Close'], name='Kapanış Fiyatı')])
        elif plot_type == 'area':
            fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], fill='tozeroy', mode='lines', name='Kapanış Fiyatı')])

        # Grafiğin görünümünü düzenle
        fig.update_layout(
            title=f'{symbol} Hisse Senedi {plot_type.capitalize()} Grafiği',
            xaxis_title='Tarih',
            yaxis_title='Fiyat',
            xaxis_rangeslider_visible=False if plot_type != 'candlestick' else True,
            plot_bgcolor='#1f1f1f',  
            paper_bgcolor='#1f1f1f',  
            font=dict(color='white')  
        )

        graph_history.append(fig)

        return fig, graph_history

    
    elif button_id == 'undo-button':
        # Geri alma işlemi varsa ve geçmiş boş değilse
        if undo_clicks > 0 and len(graph_history) > 1:
            graph_history.pop()  # Son grafiği çıkar
            return graph_history[-1], graph_history  # Önceki grafiği göster
        elif len(graph_history) == 1:
            return graph_history[0], graph_history  # İlk grafiği göster 
        else:
            return {}, graph_history  # Grafik yoksa boş döndür

    
    return {}, graph_history


# Uygulamayı çalıştır
if __name__ == '__main__':
    app.run_server(debug=True)
