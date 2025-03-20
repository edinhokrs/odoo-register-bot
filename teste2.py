import time
import os
import pandas as pd
import logging
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuração do log
logging.basicConfig(filename='cadastros_erro.log', level=logging.ERROR, 
                    format='%(asctime)s - %(message)s')

load_dotenv()

EMAIL = os.getenv("EMAIL")
SENHA = os.getenv("SENHA")

# Configuração das opções do Chrome
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-dev-shm-usage")

# Caminho para o ChromeDriver
service = Service("/usr/bin/chromedriver")

# Inicializa o Chrome
driver = webdriver.Chrome(service=service, options=chrome_options)

# Função de login
def login_odoos():
    try:
        driver.get("https://falkerstaging.cloud.escodoo.com")

        # Aguarda o carregamento da página
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Verifica se já estamos logados
        if "web/login" not in driver.current_url:
            print("Já está logado.")
            return

        # Preenche os campos de login
        login_field = driver.find_element(By.ID, "login")
        password_field = driver.find_element(By.ID, "password")

        login_field.send_keys(EMAIL)
        password_field.send_keys(SENHA)
        password_field.send_keys(Keys.RETURN)

        # Aguarda até que a página mude após o login
        WebDriverWait(driver, 20).until(EC.url_changes(driver.current_url))
        print("Login feito com sucesso!")

    except Exception as e:
        print(f"Erro no login: {e}")
        driver.quit()
        exit()

# Função para detectar e fechar um modal com o botão "Ok"
def detectar_fechar_modal():
    try:
        # Verifica a presença de um modal na página
        modal = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "modal-content"))
        )
        print("Modal detectado!")

        # Tenta encontrar o botão "Ok" e clicar
        ok_button = WebDriverWait(modal, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@class='btn btn-primary']/span[text()='Ok']"))
        )
        time.sleep(3)
        ok_button.click()
        print("Botão 'Ok' do modal clicado.")
        
        # Espera o modal desaparecer
        WebDriverWait(driver, 5).until(EC.invisibility_of_element(modal))
        print("Modal fechado.")
        return True
        
    except Exception:
        print("Nenhum modal detectado ou erro ao fechar modal.")
        return False  # Retorna False caso não haja modal

# Função para cadastrar ou atualizar clientes
def cadastrar_cliente(nome, cnpj, telefone, email):
    try:
        # Ir para a tela de parceiros se necessário
        driver.get("https://falkerstaging.cloud.escodoo.com/web#action=342&model=res.partner&view_type=kanban&cids=1&menu_id=525")

        # Detecta e fecha modal, caso apareça
        detectar_fechar_modal()

        # Aguarda o botão de novo cadastro aparecer e clica
        novo_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.btn-primary.o-kanban-button-new"))
        )
        novo_button.click()

        # Preenche os campos
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "name"))).send_keys(nome)

        try:
            cnpj_cpf_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "cnpj_cpf")))
            cnpj_cpf_field.send_keys(cnpj)
        except Exception:
            print(f"Campo CNPJ não encontrado para {nome}")

        # Pesquisa o CNPJ
        try:
            search_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "action_open_cnpj_search_wizard"))
            )
            search_button.click()
            time.sleep(5)

            # Detecta e fecha modal, caso apareça
            if detectar_fechar_modal():  # Se retornar True, há um modal
                print('caiu no return')
                logging.error(f"CNPJ não cadastrado: {cnpj}")
                return  # Retorna e não continua o processo

        except Exception:
            print(f"Erro ao buscar dados do CNPJ para {cnpj}")

        # Atualizar parceiro
        try:
            update_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "action_update_partner"))
            )
            time.sleep(25)
            update_button.click()                        
        except Exception:
            print(f"Erro ao atualizar parceiro para {cnpj}")

        time.sleep(10)

        # Preencher telefone e e-mail
        try:
            phone_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "phone"))
            )
            phone_field.clear()
            phone_field.send_keys(telefone)
        except Exception:
            print(f"Erro ao preencher telefone para {cnpj}")

        try:
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "email"))
            )
            email_field.clear()
            email_field.send_keys(email)
        except Exception:
            print(f"Erro ao preencher e-mail para {cnpj}")

        # Salvar
        try:
            save_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "o_form_button_save"))
            )
            save_button.click()
            print(f"Cadastrado/Atualizado: {cnpj}")
        except Exception:
            print(f"Erro ao salvar cliente {cnpj}")

    except Exception as e:
        print(f"Erro ao processar {cnpj}: {e}")

# Carregar os dados do CSV
df = pd.read_csv('dados_empresas.csv')
print(df.head())  # Para visualizar as primeiras linhas

# Login
login_odoos()

# Processar clientes
for _, row in df.iterrows():
    print(f'dados: {row['nome']}, {row['cnpj']}, {row['telefone']}, {row['email']}')
    cadastrar_cliente(row['nome'], row['cnpj'], row['telefone'], row['email'])
    time.sleep(5)

# Fechamento seguro
try:
    driver.quit()
except Exception:
    print("Erro ao fechar o driver.")
