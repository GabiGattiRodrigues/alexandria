# Primeiros passos (Windows)

Ordem recomendada: **rodar na sua máquina primeiro, subir pro GitHub depois.**
Assim você já sabe que passa antes de o selo do Actions ficar público.

---

## 1. Escolha a pasta

Descompacte em algo como `C:\dev\alexandria`.

**Evite a Área de Trabalho dentro do OneDrive.** Funciona, mas o OneDrive tenta
sincronizar os milhares de arquivos do ambiente virtual e o banco DuckDB, o que
deixa tudo lento e às vezes trava arquivo em uso no meio do build. O `rodar.bat`
avisa se detectar que está rodando de dentro do OneDrive.

Você precisa de Python instalado (python.org, marcando **Add Python to PATH**).

## 2. Rode o `rodar.bat`

Dois cliques. Ele faz tudo sozinho:

1. cria o ambiente virtual
2. instala dbt e DuckDB
3. gera a amostra sintética (ou usa os CSVs reais, se estiverem em `data\raw`)
4. carrega a camada bronze
5. constrói silver e gold e **roda os 75 testes**
6. gera a documentação, o placar e o dashboard de qualidade

No fim ele diz uma de duas coisas: *liberado para subir* ou *algum teste falhou,
não suba ainda*. Depois pergunta se você quer abrir a documentação com o grafo
de linhagem.

Da primeira vez demora uns minutos, por causa da instalação. Das próximas, uns
segundos.

### Ver o dashboard de qualidade

Duas versões, a partir dos mesmos dados:

- **Estática:** abra `site\qualidade.html` com dois cliques. É essa que vai pro ar.
- **Interativa:** `.venv\Scripts\streamlit run app\dashboard_qualidade.py` — com
  filtros, ordenação e seleção de tabela.

### Se quiser usar o dataset real

Baixe em
[kaggle.com/datasets/olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
descompacte os CSVs em `data\raw` e rode o `.bat` de novo. Ele detecta sozinho e
passa a usar os dados reais. Os números dos gráficos mudam junto.

## 3. Suba pro GitHub

Só depois que o passo 2 der verde.

Crie o repositório vazio em github.com/new — **público**, senão o GitHub Actions
e o Pages não são gratuitos e o selo não aparece. Sem README nem .gitignore, para
não dar conflito.

Depois, clone onde você costuma trabalhar (a Área de Trabalho, por exemplo) e use
o **`publicar.bat`** para copiar esta pasta de teste para dentro do clone:

```
publicar.bat
```

Ele pergunta o caminho do clone (dá pra arrastar a pasta pra cima da janela) e
copia tudo, deixando de fora `.venv`, `target`, `dbt_packages`, `data`, `logs` e
o `.duckdb` — que é o que faria o OneDrive sofrer. No fim ele imprime os comandos
do git.

No clone:

```bash
git add .
git commit -m "Alexandria: modelagem, governanca e observabilidade"
git branch -M main
git remote add origin https://github.com/GabiGattiRodrigues/alexandria.git
git push -u origin main
```

**Confira no `git status` se estes quatro foram junto** — são eles que alimentam
os gráficos:

```
site\resultados.json   site\qualidade.json
site\qualidade.html    site\historico.jsonl
```

## 4. Ligue o GitHub Pages

No repositório: **Settings → Pages → Source: GitHub Actions**.

No primeiro push o workflow roda sozinho e publica **tudo** no Pages deste mesmo
repositório:

| Endereço | O que abre |
|---|---|
| `gabigattirodrigues.github.io/alexandria/` | a página do case |
| `.../alexandria/qualidade.html` | o dashboard de observabilidade |
| `.../alexandria/docs/` | a documentação do dbt com o grafo de linhagem |

Você não precisa copiar página nenhuma para o repositório do site.

## 5. Coloque o card no portfólio

Cole o bloco de `site\card-para-o-portfolio.html` na aba de projetos do seu site.
Ele só aponta para os endereços acima. O detalhe está em
[`site/LEIAME.md`](site/LEIAME.md).

## 6. (Opcional) Publique o dashboard interativo

Em share.streamlit.io, aponte para o repositório e para o arquivo
`app/dashboard_qualidade.py`. O `requirements.txt` da raiz já tem o que ele
precisa. A versão estática continua no ar de qualquer jeito — o Streamlit é o
extra, não a dependência.

---

## Quando algo der errado

| Sintoma | O que é |
|---|---|
| `python nao encontrado` | Python não está no PATH. Reinstale marcando "Add Python to PATH". |
| `dbt deps` falha | Sem internet ou proxy bloqueando `hub.getdbt.com`. |
| Trava no meio, arquivo em uso | Quase sempre OneDrive sincronizando. Mova a pasta para fora. |
| Um teste falha | É o projeto funcionando. A mensagem diz qual regra foi violada. |
| Selo do README quebrado | O workflow ainda não rodou, ou o repositório está privado. |
