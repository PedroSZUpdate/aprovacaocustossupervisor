import win32com.client
import pandas as pd


def send_outlook_email(to_address, type, df, mes=None):
    if type == "requisicao":
        subject = "Nova solicitação de Movimentação de Saldo"
        body = "Há uma nova solicitação de movimentação de saldo para sua aprovação:"
    elif type == "aprovacao":
        subject = "Aprovada - Solicitação de Movimentação de Saldo"
        body = "Sua solicitação de movimentação de saldo foi aprovada:"
    elif type == "reprovacao":
        subject = "Reprovada - Solicitação de Movimentação de Saldo"
        body = "Sua solicitação de movimentação de saldo foi reprovada:"
    elif type == "aprovar":
        subject = "Nova Solicitação de Aprovação de Ordem acima do Saldo Disponível"
        body = "Há uma nova solicitação de aprovação de ordem:"
    elif type == "ge":
        subject = "Notificação de Estouro de Custo"
        body = "As seguintes ordens foram aprovadas estourando o saldo disponível:"
    else:
        subject = "Erro"
        body = "Erro"
    # Convert the DataFrame to an HTML table without class attributes
    html_table = df.to_html(index=False, header=True)

    # Split the HTML table into rows for manipulation
    rows = html_table.split('<tr>')

    # Initialize the updated table with the initial part of the table
    updated_table = rows[0] + '<tr>'

    # Loop through the rows to add alternating colors
    for i, row in enumerate(rows[1:], start=1):
        color = '#f2f2f2' if i % 2 == 0 else '#ffffff'
        if '<th>' in row:  # If it's a header row, skip adding background color
            updated_table += row
        else:
            updated_table += f'<tr style="background-color: {color};">{row}'

    # Custom styles for the HTML table
    styles = """
    <style>
        .dataframe {
            border-collapse: collapse;
            width: 100%;
            text-align: center;
        }
        .dataframe th {
            background-color: black;
            color: white;
            text-align: center;
            padding: 8px;
        }
        .dataframe td {
            text-align: center;
            padding: 8px;
        }
    </style>
    """

    # Create the Outlook application object
    outlook = win32com.client.Dispatch("Outlook.Application")
    mail = outlook.CreateItem(0)  # 0 represents the olMailItem enum value

    # Set up the email details
    mail.Subject = subject
    mail.BodyFormat = 2  # Set the body format to HTML
    mail.HTMLBody = f"""
    <html>
    <head>{styles}</head>
    <body>
        <p>{body}</p>
        <table class="dataframe">{updated_table}</table>
    </body>
    </html>
    """
    mail.To = to_address

    # Send the email
    mail.Send()


if __name__ == "__main__":
    recipient_address = "williamyamashita.gff@suzano.com.br"

    df = pd.DataFrame({
        'Valor': ['Data1', 'Data2', 'R$ 5.567,00', 'R$ 452.342,00', 'aaa', 'e1vefv', 'rdqve'],
        'Mês': ['Data3', 'Data4', 'Jan', 'Abr', 'regbfbf', 'eeg23w', 'tbr2qe']
    })

    # Example usage
    send_outlook_email(recipient_address, "", df)
