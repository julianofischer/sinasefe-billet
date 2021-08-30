import os
import pdftotext
import smtplib, ssl
import pickle
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
load_dotenv()


class Person:
    def __init__(self, nome, mensalidade):
        self.nome = nome
        self.mensalidade = mensalidade
        self.dependencia = None
        self.data_nascimento = None
        self.data_inclusao = None
        self.dependentes = []
        self.utilizacao = 0
        self.taxa_boleto = 2.93
        self.reaj_retro = 0
        self.reaj_faixa = 0
        
    def get_valor_mensalidades(self):
        valor_dependentes = sum([x.mensalidade for x in self.dependentes])
        return self.mensalidade + valor_dependentes
    
    def get_valor_utilizacao(self):
        valor_dependentes = sum(x.utilizacao for x in self.dependentes)
        return self.utilizacao + valor_dependentes
    
    def get_valor_reaj_retroativo(self):
        valor_dependentes = sum([x.reaj_retro for x in self.dependentes])
        return self.reaj_retro + valor_dependentes
    
    def get_valor_reaj_faixa(self):
        valor_dependentes = sum([x.reaj_faixa for x in self.dependentes])
        return self.reaj_faixa + valor_dependentes
    
    def get_valor_total(self):
        return self.get_valor_mensalidades() + self.get_valor_utilizacao() + self.taxa_boleto + self.get_valor_reaj_retroativo() + self.get_valor_reaj_faixa()

    def __str__(self):
        return f'{self.nome} - {self.get_valor_total()}'

    def __repr__(self):
        return f'{self.nome} - {self.get_valor_total()}'

    def report_values(self):
        l = []
        l.append(f'{self.nome}: {self.mensalidade:.2f}')
        l.append(f'Utilização: {self.utilizacao:.2f}')
        l.append(f'Reajuste retroativo: {self.reaj_retro:.2f}')
        l.append(f'Reajuste faixa etária: {self.reaj_faixa:.2f}')
        for p in self.dependentes:
            l.append(f'{p.nome}: {p.mensalidade:.2f}')
            l.append(f'Reajuste retroativo: {p.reaj_retro:.2f}')
            l.append(f'Reajuste faixa etária: {p.reaj_faixa:.2f}')
        return l


def load_contacts():
    d = {}
    with open("nomes", 'r') as fi:
        for line in fi.readlines():
            line = line.split(" ")
            # name : email
            nome = line[0].strip()
            email = line[1].strip()
            d[nome] = email
    print(d)
    return d


def rename_pdfs():
    print("renaming pdfs")
    for r, d, f in os.walk("."):
        for file in f:
            if '.pdf' in file:
                with open(file, "rb") as pdf:
                    pdftext = pdftotext.PDF(pdf)
                    nome = \
                    pdftext[0][pdftext[0].find("Valor Cobrado"):pdftext[0].find("CPF")].split("\n")[2].split("-")[
                        0].strip().replace(" ", "-")
                    newname = nome+".pdf"
                    i = 1
                    while os.path.exists(newname):
                         newname = f'{nome}_{i}.pdf'
                         i = i + 1
                    os.rename(file, newname)


def send_email(name, email):
    api_key = os.getenv("ENV_API_KEY")
    email_address_from = os.getenv("ENV_EMAIL_FROM")
    
    print(f'Sending email to {name}')
    o = get_object(objetos, name)
    if o == None:
        raise Exception("Erro")
    port = 465  # For SSL
    fromaddr = email_address_from
    toaddr = email
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Boleto agosto 2021"
    body = f"""Este é um e-mail automático.
Solicitamos que verifique as informações do boleto.

Muito obrigado pela atenção.

RELATÓRIO:
{o.report_values()}

Atenciosamente,
Juliano Fischer Naves"""

    msg.attach(MIMEText(body, 'plain'))

    filename = name+".pdf"
    print(filename)
    attachment = open(filename, "rb")
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment", filename=filename)
    msg.attach(p)
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()

    s.login(fromaddr, api_key)

    text = msg.as_string()
    s.sendmail(fromaddr, toaddr, text)
    s.quit()

def get_object(objetos, key):
   for o in objetos:
       if o.nome.upper().replace(' ', '-') == key:
           print(f"{o.nome.upper().replace(' ', '-')} == {key}")
           return o
   return None


if __name__ == '__main__':
    print("running main")
#    rename_pdfs()

    d = load_contacts()
    global objetos
    objetos = pickle.load(open( "titulares-agosto-21", "rb" ))
    with open('log', 'w') as f:
        for key, item in d.items():
           try:
               send_email(key, item)
               f.write(f'{key} SUCCESS\n')
           except Exception as e:
               f.write(f'{key} FAILED {str(e)}\n')
               print(e)
