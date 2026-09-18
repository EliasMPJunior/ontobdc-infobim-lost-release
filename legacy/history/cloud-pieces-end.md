# O fim do Cloud Pieces — caso Pocketech / iPhix

> Documento histórico complementar ao roadmap do OntoBDC.
>
> Objetivo: registrar o encerramento do Cloud Pieces e o caso Caio Mello Franco / Pocketech / iPhix com separação entre fatos documentados, relato retrospectivo do autor e interpretação posterior.

## Contexto do produto

O **Cloud Pieces** foi concebido como uma comercialização do princípio técnico do CrudMaker: geração rápida de aplicações CRUD padronizadas, hospedadas e operadas por assinatura, com uma camada de customização contratualmente limitada.

A lógica econômica dependia da automação. O produto não foi pensado como uma software house tradicional nem como desenvolvimento integralmente sob encomenda.

Segundo relato de Elias Magalhães Júnior em 2026-08-09, a faixa comercial típica era aproximadamente:

- setup entre R$ 5 mil e R$ 10 mil;
- muitos contratos entre R$ 5 mil e R$ 7 mil de setup;
- mensalidade em torno de R$ 2 mil.

O Cloud Pieces chegou a ter aproximadamente três ou quatro clientes pagantes.

## Como funcionava a customização

Uma característica importante do Cloud Pieces é que **reuniões, backlog, sprints e trabalho de desenvolvedores não eram, por si só, indícios de que o produto havia se transformado em software sob encomenda**.

Segundo relato de Elias em 2026-08-09, o modelo funcionava da seguinte forma:

1. o CrudMaker gerava a base CRUD padronizada;
2. o cliente podia solicitar customizações dentro dos limites do plano contratado;
3. essas solicitações entravam em uma fila/backlog;
4. cada plano concedia uma franquia de horas de desenvolvimento por período/sprint;
5. a equipe consumia essas horas realizando alterações **sobre a base gerada pelo CrudMaker**;
6. a mensalidade incluía, portanto, não apenas hospedagem e operação, mas também uma quantidade limitada de evolução/customização.

Elias recorda, como ordem de grandeza, que um plano na faixa de R$ 2 mil/mês podia incluir algo próximo de **15 horas de desenvolvimento**, embora esse número ainda deva ser confirmado documentalmente.

Assim, a existência de sprints, reuniões de alinhamento, equipe, Jira, Figma e backlog era compatível com o produto Cloud Pieces. O ponto crítico não era a existência de desenvolvimento, mas **o limite desse desenvolvimento e a natureza das customizações esperadas**.

## Pocketech / iPhix

O episódio mais importante para compreender o fim do Cloud Pieces é o projeto de **Caio Mello Franco**, da **Pocketech**, relacionado ao **iPhix / InspecPRO**.

### Setembro de 2023 — o conflito de entendimento já aparece antes da execução consolidada

Em mensagens encaminhadas internamente pela Brasidata em setembro de 2023, Caio registrou dúvidas sobre a contratação e deixou explícita sua interpretação do negócio.

Ele solicitava, entre outros pontos:

- suporte a vários idiomas;
- arquitetura preparada para novas funcionalidades;
- barramento de APIs;
- importação de listas/checklists/calendários mantidos em Excel;
- previsibilidade de entregas;
- mecanismo para acompanhar produtividade e andamento.

O ponto central aparece quando Caio contesta o contrato: ele afirma que o documento tratava de contratação **SaaS**, mas que, no entendimento dele, o objeto da relação era **desenvolvimento de software**. Para ele, SaaS seria o modelo comercial que a própria Pocketech utilizaria posteriormente com seus usuários finais.

Assim, o conflito fundamental entre as partes estava documentado desde o início:

- **Cloud Pieces/Brasidata:** aplicação gerada a partir de uma base padronizada, operada como serviço, com customização limitada por franquia de desenvolvimento;
- **Caio/Pocketech:** desenvolvimento de um software específico da Pocketech.

### Interpretação retrospectiva de Elias sobre a assinatura

Em 2026-08-09, ao relembrar as mensagens de setembro de 2023, Elias acrescentou uma interpretação pessoal importante.

Para Elias, se Caio tinha uma dúvida tão fundamental sobre o objeto do contrato — SaaS/Cloud Pieces versus desenvolvimento de software sob encomenda — a decisão coerente seria **não assinar até que a divergência estivesse resolvida**.

Elias interpreta que Caio pode ter assinado mesmo discordando da natureza formal do contrato porque o preço era atraente e porque acreditava que posteriormente conseguiria pressionar a condução comercial, especialmente junto a Juliana, para obter um nível de customização maior do que o produto previa.

Essa hipótese é registrada aqui **apenas como interpretação retrospectiva de Elias**. Não há, neste momento, evidência documental suficiente para afirmar a intenção subjetiva de Caio como fato.

### 2024 — operação dentro do modelo Cloud Pieces, mas com risco de ambiguidade

Ao longo de 2024 há evidências de uma operação de desenvolvimento significativa em torno do iPhix:

- reuniões de alinhamento;
- atas formais;
- Jira;
- Figma;
- relatórios semanais;
- equipe da Brasidata;
- cronograma;
- discussão de requisitos e funcionalidades.

Esses elementos, isoladamente, **não caracterizam software sob encomenda**, porque faziam parte do funcionamento normal do Cloud Pieces: customizações eram organizadas e executadas dentro da franquia de horas de desenvolvimento associada ao plano.

Ainda assim, retrospectivamente, o formato podia contribuir para ambiguidade caso os limites da franquia, do backlog e da natureza da base padronizada não estivessem suficientemente claros ou fossem comercialmente ultrapassados.

Segundo relatos posteriores de Elias, a interface originalmente padronizada do Cloud Pieces também sofreu pressão por customização visual e funcional, inclusive com referência a telas produzidas por designer para o cliente.

O problema, portanto, não era "existir desenvolvimento", e sim **a expectativa de que o desenvolvimento limitado e incremental incluído no produto pudesse equivaler à construção irrestrita de um aplicativo inteiro sob medida**.

## Novembro de 2024 — cobrança formal de andamento

Em 12 de novembro de 2024, Caio escreveu à Brasidata dizendo que já havia aproximadamente um ano de colaboração.

No e-mail, ele se refere explicitamente ao desenvolvimento de três produtos:

- **iPhix PRO**;
- **HOME**;
- **CONNECT**.

Ele afirma que havia etapas de desenvolvimento previamente discutidas, aprovadas e transformadas em cronograma físico pela Brasidata e pede atualização do andamento.

Também solicita, caso a colaboração tivesse sido encerrada, a entrega do material produzido: telas, código frontend, código backend e demais artefatos, para permitir que outra empresa continuasse o desenvolvimento.

Esse registro demonstra que, naquele momento, a interpretação de Caio continuava sendo a de um projeto de desenvolvimento de software com entregáveis próprios.

## Janeiro de 2025 — transição técnica

Em janeiro de 2025, Caio volta a solicitar reunião para esclarecer o andamento dos três aplicativos.

Na resposta, Elias pergunta se o novo desenvolvedor contratado por Caio participaria da reunião e solicita acesso ao GitHub do cliente para enviar os códigos disponíveis.

O episódio indica que já havia um movimento de transição do desenvolvimento para outra pessoa/equipe.

## Maio de 2025 — tentativa formal de encerramento e realinhamento

Em 20 de maio de 2025, Elias envia uma comunicação formal a Caio informando que a Brasidata seguiria com o **Cloud Pieces Premium por mais três meses, sem custo adicional**, caracterizando a medida como **cortesia única e final**.

Durante esse período, as entregas seriam acompanhadas por sprints Scrum.

Para iniciar essa etapa, a Brasidata exigiu a assinatura de uma **Declaração de Entendimento do Modelo Scrum**, vinculada ao contrato original.

O movimento pode ser interpretado como uma tentativa formal de:

1. encerrar o passivo comercial;
2. explicitar novamente o modelo de trabalho;
3. criar uma janela final de entregas;
4. reduzir a ambiguidade sobre acompanhamento, escopo e processo.

Há registros posteriores de Sprint Planning em junho de 2025 e nova reunião com Caio em julho de 2025.

## Relato retrospectivo sobre o desfecho

Em conversas posteriores, Elias descreveu o caso como um dos fatores decisivos para o encerramento do Cloud Pieces.

Segundo esse relato:

- o Cloud Pieces não tinha sido concebido para software inteiramente customizado;
- o produto admitia customizações e horas de desenvolvimento, mas dentro de uma franquia e sobre a base produzida pelo CrudMaker;
- Caio passou a demandar um aplicativo completo, com muitas funcionalidades específicas;
- havia também expectativa de aderência a uma interface própria desenhada especificamente para o produto;
- essas demandas ultrapassavam, na interpretação de Elias, a fronteira entre customização do produto e desenvolvimento integral sob encomenda;
- o nível de trabalho esperado era incompatível com a precificação e com a automação que sustentavam o modelo Cloud Pieces;
- a venda inicial e a condução comercial teriam contribuído para criar expectativas acima dos limites do produto.

Elias também relatou posteriormente que, quando revisou o histórico após a saída de pessoas envolvidas na venda/operação, percebeu promessas que excediam o que o Cloud Pieces deveria oferecer.

## Análise revisada

A documentação mostra um problema estrutural mais específico do que simplesmente "produto versus software house".

1. o produto era concebido como serviço padronizado e altamente automatizado;
2. o contrato era apresentado como SaaS/Cloud Pieces;
3. o plano incluía **customização real**, organizada em backlog/sprints e limitada por uma franquia de horas;
4. o cliente declarou antes da execução que entendia estar contratando desenvolvimento de software;
5. a relação prosseguiu apesar dessa divergência fundamental;
6. o funcionamento normal do produto — reuniões, sprints, desenvolvedores e backlog — podia parecer externamente semelhante a um projeto de software tradicional;
7. o ponto de ruptura estava na fronteira entre **customização limitada da base gerada** e **construção irrestrita de um produto inteiro sob medida**.

Portanto, a existência de equipe de desenvolvimento não era uma contradição do Cloud Pieces. A vulnerabilidade estava em tornar inequívoco, comercial e operacionalmente, **o que aquelas horas compravam e o que elas não compravam**.

### Consequência econômica

A automação do CrudMaker permitia cobrar pouco porque o núcleo da aplicação era gerado e reaproveitado.

As horas de desenvolvimento eram economicamente viáveis enquanto atuavam como uma camada limitada de customização sobre essa base.

Quando a expectativa passa a incluir, de forma aberta ou cumulativa:

- UI exclusiva integral;
- novas funcionalidades em volume elevado;
- arquitetura específica;
- aplicativos ou módulos adicionais;
- evolução sem uma fronteira clara de produto;

as horas deixam de ser uma franquia de customização e começam a assumir características de um projeto sob encomenda. Nesse ponto, a estrutura de preço original deixa de se sustentar.

## Relação genealógica com o OntoBDC

O episódio pertence ao histórico do OntoBDC apenas como **contexto genealógico**, e não porque Cloud Pieces já fosse OntoBDC.

Uma interpretação posterior possível é que o caso reforça a importância de eliminar ambiguidades entre:

- descrição;
- contrato;
- estado real do sistema;
- comportamento executável;
- limites de capacidade;
- expectativa humana.

No OntoBDC, essa preocupação aparece posteriormente em mecanismos como contratos semânticos explícitos, capabilities declaradas, validação, estados verificáveis e execução determinística.

Essa relação é uma **interpretação histórica posterior**, não uma motivação documentada como consciente durante o encerramento do Cloud Pieces.

## Fontes preservadas

Entre os registros contemporâneos identificados estão:

- mensagens de setembro de 2023 encaminhadas internamente sob o assunto **"Conversa com o Caio"**;
- atas e relatórios de alinhamento iPhix de 2024;
- e-mail de Caio de 12/11/2024, **"Andamento desenvolvimento"**;
- thread de janeiro de 2025, **"Solicitação de reunião"**;
- comunicação da Brasidata de 20/05/2025, **"Assinatura da Declaração de Entendimento do Modelo Scrum – Projeto iPhix"**;
- convites e reuniões de Sprint Planning de junho/julho de 2025;
- relatos retrospectivos de Elias em conversas posteriores.

---

Este documento deve ser expandido se forem recuperados contrato, proposta comercial, tabela dos planos, quantidade exata de horas de desenvolvimento por plano, telas, atas adicionais, mensagens de venda ou outros documentos que permitam distinguir com maior precisão o escopo formal do Cloud Pieces do escopo efetivamente prometido e executado.
