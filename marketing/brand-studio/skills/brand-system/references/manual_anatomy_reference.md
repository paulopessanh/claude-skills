# Anatomia de um manual de identidade visual

Leitura de engenharia reversa de um manual corporativo real de 121 páginas (2005, grupo nacional de energia, em português). O manual é referência de método. Nada dele é copiado aqui: nem texto, nem figura, nem nome, nem valor de cor, nem fonte. Quem usa este documento empresta a estrutura e nunca a marca.

Níveis de confiança: 🟢 observado direto no sumário ou no texto do manual · 🟡 inferido, com explicação rival · 🔴 hipótese.

## 1. A espinha: cinco capítulos mais pré-textuais

| Bloco | O que responde | Páginas | Confiança |
|---|---|---|---|
| Pré-textuais (escopo, carta da liderança, porquê da marca, evolução, como consultar, sumário) | Quem manda e como ler | 2 a 8 | 🟢 |
| 1. Códigos visuais | Quais são as peças da marca | 9 a 48 | 🟢 |
| 2. Normas de utilização | Como não quebrá-las | 49 a 71 | 🟢 |
| 3. Aplicações | Como aparecem em peças reais | 72 a 92 | 🟢 |
| 4. Diretrizes de comunicação | Valores, peças institucionais, apoio gráfico, imagens | 93 a 104 | 🟢 |
| 5. Anexo | Arquivos de produção | 105 a 121 | 🟢 |

A ordem é a lógica de uso: primeiro o que a marca é, depois como se protege, depois onde aparece, depois o que ela fala, por fim com quais arquivos se reproduz. 🟡 Um leitor que só quer um logo acha tudo no capítulo 1, e quem produz uma peça vai direto ao 3.

## 2. Os sete níveis de necessidade

O blueprint (`assets/manual_blueprint.v1.json`) lista 34 necessidades. Cada uma tem a pergunta que responde, um padrão sem valores e os campos da fonte que a respondem.

1. Governança do manual (5): autoridade e escopo, voz da liderança, porquê da nitidez, evolução, como consultar.
2. Fundamentos (2): valores e significado das cores.
3. Código visual (7): símbolo, logotipo, lockups, versões cromáticas, arquitetura de marcas, tipografia, cores.
4. Normas de uso (9): redução, proteção, matriz de fundos, texto ao lado, nome em texto, hierarquia, assinatura, grelha, usos incorretos.
5. Aplicações (6): papelaria, formulários, meios digitais de escritório, anúncio, vídeo, brindes e eventos.
6. Linguagem de apoio (3): módulo, símbolo como grafismo, imagens.
7. Entrega (2): arquivos de produção, arquivos de fontes.

## 3. Cinco padrões de método que valem para qualquer marca

1. **Toda medida é relativa.** Proteção, tamanho de texto e espaço entre marcas são frações de uma parte do próprio símbolo, nunca milímetros soltos. Assim a regra escala sozinha. 🟢
2. **A mesma regra vale para todas as versões.** A área de proteção tem a mesma fração nas seis versões (símbolo, vertical e horizontal, cada um sobre a cor da marca e regular). Não há exceção escondida. 🟢
3. **Cada versão diz quando usar.** Não basta mostrar oito versões cromáticas. Cada página traz o critério (cor possível, meio-tom possível, contraste garante a leitura). 🟢
4. **A saída de emergência é nomeada e restrita.** Fundo conflitante pode ser neutralizado preenchendo a área de proteção, "só em último caso". Uma exceção com nome é mais fácil de policiar do que silêncio. 🟢
5. **O manual manda produzir pelo arquivo, nunca redesenhar.** O anexo entrega vetor em três formatos e três sistemas de cor, com a área de proteção marcada num retângulo que não imprime. Há versão editável e versão em curvas das peças. 🟢

## 4. O que se infere e o que se perde

- Briefing, pesquisa e estratégia não aparecem. O manual só mostra efeitos. A carta da liderança e a página de valores deixam ler a intenção, mas são autorrelato. 🟡 Rival: texto escrito depois da decisão visual para justificá-la (Nisbett e Wilson, 1977).
- O significado das cores (sol, trabalho, recurso natural) é narrativa de justificativa. 🟡 Rival: associação escolhida depois de a paleta existir.
- A ordem de domínio das cores (principal, segunda, terceira) é regra observada, não intenção provada. 🟢 regra, 🟡 intenção.

## 5. Onde o manual envelheceu, e o que o nosso sistema já cobre

O manual é de 2005 e pensa em impressão. O sistema brand-studio já cobre o que ele não trata:

| Lacuna do manual | Cobertura no sistema |
|---|---|
| Sem tokens de cor nem tema escuro | Tokens em JSON e CSS, claro e escuro |
| Contraste não calculado | Pares com razão WCAG recalculada pelo auditor |
| Sem voz verbal além de "como escrever o nome" | Capítulo de voz com traços, vocabulário e tom por canal |
| Sem movimento | Capítulo de movimento, com respeito a prefers-reduced-motion |
| Cor impressa só por referência de tinta | CMYK aproximado com aviso de prova de gráfica |

Fonte de confiança: 🟢 para a tabela, pois cada linha é verificável no manual e no pacote.

## 6. Como o sistema usa este blueprint

`scripts/manual_coverage_check.py` lê a fonte da marca e diz, por necessidade, COVERED, PARTIAL ou MISSING, e nomeia o campo que falta. As 34 necessidades se dividem em essenciais (18), recomendadas (10) e condicionais (6). A condicional só vale quando a sua condição existe (por exemplo, arquitetura de marcas só com mais de uma marca). COVERED quer dizer que o dado existe na fonte. A qualidade continua com a revisão.

## Fontes

- O manual de referência (fonte primária, dezembro de 2004 a março de 2005).
- Wheeler, A. Designing Brand Identity, capítulos sobre padrões e diretrizes de marca (Wiley).
- Danne, R. e Blackburn, B. NASA Graphics Standards Manual (1975), exemplo canônico de manual por norma e medida relativa.
- W3C, Web Content Accessibility Guidelines 2.1, critérios 1.4.3 e 1.4.11.
- Design Tokens Community Group, rascunho do formato.
- Nisbett, R. e Wilson, T. (1977), Telling more than we can know, Psychological Review.
