# Anatomia de um manual de plataforma estratégica

Leitura de 66 páginas distintas de um manual de branding estratégico (cerca de 66 páginas, 2026, português), entregue pelo usuário como imagens. O manual é referência de método. Nada dele é copiado aqui: nem texto, nem nome de cliente, nem número, nem citação, nem fonte de dados.

Níveis de confiança: 🟢 observado direto numa página · 🟡 inferido, com explicação rival · 🔴 hipótese.

Limites honestos: a pasta tem 68 imagens. Duas repetem a mesma página e uma numeração está ausente, então 66 páginas foram lidas. A leitura foi a 1080 px de largura. Notas de rodapé em corpo pequeno ficaram parcialmente ilegíveis. O áudio do reel de onde o material veio não foi transcrito.

## 1. Este manual é a outra metade do manual visual

O manual de 121 páginas (`manual_anatomy_reference.md`) responde como a marca se mostra. Este responde quem a marca é e o que decide ser. Não tem logotipo, cor nem grelha. 🟢 No fim, ele próprio aponta o próximo passo: a identidade visual. 🟡 Leitura: a plataforma vem primeiro e alimenta o código visual. Por isso o blueprint estratégico fica numa camada separada e não muda a contagem de 18 essenciais da parte visual.

`assets/strategic_blueprint.v1.json` guarda 49 necessidades em 5 camadas (22 essenciais, 22 recomendadas, 5 condicionais), a espinha do documento e 8 regras de QA.

## 2. A espinha do documento 🟢

| Bloco | Conteúdo | Páginas |
|---|---|---|
| Abertura | Capa, carta de boas-vindas assinada, sumário, pergunta-guia, método | 1 a 5 |
| 1 Diagnóstico | Leitura por pilar, mercado, premissas e objetivos, pontos de atenção, consumidor e personas, valor percebido, concorrência e território, arquétipo e universo, pesquisa de percepção | 6 a 28 |
| 2 Viradas de chave | Sete viradas e uma síntese | 29 a 37 |
| 3 Direção estratégica | Posicionamento e promessa, essência/propósito/missão/visão, valores e princípios, big idea e slogan, narrativa e manifesto, personalidade e tom, pilares de conteúdo, comunicação e arquitetura, plataforma | 38 a 64 |
| Encerramento | Fecho com próximo passo e fontes | 65 e 66 |

A ordem vai do que se observa (diagnóstico) ao que se decide (direção). Entre os dois, as viradas de chave fazem a ponte: cada uma cruza uma crença do dono com uma evidência. 🟡 Explicação rival: a ordem repete a sequência dos três encontros de imersão.

## 3. O método e a regra que o sustenta 🟢

Quatro pilares: negócio, audiência, valor, estória (a sigla forma o nome do método). Cada um tem uma pergunta. Uma faixa de números mostra a base de evidência: encontros, respostas válidas, anos de histórico e fontes públicas.

A regra do método é separar o que o dono acredita do que as evidências mostram. Onde os dois divergem está a estratégia. 🟡 Isso explica três recursos que o sistema ainda não tinha:

1. **Duas camadas por achado.** Cada pilar tem o que encontramos e o que isso significa. A segunda camada obriga a tirar consequência do fato.
2. **Correção à leitura do dono.** Uma faixa mostra onde a evidência contradiz ou amplia a crença do cliente.
3. **Olhar crítico sobre as metas.** O autor compara a visão do cliente com a capacidade atual e diz que a promessa pública deve ser o que a operação entrega hoje. 🟡 É a regra de não prometer para fora o que não se sustenta dentro.

No sistema, o `evidence_ledger.py` do brand-reverse já separa observado, inferido e hipótese. O manual mostra o equivalente para um projeto novo: cada página de diagnóstico tem de dizer de qual encontro, pesquisa ou fonte saiu.

## 4. Padrões de conteúdo 🟢

| Padrão | Como se constrói | Necessidades |
|---|---|---|
| Pergunta-guia | Contraste entre o que a empresa entrega e o que mostra | P03 |
| Linha do tempo de regras | Marcos datados com fato e efeito, o marco da virada em círculo cheio | P08 |
| Persona de quatro campos | Situação, o que quer, o que trava, frase que precisa ouvir | P15 |
| Tensão com decisão | Dois lados e uma decisão escrita. Sem decisão, a tensão sai | P12 |
| Equação de valor | Ganhos sobre perdas, e uma leitura de cada fator em barras de 1 a 5 com ação | P17 |
| Concorrência por tipo | Faz bem, falha em, a marca faz diferente. Serve para achar o lugar livre | P19 |
| Mapa 2x2 | Dois eixos, quadrante da marca em preto | P20 |
| Arquétipo com sombra | Principal, secundário, o risco de cada um e quem equilibra | P22 |
| Pesquisa pequena, rotulada | n declarado e frase de sinal qualitativo | P23 |
| Viradas numeradas | Número grande, título em duas pesagens e um parágrafo, alternando fundo escuro e claro | P24 |
| Síntese | Cenário, problema, oportunidade, território e percepção desejada | P25 |
| Posicionamento com espectro | Declaração, categoria com o que ela não é e ponto entre popular e exclusivo | P26 |
| Diferencial com teste de cópia | Coluna que diz se a vantagem é conduta (ninguém copia) ou só esforço | P28 |
| Valores com comportamento | Nome, origem e descrição de conduta. Valor só conta se aparece no dia a dia | P30 |
| Big idea com razões | Uma ideia, cinco razões e a ligação com o slogan | P32 |
| Slogan em dois tempos | O que a marca faz e o que isso gera, com regra de uso por contexto | P33 |
| Narrativa em seis etapas | Origem até agora, com a última em destaque | P34 |
| Personalidade em réguas | Dez pares com cinco posições, meio é equilíbrio, uma casa é 75%, a ponta é 100% | P37 |
| Antes e depois | O mesmo recado burocrático, técnico, alarmista e seco, reescrito | P40 |
| Pilares com peso | Cinco assuntos com percentual somando 100 | P42 |
| Plataforma derivada | Doze células que repetem textos de páginas anteriores | P47 |

Três ideias merecem nome:

- **Decisão obrigatória.** Impede o diagnóstico de virar lista de queixas.
- **Teste de cópia.** Separa o que a marca faz do que a marca é. Conduta depende de caráter e por isso ninguém copia. 🟡 É o critério mais útil para o brief de diferenciais, porque força prova.
- **Plataforma derivada.** A página-resumo nunca diz algo que o corpo não disse. 🟡 Inferência: o original só mostra a página pronta, a regra de derivação é do sistema.

## 5. Como o sistema usa isto

1. `brand-system`: `manual_coverage_check.py --blueprint assets/strategic_blueprint.v1.json --source <fonte>` mostra o que uma fonte ainda não responde na camada estratégica.
2. `brand-discovery` (passos 1 a 3): o método de quatro pilares e a base de evidência estruturam briefing, imersão e pesquisa. A regra de separar crença de evidência vira item do gate do passo 3.
3. `brand-direction` (passos 4 e 5): posicionamento, essência, valores, big idea, slogan e arquétipo seguem os padrões da seção 4. A decisão obrigatória e o teste de cópia valem como itens de gate.
4. `brand-ecosystem` (passo 9): o modelo `brand-source.v2` cobre hoje 2 das 49 necessidades. Fechar o resto exige o bloco `strategy.*` na fonte e capítulos no gerador. Isso fica como decisão do projeto.
5. `brand-reverse`: serve de exemplo de estágios recuperáveis. O diagnóstico e a direção aparecem na página. Briefing, pesquisa e rodadas rejeitadas continuam perdidos (LOST).

## 6. O que não foi observado

Uma numeração de página não está na pasta, e a página 6 (abertura do capítulo 1), 29 (abertura do 2) e 38 (abertura do 3) só têm a lista de itens, sem corpo. Se o capítulo de direção tem páginas além das 64 listadas no sumário, não foram vistas. 🔴 Hipótese: o sumário é o que está em todas as cópias do original.
