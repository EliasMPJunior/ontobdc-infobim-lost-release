# OntoBDC — Roadmap Histórico

> Documento vivo de reconstrução histórica e genealógica do OntoBDC.
>
> Critério: separar explicitamente evidência documental contemporânea, relato retrospectivo do autor, continuidade conceitual provável e inferência posterior. Projetos precursores não são chamados retroativamente de OntoBDC sem evidência.

## Antes do OntoBDC

### Anos 2000 — Projeto MENTE

**Fonte:** relato direto de Elias Magalhães Júnior em 2026-08-09.

O Projeto **MENTE** (Mike Echo November Tango Echo) é um precursor na história pessoal de automação de software de Elias.

A ideia central era associar uma página a uma entidade e fazer com que essa página fosse montada/adaptada automaticamente conforme a entidade em uso. Em vez de construir uma interface fixa para cada caso, a própria definição da entidade orientava a composição da tela.

Elementos lembrados com segurança:

- havia uma entidade como referência central;
- a página se adequava à entidade corrente;
- a interface era montada de forma automatizada;
- o objetivo já era reduzir trabalho manual e repetição na construção de software.

**Classificação no roadmap:** precursor conceitual. Não há, neste registro, evidência para afirmar que o MENTE era OntoBDC ou que possuía ontologias, RDF ou qualquer uma das tecnologias que posteriormente caracterizariam o OntoBDC.

### Aproximadamente 2010–2012 — orquestrador Java EE orientado por XML

**Fonte:** relato direto de Elias Magalhães Júnior em 2026-08-09.

Entre aproximadamente 2010 e 2012, Elias desenvolveu um projeto em **Java EE** voltado à orquestração de fluxos de trabalho. O nome original do projeto não é lembrado neste momento; ele é explicitamente anterior ao **CrudMaker**.

O mecanismo central era declarativo:

1. um processo era descrito em XML;
2. esse XML definia as etapas necessárias para executar um fluxo;
3. um orquestrador lia a definição;
4. conforme a etapa corrente, o sistema montava automaticamente a tela e os elementos necessários para o trabalho daquela etapa.

Exemplo lembrado: para produzir um documento poderiam existir cinco etapas distintas. Em vez de cada uma ser codificada como uma tela fixa, as etapas eram descritas no XML e a interface correspondente era gerada/orquestrada dinamicamente.

O projeto foi desenvolvido como trabalho de conclusão de uma pós-graduação que Elias posteriormente abandonou. O projeto não prosseguiu, embora Elias tenha recebido um convite para levá-lo/desenvolvê-lo na Holanda.

**Classificação no roadmap:** precursor arquitetural forte. Já estão presentes princípios que reapareceriam muitos anos depois na trajetória do OntoBDC: descrição declarativa de comportamento, orquestração a partir de metadados/contratos, geração dinâmica de interfaces e esforço sistemático para eliminar implementação manual repetitiva.

Isso, porém, não autoriza afirmar que este sistema era uma versão inicial do OntoBDC. A continuidade deve ser tratada como genealógica e conceitual até que existam evidências adicionais.

### 2012–2020 — hiato de projetos diretamente relacionados

**Fonte:** relato direto de Elias Magalhães Júnior em 2026-08-09.

Após o projeto Java EE de aproximadamente 2010–2012, há um hiato de cerca de oito anos na linha de projetos que Elias hoje relaciona diretamente à genealogia do OntoBDC. Esse período não deve ser interpretado como ausência de experiência profissional ou automação, apenas como ausência, por enquanto, de um projeto identificado nesta linha histórica específica.

## 2020 em diante — CrudMaker e a retomada da geração declarativa

**Fonte principal:** relato direto de Elias Magalhães Júnior em 2026-08-09.

Por volta de **2020**, surge o **CrudMaker**, que Elias relaciona diretamente como ancestral da linha que posteriormente desembocaria no OntoBDC.

A característica constante do CrudMaker era a automação agressiva da produção de software: reduzir a construção repetitiva de estruturas CRUD a uma descrição mínima e uma execução automática.

### CrudMaker v1 — geração de uma entidade

A primeira versão foi implementada em **Laravel**.

O usuário informava o nome da entidade e o CrudMaker gerava automaticamente os artefatos necessários dentro do padrão adotado pela aplicação, incluindo, conforme lembrança atual:

- model;
- controller;
- request;
- response;
- demais arquivos estruturais necessários para disponibilizar o CRUD daquela entidade.

O princípio era simples: definir a entidade uma vez e eliminar a criação manual e repetitiva de todos os arquivos de infraestrutura associados.

### CrudMaker v2 — manifesto com múltiplas entidades

Na segunda versão, a unidade declarativa deixa de ser apenas uma entidade informada isoladamente e passa a existir um **manifesto**.

Nesse manifesto era possível descrever várias entidades que comporiam a aplicação. A partir dele, o CrudMaker gerava em lote os artefatos necessários para todas elas.

Essa mudança é importante na genealogia: a automação deixa de atuar apenas sobre uma unidade e começa a interpretar uma descrição mais ampla do sistema.

### CrudMaker v3 — relacionamentos entre entidades

Na terceira versão, o manifesto passa a expressar também os **relacionamentos entre as entidades**.

Com entidades e relacionamentos descritos, o CrudMaker conseguia montar automaticamente a estrutura necessária para o CRUD completo em Laravel. Na experiência relatada por Elias, o efeito prático era próximo de "dar Enter e o CRUD estar pronto".

O salto conceitual entre as versões pode ser resumido assim:

- **v1:** descrição de uma entidade -> geração de seus artefatos;
- **v2:** descrição de um conjunto de entidades -> geração de uma aplicação estruturada;
- **v3:** descrição de entidades + relações -> geração de uma estrutura de aplicação relacionalmente coerente.

**Classificação no roadmap:** ancestral técnico direto. Diferentemente dos projetos anteriores, Elias relaciona explicitamente o CrudMaker à sequência que levaria ao OntoBDC.

## Cloud Pieces — comercialização do princípio do CrudMaker

**Fontes:** relato direto de Elias Magalhães Júnior em 2026-08-09; materiais preservados no Google Drive; e-mails e comunicações contemporâneas de 2023–2025 sobre o caso Pocketech/iPhix.

O **Cloud Pieces** surge como uma **versão comercial do CrudMaker**.

A proposta não era vender desenvolvimento de software totalmente sob encomenda. O modelo era usar a capacidade de geração do CrudMaker para produzir rapidamente uma aplicação CRUD padronizada, operar essa aplicação por assinatura e permitir uma camada limitada de customização evolutiva.

### Modelo comercial e operacional

A oferta típica envolvia:

- geração inicial do sistema a partir do CrudMaker;
- hospedagem e manutenção da aplicação;
- operação contínua da infraestrutura;
- monitoramento e aspectos de segurança;
- pagamento de um setup inicial;
- assinatura mensal de baixo valor em comparação com desenvolvimento customizado tradicional;
- uma franquia limitada de horas de desenvolvimento para customizações sobre a base gerada.

Segundo relato posterior de Elias, essas customizações eram organizadas em fila/backlog e consumidas ao longo de sprints. Assim, **reuniões, backlog, sprints e desenvolvedores eram parte normal do produto**, e não evidência automática de que o Cloud Pieces tivesse se transformado em software sob encomenda.

Elias recorda, como ordem de grandeza ainda a confirmar documentalmente, que uma mensalidade na faixa de R$ 2 mil poderia incluir algo próximo de **15 horas de desenvolvimento**.

Valores lembrados por Elias:

- **setup:** aproximadamente R$ 5 mil a R$ 10 mil, com muitos casos na faixa de R$ 5 mil a R$ 7 mil;
- **mensalidade:** aproximadamente R$ 2 mil/mês.

A lógica econômica dependia diretamente da automação: como o núcleo do software era gerado e padronizado, era possível cobrar um valor significativamente menor do que um projeto de software sob medida e ainda reservar uma quantidade controlada de trabalho humano para evolução do cliente.

### O produto não era o código

O código-fonte não era o principal entregável do Cloud Pieces. O produto era a **aplicação operada como serviço**, acompanhada da infraestrutura necessária para mantê-la em funcionamento.

Segundo Elias, o cliente receberia o código principalmente em caso de saída do serviço. Enquanto permanecesse no Cloud Pieces, o valor estava no conjunto: aplicação, hospedagem, operação, manutenção, monitoramento, segurança e capacidade contratada de evolução.

### Comunidade involuntária e compartilhamento de evolução

Havia ainda uma ideia de efeito de rede operacional, descrita por Elias como uma espécie de **"comunidade involuntária"**.

Uma funcionalidade solicitada por um cliente, quando incorporada ao produto-base, tenderia a ficar disponível para os demais clientes. Se vários clientes solicitassem a mesma evolução, a intenção era que o custo em horas pudesse ser compartilhado entre eles.

Esse mecanismo permaneceu majoritariamente no nível de planejamento, porque o Cloud Pieces não alcançou escala suficiente de clientes ativos para que a dinâmica amadurecesse.

### Validação comercial

O Cloud Pieces chegou a ter aproximadamente **três ou quatro clientes pagantes**, segundo a lembrança atual. Portanto, não ficou apenas no nível de conceito ou apresentação: houve venda e uso comercial real.

Segundo Elias, os demais clientes também demonstraram dificuldades em compreender os limites do modelo, mas abandonaram antes que o conflito atingisse a escala do caso Pocketech/iPhix.

### Caso Pocketech / iPhix

O caso mais bem documentado é o da **Pocketech / iPhix**, de Caio Mello Franco. Já em setembro de 2023, antes da execução consolidada, Caio registrou por escrito que não entendia estar contratando SaaS: para ele, o objeto era **desenvolvimento de software**.

Essa divergência ocorreu apesar de o contrato ser apresentado pela Brasidata como contratação SaaS/Cloud Pieces.

Em 2026-08-09, Elias acrescentou sua interpretação retrospectiva: diante de uma divergência tão fundamental, Caio poderia simplesmente ter recusado a assinatura até que o objeto estivesse esclarecido. Elias interpreta que Caio pode ter assinado pelo preço atrativo acreditando que conseguiria posteriormente obter, por pressão comercial, um nível de customização superior ao previsto. Essa hipótese é registrada **como interpretação de Elias, não como fato comprovado sobre a intenção de Caio**.

Ao longo de 2024, a operação incluiu equipe, Jira, Figma, atas, reuniões, relatórios, cronogramas e sprints. O roadmap registra que **isso fazia parte do funcionamento normal do Cloud Pieces**, pois o produto incluía horas de customização e evolução sobre a base gerada pelo CrudMaker.

A vulnerabilidade estava em outro lugar: tornar inequívoca a fronteira entre **customização limitada por franquia de horas** e **desenvolvimento integral e irrestrito de um produto sob encomenda**.

A documentação detalhada desse episódio está em:

- [`cloud-pieces-end.md`](./cloud-pieces-end.md)

## Era das LLMs e tentativa de reinvenção do CrudMaker

**Fonte:** relato direto de Elias Magalhães Júnior em 2026-08-09.

Após o desgaste do Cloud Pieces e já durante a popularização das LLMs — inclusive no período de forte hype em torno de geração automática de software e "vibe coding" — Elias passou a considerar que a vantagem original do CrudMaker havia sido commoditizada.

A geração rápida de código, antes diferencial central, começava a parecer algo que qualquer usuário poderia obter conversando diretamente com uma LLM.

Ao mesmo tempo, a Brasidata havia sido drasticamente reduzida e Elias passou a trabalhar praticamente sozinho após a saída/demissão de membros da equipe, incluindo Juliana.

### CrudMaker v4 — conceito conversacional, não lançado

Nesse contexto surge a ideia do **CrudMaker v4**.

A proposta era permitir que o próprio usuário conversasse com o sistema em linguagem natural, de forma semelhante a uma LLM:

1. o usuário explicaria o que precisava;
2. o CrudMaker interpretaria a intenção;
3. essa intenção seria convertida para uma estrutura formal;
4. a estrutura formal alimentaria a geração da aplicação.

O objetivo não era simplesmente pedir a uma LLM que escrevesse código arbitrário, mas usá-la como **camada de interpretação entre linguagem natural e o modelo formal do CrudMaker**.

Elias realizou testes dessa abordagem. Segundo o relato, alguns testes funcionaram bem inicialmente, mas o comportamento posteriormente se tornou instável/inconsistente.

### Entrada das ontologias

A instabilidade da interpretação por LLM levou Elias a buscar um mecanismo capaz de **fixar o significado do resultado**.

A hipótese passou a ser usar **ontologias** para:

- estruturar o domínio;
- restringir e estabilizar a interpretação da linguagem natural;
- transformar a fala do usuário em uma representação formal menos ambígua;
- impedir que cada interação com a LLM produzisse uma estrutura diferente ou incoerente.

Essa investigação começou como tentativa de viabilizar o CrudMaker v4, mas o próprio v4 **nunca chegou a ser lançado**.

À medida que Elias aprofundou o estudo e o uso de ontologias, o problema deixou de ser apenas "como gerar um CRUD a partir de uma conversa" e passou a envolver representação formal de entidades, relações, regras, capacidades e comportamento.

Nesse ponto, a trajetória começa a sair do CrudMaker e a entrar no território que posteriormente se consolidaria como OntoBDC.

**Classificação no roadmap:** ponte técnica crítica. O CrudMaker v4 não deve ser registrado como produto concluído; ele é um conceito/protótipo incompleto cuja tentativa de estabilização com ontologias desencadeou uma mudança de direção arquitetural.

### Por que não simplesmente deixar o cliente conversar com uma LLM?

Retrospectivamente, Elias considera que seria preferível abandonar o modelo a repetir, com uma LLM, o mesmo problema de escopo vivido no Cloud Pieces: um usuário conversando livremente com um sistema gerador poderia continuar expandindo indefinidamente o software desejado, sem uma fronteira formal clara.

A ontologia aparece, portanto, não apenas como mecanismo de compreensão, mas como possível **limite formal entre intenção humana e execução automática**.

## Surgimento do OntoBDC

**Fonte:** relato direto de Elias em 2026-08-09, registros contemporâneos de 2025 e histórico dos repositórios OntoBDC.

O **CrudMaker v4 foi descontinuado** e o **OntoBDC entrou em seu lugar**. A transição não deve ser descrita como simples mudança de nome: o objeto técnico havia mudado. O foco deixa de ser geração de CRUD e passa a ser representação semântica formal, execução sobre essa representação, capacidades e governança de dados.

### 2025 — era conceitual e mudança de identidade

Os registros de 2025 mostram o OntoBDC ainda em intensa redefinição conceitual.

Em agosto de 2025 aparece a formulação **Ontology-Based Dynamic Coregraph**, associada à explicação de que o sistema funcionava como um motor semântico. O próprio relato contemporâneo registra que, quando as ontologias entraram, o nome passou a ser OntoBDC.

Em novembro de 2025 surge a formulação **Ontology-Based Data Choreograph** e a ideia de **Semantic Runtime**: um runtime capaz de operacionalizar ontologias existentes, ligar modelos, tarefas, documentos, sensores, validações e eventos, e tratar mudanças com rastreabilidade e versionamento.

Essa é a era em que o OntoBDC deixa definitivamente de ser uma tentativa de "CrudMaker semântico" e passa a buscar uma infraestrutura geral de execução semântica.

### Fevereiro–março de 2026 — era do runtime executável e capabilities (v0.1–v0.3)

O GitHub registra a primeira sequência consolidada de releases do runtime:

- **v0.1.0-alpha2** em 23/02/2026;
- **v0.1.0-alpha3** em 02/03/2026;
- **v0.2.0** em 06/03/2026, com evolução do CLI e carregamento de capabilities;
- **v0.3.0** em 07/03/2026, com maior flexibilidade do CLI, estratégias dinâmicas e robustez.

O núcleo dessa era é a consolidação do OntoBDC como **runtime executável orientado a capabilities**, e não apenas como modelo semântico.

### Março de 2026 — era de contexto portátil e metadados (v0.4–v0.6)

A **v0.4.1**, em 09/03/2026, introduz explicitamente **RO-Crate Integration & Enhanced Metadata Strategy**.

Na **v0.6.0**, em 13/03/2026, `init context`, RO-Crate, tooling de desenvolvimento e estabilização do test runner aparecem como elementos centrais.

É aqui que a ideia de contexto deixa de ser apenas informação auxiliar e começa a se tornar uma unidade portátil e inicializável pelo runtime.

### Março–abril de 2026 — era de checks, storage, entidades e ICDD (v0.7–v0.8)

A longa evolução da **v0.7** introduz e endurece CLI, composição de camadas e mecanismos de check.

A **v0.8.0**, em 14/04/2026, marca explicitamente:

- **Entity Framework**;
- **ISO 21597 Integration**;
- expansão da **Storage Layer**.

Esse é um salto importante: OntoBDC passa a operar não apenas ontologias e capabilities, mas entidades persistidas, storage e integração com a lógica de containers documentais/ICDD.

### Abril–maio de 2026 — checkpoint, expansão e o "Great Rollback"

Em abril há um **Checkpoint Alpha** e expansão dos objetivos da v0.9.

Em 04/05/2026 aparece no histórico o commit literalmente denominado **"The great rollback to v0.8"**.

Esse evento deve ser tratado como uma era própria de correção arquitetural: houve expansão suficiente para exigir recuo deliberado a uma base conhecida antes de continuar.

### Maio–junho de 2026 — era "Data with Brains" / containers e execução semântica (v0.9–v0.10)

A v0.9 é reconstruída após o rollback e passa por refactors importantes, incluindo A3 e checks, até ser consolidada em junho.

É nessa fase que amadurecem conceitos posteriormente descritos como:

- **Data with Brains**;
- Context Containers;
- pacote `.obdc` reunindo payload, contexto semântico e capabilities;
- execução de datasets como unidades autônomas;
- SHACL e reasoning;
- Reachability Planning;
- combinação de RO-Crate, Frictionless e ICDD.

A **v0.10** é promovida ao Core em 22/06/2026.

### Junho–julho de 2026 — era de soberania, edge/offline e Digital Briefcase

Nos documentos e discussões de junho e julho, o OntoBDC passa a ser apresentado cada vez mais como infraestrutura de **soberania de dados**, execução local e portabilidade.

Aparecem com força:

- execução offline/edge;
- `.obdc` como container semântico portátil;
- BYOS e redução de vendor lock-in;
- **Digital Briefcase / dBriefcase**;
- HTML local embarcado;
- snapshot, hash e provenance;
- separação entre TBox (`ns/`) e ABox (`nid/`).

Nessa etapa o acrônimo também aparece associado a formulações como **Ontology-Based Data Capabilities** e **Ontology-Based Datasets & Containers**, mostrando que o próprio significado nominal ainda acompanhava a evolução arquitetural.

### Julho de 2026 — era de portabilidade operacional e WorkStreams (v0.11)

A **v0.11** é promovida ao Core em 29/07/2026.

Entre os elementos característicos dessa era estão:

- instalação via ZIP;
- pasta oculta `.__ontobdc__`;
- `index.html` local;
- comandos `project` e `context`;
- geração de planilhas via command;
- **WorkStream**;
- linksets ICDD;
- integração com aplicações verticais como InfoBIM.

O OntoBDC passa a ficar utilizável como infraestrutura local concreta para projetos reais, sem depender de uma plataforma central.

### Final de julho–início de agosto de 2026 — era de conhecimento anotado e navegação semântica (v0.12)

A v0.12 começa imediatamente após a promoção da v0.11 e é implantada no Core em **04/08/2026**.

Sua marca principal é a formalização de **typed annotation contracts** e uma arquitetura de annotations mais rígida:

- categorias tipadas;
- Subjects separados de targets;
- papéis como creator, modifier, assignee, resolver e recorder;
- representação visual e geometria;
- editor genérico dirigido por categoria;
- annotation workspace;
- Subject Page com dimensões como Space, Timeline e People;
- persistência local estrita;
- remoção de fallback/migração do schema legado.

A v0.12 representa a passagem de containers apenas executáveis para containers capazes de organizar **conhecimento contextual e navegável** sobre seus próprios recursos.

### Agosto de 2026 — era de integração operacional (v0.13)

O histórico mostra que a **v0.13 foi implantada no Core em 05/08/2026**, após merges associados também ao trabalho `techcenter-labsea`.

Essa etapa é caracterizada menos por uma nova tese filosófica e mais pela aplicação integrada do runtime em cenários operacionais reais, consolidando view, storage, cronogramas, datasets, containers e integração vertical.

A classificação detalhada da v0.13 ainda deve ser refinada a partir de seus PRs e changelog, mas documentalmente ela já é uma release de produção, posterior à v0.12.

## Eras reconstruídas — resumo

Estas **não são fases oficiais definidas por Elias**; são uma reconstrução histórica baseada em mudanças observáveis de problema, arquitetura e releases:

1. **CrudMaker v4 / ontologias** — linguagem natural precisava virar estrutura formal estável;
2. **OntoBDC conceitual (2025)** — motor semântico / Dynamic Coregraph / Data Choreograph;
3. **Runtime & capabilities (v0.1–v0.3)** — execução concreta;
4. **Contexto portátil & RO-Crate (v0.4–v0.6)**;
5. **Checks, storage, entidades & ICDD (v0.7–v0.8)**;
6. **Checkpoint e Great Rollback**;
7. **Data with Brains / containers (v0.9–v0.10)**;
8. **Soberania, edge/offline & dBriefcase**;
9. **Portabilidade operacional & WorkStreams (v0.11)**;
10. **Annotations & Subject Page (v0.12)**;
11. **Integração operacional (v0.13)**.

## Leitura genealógica provisória

A sequência até este ponto revela uma continuidade mais específica do que simplesmente "gostar de automação":

1. **MENTE:** entidade -> interface adaptada automaticamente;
2. **Java EE/XML:** processo declarativo -> fluxo e interface montados automaticamente;
3. **CrudMaker v1:** entidade -> código de infraestrutura gerado;
4. **CrudMaker v2:** manifesto de entidades -> aplicação gerada;
5. **CrudMaker v3:** entidades + relações -> aplicação relacionalmente estruturada e gerada;
6. **Cloud Pieces:** o mecanismo gerador passa a sustentar um modelo comercial de software padronizado, com operação recorrente e customização limitada por capacidade contratada;
7. **CrudMaker v4 (não lançado):** linguagem natural -> tentativa de conversão para estrutura formal -> geração;
8. **entrada das ontologias:** mecanismo buscado para estabilizar a interpretação e fixar significado;
9. **OntoBDC:** a representação formal deixa de ser um meio para gerar CRUD e vira o centro do sistema — runtime, capabilities, containers, validação, contexto e conhecimento navegável.

O padrão recorrente é deslocar conhecimento que normalmente estaria espalhado em código manual para uma **descrição explícita interpretável por um motor**.

A entrada das LLMs muda o problema: gerar código deixa de ser o gargalo principal. O gargalo passa a ser **garantir significado, coerência e limites sobre aquilo que é gerado**.

É precisamente nessa mudança de problema que a genealogia deixa de ser predominantemente sobre geradores de CRUD e se torna a arquitetura semântica do OntoBDC.

## Regra de interpretação histórica

A história pessoal de Elias com automação antecede em muitos anos o nome e o código do OntoBDC. Por isso, este roadmap diferencia pelo menos quatro coisas:

- experiência e princípios pessoais de automação;
- projetos precursores independentes;
- ancestrais técnicos que Elias relaciona diretamente à linhagem posterior;
- surgimento documentado do conceito, nome, código e arquitetura formal do OntoBDC.

Essa separação evita criar uma narrativa retrospectiva artificial em que todo projeto antigo seria tratado como "OntoBDC antes de se chamar OntoBDC".

---

Documento em construção. Próximos relatos e evidências serão incorporados cronologicamente.