# Gramática de página e lições de apresentação do manual estratégico

Complemento de `strategic_manual_reference.md`. Descreve como o original monta cada página, o ritmo visual do documento inteiro e os erros de consistência que ele tem, para o sistema aplicar a si mesmo as mesmas regras. Fonte: 66 páginas distintas lidas a 1080 px. Nada de texto, nome ou número do original é copiado.

Níveis de confiança: 🟢 observado · 🟡 inferido · 🔴 hipótese.

## 1. Formato e sistema visual 🟢

- Página 16:9, uma ideia por página, sem parágrafo corrido longo.
- Paleta em preto, branco e cinza. A cor nunca carrega significado. Em gráficos, a barra do público da marca é preta e as demais são cinza. No anel, as fatias vão do preto ao cinza claro.
- Uma família tipográfica sem serifa, geométrica, em dois pesos. Títulos de uma frase em peso leve e peso extra-pesado na parte que carrega a ideia. 🟡 O peso pesado funciona como a camada de leitura rápida.
- Microrótulos em caixa alta com espaçamento largo para sobretítulo, rótulos de coluna e cabeçalho.
- Número do capítulo em corpo gigante, quase apagado, no canto superior direito de cada página (marca d'água).

## 2. Gramática da página 🟢

1. Cabeçalho corrente: número e nome do capítulo à esquerda, nome do documento à direita.
2. Sobretítulo em caixa alta que diz o tema.
3. Título de uma frase que afirma. Exemplo de padrão: um achado, não um rótulo.
4. Corpo em módulo: colunas, tabela, régua, linha do tempo, diagrama ou gráfico.
5. Um único módulo escuro por página para o que mais importa (a persona de maior valor, o território, a etapa final da narrativa, o que não cabe).
6. Rodapé de definição, 'Por trás do termo', com uma ou duas linhas para o leigo. Em páginas de dados, o rodapé traz a fonte.
7. Rodapé corrente: assinatura do autor à esquerda, tipo do documento e ano ao centro, número da página à direita.

## 3. Ritmo do documento 🟢

| Recurso | Uso |
|---|---|
| Página de capítulo escura | Número grande à esquerda, título e uma linha de subtítulo, lista numerada do que vem no capítulo à direita |
| Páginas de virada | Fundo alterna escuro, claro, escuro, claro ao longo das sete |
| Páginas escuras no meio do capítulo | Reservadas para a consequência de um cenário, a proposta de valor, a big idea, o manifesto e o encerramento |
| Alternância claro e escuro | Marca a troca de parte e dá respiro a quem folheia |

🟡 Regra para o sistema: página escura só para o que o autor quer que o leitor não esqueça. Mais de um terço do documento escuro tira esse efeito.

## 4. Lições de apresentação

1. O documento é um guia para decidir e não material para ler. A carta de abertura diz isso e diz a quem serve: ao dono, à equipe e a qualquer pessoa que fale em nome da marca. 🟢
2. Cada termo técnico aparece com a sua tradução no rodapé da mesma página. O leitor nunca precisa de glossário no fim. 🟢
3. O autor mostra o que corrige a leitura do cliente e assume um olhar crítico sobre as metas. 🟢 🟡 Isso dá credibilidade, porque o documento não só concorda com o dono.
4. Toda amostra pequena traz n e a frase de sinal qualitativo. 🟢
5. O fecho reformula a conclusão em uma frase e aponta o próximo passo. 🟢

## 5. Erros de consistência no original

Estes pontos aparecem no original. Confirme no arquivo de origem antes de tratá-los como defeito, porque a leitura foi a 1080 px.

| Regra | O que se observa | Id |
|---|---|---|
| Número de página único e em ordem | Dois pares de páginas imprimem o mesmo número, e o sumário aponta uma página que não bate | Q1 |
| Cabeçalho igual ao sumário | O capítulo de direção tem um número no sumário e outro no cabeçalho de suas páginas | Q2 |
| Ano único no rodapé | O rodapé mostra 2025 em algumas páginas e 2026 em outras, e a capa traz 2026 | Q3 |
| Fatias somam 100 | O anel de pilares de conteúdo soma 100 | Q4 |
| Amostra pequena rotulada | A pesquisa declara n e natureza qualitativa | Q5 |
| Dado de mercado com fonte | Presente na página e na lista final | Q6 |
| Tensão com decisão | As sete tensões têm decisão | Q7 |
| Plataforma derivada | As doze células repetem textos das páginas anteriores | Q8 |

As oito regras estão em `qa_rules` no blueprint, em formato legível por máquina. 🟡 Elas viram linter do manual HTML do brand-ecosystem quando o capítulo estratégico existir: número único, sumário com página real, cabeçalho igual ao capítulo, ano único, soma de fatias igual a 100, n e natureza em toda amostra, fonte em todo dado e decisão em toda tensão.

## 6. O que aplicar já

- No passo 3 do brand-studio: cada achado de diagnóstico leva duas camadas, o que encontramos e o que isso significa.
- No passo 4: toda tensão fecha com uma decisão escrita. Todo diferencial passa pelo teste de cópia.
- No briefing do passo 9: a plataforma em uma página é derivada, nunca escrita à mão.
- Na entrega ao cliente: duas leituras. A rápida são os títulos e os módulos escuros. A lenta são os corpos e os rodapés de definição.
