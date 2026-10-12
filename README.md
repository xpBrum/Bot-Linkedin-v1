# Bot de Candidaturas — versão inicial

Pode acessar aqui: https://bot-vagas.streamlit.app

Aplicação local em Python para cadastrar/importar vagas, calcular uma pontuação de aderência ao perfil profissional e acompanhar candidaturas. Não faz login nem envia candidaturas automaticamente; a confirmação é manual.

## Requisitos
- Python 3.10 ou superior
- Internet apenas para instalar as dependências; o painel e banco funcionam localmente.

## Instalação (Windows)
1. Extraia o ZIP para uma pasta.
2. Abra o Prompt de Comando dentro da pasta.
3. Crie um ambiente virtual (recomendado):
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. Instale as dependências:
   ```bat
   pip install -r requirements.txt
   ```
5. Inicie:
   ```bat
   streamlit run app.py
   ```
6. O navegador abrirá o painel local. Se não abrir, acesse o endereço local exibido no terminal.

## Como usar
1. Revise o perfil e os termos prioritários na barra lateral.
2. Cole os dados de uma vaga em **Adicionar vaga**, ou importe um CSV na aba **Importar CSV**.
3. Veja a pontuação de 0 a 100 e a justificativa.
4. Abra o link da vaga, revise os requisitos e candidate-se manualmente no site.
5. Clique em **Confirmo: candidatura enviada** para registrar o envio.
6. Atualize o status e exporte seu histórico em CSV.

## CSV
Colunas aceitas: `title` (obrigatória), `company`, `location`, `modality`, `salary`, `url`, `description`.

## Como a pontuação funciona
É uma heurística simples com termos prioritários, interseção de palavras entre descrição e perfil, sinais de formação, modalidade e palavras ligadas a cargos de entrada/desenvolvimento. Não é um modelo de IA e não substitui a leitura da descrição. Ajuste os termos prioritários para refletir cada objetivo.

## Limitações da versão 1
- Não coleta vagas diretamente do LinkedIn.
- Não faz login, não contorna CAPTCHA e não envia candidaturas.
- A pontuação é baseada em palavras-chave; próximas versões podem incluir fontes de vagas autorizadas, melhores regras de senioridade/salário e geração de respostas personalizadas.
- Banco de dados `candidaturas.db` é criado automaticamente na pasta da aplicação. Faça backup se quiser preservar o histórico.
