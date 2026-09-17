# Página do case e card do portfólio

Estes dois arquivos não fazem parte do projeto dbt — são a parte que vai para o
site.

- **`index.html`** — a página independente do case, em PT/EN com botão de troca.
- **`card-para-o-portfolio.html`** — o card que entra na aba de projetos do site
  e aponta para a página acima. As instruções de encaixe estão no comentário no
  topo do arquivo.

- **`resultados.json`** — o placar do último build, gerado por
  `scripts/resumo_testes.py`. A página traz uma cópia embutida como fallback e
  tenta buscar a versão publicada pela CI em
  `gabigattirodrigues.github.io/alexandria/resultados.json`. Você não precisa
  copiar este arquivo para o site: ele está aqui só para conferência.

- **`farol-de-alexandria.jpg`** — a gravura usada no topo da página. Ela já está
  embutida no `index.html` como data URI, então o arquivo solto é opcional.

## Onde cada coisa vai (importante)

O GitHub Pages de um repositório de projeto já ocupa
`gabigattirodrigues.github.io/<nome-do-repo>/`. Como a documentação do dbt vai
sair em `gabigattirodrigues.github.io/alexandria/`, **a página do case não pode
ficar numa pasta `alexandria/` do site pessoal** — os dois brigariam pelo mesmo
endereço.

O caminho já configurado nos arquivos é este:

| O quê | Repositório | Endereço |
|---|---|---|
| Página do case | `gabigattirodrigues.github.io` → pasta `projetos/alexandria/` | `gabigattirodrigues.github.io/projetos/alexandria/` |
| Documentação e linhagem do dbt | `alexandria` (GitHub Pages do próprio projeto) | `gabigattirodrigues.github.io/alexandria/` |

Ou seja: copie `index.html` para `projetos/alexandria/index.html` no repositório
do site, e o card já aponta para lá.

## Antes de publicar

A documentação só existe depois de ativar o GitHub Pages no repositório do
projeto dbt (Settings → Pages → Source: GitHub Actions) e rodar o workflow uma
vez. Até lá, o botão "Documentação e linhagem" vai dar 404 — e os gráficos da
página vão mostrar o snapshot embutido, que é o build de hoje.

O selo verde do GitHub Actions também só aparece depois do primeiro push, porque
é o GitHub que gera a imagem.

## Os gráficos

Os números dos gráficos não estão escritos no HTML à mão. Eles vêm de
`resultados.json`, que sai de `target/run_results.json` — o artefato que o dbt
escreve a cada execução. A página tenta primeiro a versão publicada pela CI (o
build mais recente) e cai no snapshot embutido se não conseguir.

Se um dia você tirar ou acrescentar um teste, o gráfico muda sozinho no próximo
build. Não tem número para atualizar na mão.
