# Interoperabilidade de apresentação, componentes semânticos, eventos, BLE e Dock — registro da conversa

**Data:** 7 de agosto de 2026  
**Repositório:** `EliasMPJunior/ontobdc-doc`  
**Diretório:** `notes/domain-conversations/`  
**Status:** registro conceitual e transcrição da conversa  
**Ponto final deste registro:** consolidação provisória de `Tile` como unidade espacial/universal de apresentação em superfícies heterogêneas, com grid calculado pela capacidade da superfície, prioridade por recência/contexto e materialização desde relógios e displays monocromáticos até celulares, carros, desktops, TVs e videowalls.

> **Nota de fidelidade:** o trecho inicial deste documento reconstrói, com o máximo de detalhe disponível no contexto preservado da própria conversa, a sequência que antecedeu o trecho literal recuperado nesta sessão. A partir da seção **“Trecho integral da conversa atual”**, as falas foram registradas diretamente a partir do conteúdo disponível na conversa. O objetivo deste arquivo é preservar integralmente as ideias, distinções, exemplos, dúvidas, correções e decisões arquiteturais, e não produzir uma versão “limpa” ou resumida.

---

# 1. Origem da discussão: RAD, Delphi, VB6 e o incômodo com a Web moderna

A conversa começou a partir de uma comparação com ambientes RAD antigos, sobretudo Delphi/Object Pascal e VB6.

A referência principal era a experiência de construir interfaces arrastando componentes prontos, com comportamento, estado e integração de dados já encapsulados. Em Delphi, o paralelo lembrado foi a VCL e os componentes data-aware, em especial o encadeamento conceitual:

`TQuery/TTable -> TDataSource -> TDBLookupComboBox/TDBGrid`

A ideia importante não era reproduzir Delphi, mas recuperar a propriedade arquitetural de **resolver um componente uma vez e reutilizá-lo sem reimplementar HTML, CSS, JavaScript e comportamento em toda tela**.

VB6 entrou como outro exemplo da mesma época: Toolbox, componentes ActiveX/OCX, controles Data/ADO e composição visual de aplicações. A crítica era que, apesar de décadas de evolução, o desenvolvimento Web frequentemente obriga o desenvolvedor a voltar a discutir margem, padding, hover, grid, comportamento de combo, tabela, foco e JavaScript de cada tela, como se cada interface fosse inédita.

O objetivo não era nostalgia de ferramenta. O ponto era: **por que uma aplicação moderna não poderia voltar a trabalhar com unidades encapsuladas, previsíveis e reutilizáveis, mas agora em uma arquitetura muito mais interoperável?**

---

# 2. Bibliotecas e referências existentes consideradas

Foram discutidas algumas tecnologias modernas que se aproximam parcialmente daquela experiência:

- **Sencha Ext JS** como uma das aproximações mais diretas da filosofia “Delphi para Web”: suíte grande de componentes, Model, Store, Proxy, ViewModel, binding e ferramentas visuais como Sencha Architect/Rapid Ext JS;
- **OpenUI5** como ecossistema open-source com controles, models e bindings, também com uma abordagem relativamente data-aware;
- **Vaadin** como outra possibilidade de componentes ricos e abstração da camada Web;
- posteriormente, **Web Awesome** — sucessor do Shoelace — como biblioteca de Web Components reutilizáveis e self-hostable;
- **Tabulator** como componente modular para grids/tabelas de dados.

A conclusão do usuário, porém, foi explícita: **arquitetura é justamente uma de suas áreas mais fortes; não pretende copiar a arquitetura de Ext JS ou UI5**. Essas ferramentas servem como prova de que certas peças são viáveis ou como implementação concreta de baixo nível, mas não devem ditar a arquitetura do sistema.

O princípio passou a ser: bibliotecas externas podem ficar no fundo da pilha como adapters/drivers. O contrato do sistema não pode depender de Tabulator, Web Awesome, Ext JS, Flutter ou qualquer biblioteca específica.

---

# 3. A ideia central: máxima interoperabilidade de apresentação

O conceito inicialmente apareceu como “interoperabilidade visual”, mas foi refinado para **interoperabilidade de apresentação**, porque a saída pode não ser visual. A mesma resposta pode ser apresentada em HTML, Flutter, PDF, terminal, widget, totem ou voz/Alexa.

A separação central ficou assim:

- **Command** executa intenção/regra de negócio;
- o Command **não constrói uma tela**;
- o Command devolve um **Response semântico**;
- o Response descreve o que foi produzido, não como desenhar;
- um **Renderer**, injetado conforme o target de apresentação, decide como representar aquilo.

Exemplos de Responses discutidos:

- `HelpResponse`;
- `ListResponse`;
- respostas de detalhe, posteriormente tratadas conceitualmente como algo do tipo `Detail`;
- respostas de entidades ontológicas ou de registros estruturados.

A distinção que recebeu ênfase foi:

> `ListResponse` deve dizer **“isto é uma lista”**, e não **“isto é uma tabela”**.

“Lista” é semântica da resposta. “Tabela” é uma decisão de renderer.

Assim, o mesmo `ListResponse` poderia virar:

- data grid/tabela em HTML desktop;
- cards ou lista em mobile;
- lista nativa em Flutter;
- tabela paginada em PDF;
- lista textual no terminal;
- resumo ou enumeração falada em Alexa/voz;
- widget compacto em outra superfície.

Quando os dados forem ontológicos, o Response pode carregar a classe/tipo semântico das entidades. Quando não forem ontológicos, pode carregar schema/records em uma estrutura próxima a **Frictionless Data Package**, coerente com a arquitetura de dados já usada no ecossistema.

O Renderer pode receber também uma estratégia/contexto de apresentação, como HTML, PDF, Flutter, voz etc.

A proposta não foi tratada como “gerador de UI”. O conceito mais preciso passou a ser um **protocolo semântico entre intenção/dados/interação e apresentação**.

---

# 4. Renderer, capacidades e fallback

O Renderer é target-specific.

Ele traduz o Response semântico em uma representação concreta, podendo delegar a bibliotecas específicas. Um renderer HTML, por exemplo, poderia usar Tabulator para uma lista grande, sem que o Command ou o Response saibam que Tabulator existe.

Foi considerada a necessidade de **capability discovery do próprio renderer**.

Um renderer poderia declarar quais representações suporta. Se não houver uma representação equivalente, deve existir fallback semântico previsível.

Exemplos discutidos:

- um renderer de voz não tem Gantt visual;
- uma agenda/timeline pode virar descrição ou lista falada;
- um mapa pode degradar para descrição textual;
- PDF não possui o mesmo modelo de interação de uma interface HTML;
- certos eventos não fazem sentido em um renderer não interativo.

Essa capacidade de degradar sem quebrar o significado foi tratada como parte essencial da máxima interoperabilidade.

---

# 5. Componentes semânticos recorrentes

A conversa avançou para a constatação de que grande parte das interfaces empresariais repete conceitos muito semelhantes, embora cada empresa trate sua tela como algo completamente especial.

Exemplos de conceitos recorrentes:

- lista de pessoas;
- pessoas de uma empresa;
- documentos;
- atividades;
- projetos;
- cronogramas;
- detalhes de uma entidade;
- ações;
- seleção;
- estados e navegação.

A hipótese é que existe um conjunto 80/20 de **componentes semânticos** capaz de cobrir grande parte dessas aplicações.

O componente, porém, não seria apenas visual. Ele pode possuir:

- fonte de dados;
- propriedades;
- comportamento;
- estado;
- ações;
- eventos emitidos;
- eventos observados;
- regras de disponibilidade;
- apresentação/hints;
- integração com contexto.

Foi usada uma analogia com Observer: componentes poderiam reagir a eventos sem conhecer concretamente outros componentes.

Exemplo:

- um componente emite `PersonSelected`;
- um componente de detalhes observa `PersonSelected`;
- um componente de documentos também observa `PersonSelected`;
- nenhum deles conhece o outro diretamente.

---

# 6. O caso do Gantt e a separação entre conceito e representação

O usuário usou “Gantt” como exemplo de algo que deveria ser resolvido uma vez e nunca mais redesenhado manualmente.

A distinção refinada foi:

- o conceito semântico universal deveria ser algo como **Schedule/TaskTimeline**;
- **Gantt** é uma representação possível desse conceito.

Assim:

- desktop HTML pode renderizar Gantt;
- telefone pode renderizar timeline/lista;
- PDF pode renderizar tabela/diagrama;
- voz pode responder com status, próximas tarefas, atrasos etc.

Esse refinamento reforçou a regra de não colocar um detalhe de apresentação no núcleo semântico quando o objetivo é interoperabilidade máxima.

---

# 7. Experimento anterior com React Admin e ontologia

Foi lembrado um experimento já realizado com React Admin em que a interface lia uma ontologia/grafo JSON-LD e se configurava dinamicamente.

Ao alterar o grafo em runtime, a UI mudava imediatamente. Um exemplo citado foi adicionar um campo ao grafo e o campo passar a aparecer na interface sem reprogramar manualmente a tela.

O experimento impressionou quem o viu e validou o princípio, embora a implementação tenha sido considerada não profissional para servir de arquitetura definitiva.

A recomendação conceitual foi tratar esse código antigo como **arqueologia arquitetural**:

- quais metadados foram necessários para montar a interface?;
- quais exceções surgiram?;
- o que era inferível?;
- o que precisou ser explicitado?;
- onde o modelo começou a virar configuração visual específica?;
- quais propriedades poderiam formar o embrião de uma ontologia de apresentação?

---

# 8. SSE como mecanismo Web lembrado durante a discussão

Em determinado momento o usuário perguntou qual era “aquele negócio do HTML5 sem WebSocket”.

A resposta foi **Server-Sent Events — SSE**, usando `EventSource`.

A distinção registrada:

- WebSocket: comunicação bidirecional persistente;
- SSE: servidor envia eventos para o cliente sobre HTTP persistente;
- cliente pode continuar enviando ações para o servidor por HTTP/fetch/POST normal;
- SSE possui comportamento de reconexão útil para atualizações do tipo “o grafo mudou; atualize a interface”.

---

# 9. CSS, tema e independência da implementação visual

O usuário lembrou que já havia construído uma solução em que a aplicação era independente da implementação concreta de CSS: bastava trocar o arquivo CSS e, desde que as convenções de nomes fossem preservadas, as telas mudavam radicalmente.

Mesmo assim, a intenção atual não era necessariamente permitir CSS ou JavaScript arbitrário na primeira versão.

Foi sugerida uma camada de **tokens semânticos de apresentação**, em vez de deixar cada renderer receber CSS cru.

Exemplos:

- light;
- dark;
- high contrast;
- system;
- density;
- emphasis;
- variant;
- brand/profile.

O renderer HTML traduziria tokens para CSS; Flutter traduziria para `ThemeData`; PDF usaria seus próprios estilos; voz ignoraria propriedades sem significado auditivo.

A ideia era preservar identidade e consistência sem amarrar o protocolo à sintaxe de uma tecnologia específica.

---

# 10. O exemplo concreto do Button

O usuário então trouxe um componente simples para forçar a arquitetura a ficar concreta: um botão.

O botão teria:

- `label`;
- formato/aparência, por exemplo pill radius;
- ícone à esquerda;
- função/ação, como abrir uma página;
- regra para ficar enabled/disabled dependendo do tipo de componente atualmente lido/exibido na área principal;
- máquina de estados;
- estados inicialmente citados: enabled, disabled, hovered e clicked.

Foi feita uma distinção importante:

- `click` é melhor entendido como **evento/transição**, e não como estado persistente;
- `hovered` é um estado de interação específico de renderers que possuem ponteiro;
- outros estados possíveis: focused, loading, active, selected, error etc.

A estrutura conceitual do componente começou a se formar como:

- propriedades;
- appearance/presentation hints;
- disponibilidade dependente do contexto;
- máquina de estados;
- eventos;
- ações;
- data source.

Também apareceu uma fronteira arquitetural que precisa ser preservada:

- **estado semântico/de negócio** deve ser universal quando fizer sentido;
- **estado efêmero de interação** pode ser específico do renderer.

Exemplo:

- `available` ou `disabledReason` pode ter significado semântico;
- `hover` só existe em determinadas superfícies;
- Alexa não possui hover;
- `clicked` deve virar evento;
- o renderer HTML cuida de hover/focus/pressed concretos;
- Flutter usa seus equivalentes;
- voz simplesmente não possui esses estados visuais.

Da mesma maneira, um valor como “999px de border radius” é uma métrica concreta de apresentação. Para interoperabilidade máxima, o núcleo pode preferir algo como `pill`, `primary`, `compact`, deixando a métrica para o profile/theme do renderer. Ainda assim, um profile de identidade visual pode carregar métricas concretas quando o objetivo for reprodução exata.

---

# 11. Componente autocontido no HTML: Custom Elements + Shadow DOM

O usuário colocou então uma exigência forte:

> Um componente deveria poder ser colocado em **qualquer página HTML arbitrária**, com CSS externo qualquer ou sem CSS, e manter sua aparência e seu comportamento. Ainda assim, deveria aceitar temas como light, dark, high contrast e system.

A resposta foi: **Custom Elements + Shadow DOM**, isto é, Web Components.

O Shadow DOM permite encapsular:

- HTML interno;
- CSS interno;
- comportamento;
- estados de interação;
- listeners locais.

CSS externo normalmente não atravessa a shadow tree, e CSS interno não vaza para fora.

Foi feita a ressalva de que Shadow DOM não é uma cápsula absolutamente fechada:

- determinadas propriedades são herdáveis;
- CSS custom properties podem atravessar a fronteira;
- `::part` pode ser exposto deliberadamente;
- valores como fonte/cor/line-height precisam ser controlados se o objetivo for determinismo visual máximo.

Para um componente realmente autossuficiente, foi considerada a ideia de reset interno explícito, inclusive com recursos como `:host { all: initial; ... }`, tomando cuidado com propriedades customizadas e acessibilidade.

Também foram citadas possibilidades técnicas relevantes:

- `connectedCallback`;
- `attachShadow({mode: 'open'})`;
- `<style>` interno;
- `adoptedStyleSheets` / Constructable Stylesheets para compartilhar estilos com eficiência entre múltiplas instâncias;
- `:host`;
- `:host([disabled])`;
- `:focus-visible`;
- eventos customizados com `bubbles` e `composed` quando precisam atravessar o Shadow DOM.

Iframe foi lembrado como isolamento ainda mais forte, mas considerado pesado e inadequado como unidade normal de componente, por dificultar integração, layout e eventos.

O princípio resultante ficou próximo de:

> **Contrato semântico fora; implementação fechada dentro.**

E, para o objetivo temporal do usuário:

> “Resolver o botão uma vez e manter o comportamento/aparência previsível por décadas.”

---

# 12. Exigência de longevidade: abrir daqui a 50 anos com a mesma cara

O usuário explicitou que não quer uma solução “mais ou menos encapsulada”. Quer algo **amarrado**:

> daqui a 50 anos, abrir e aparecer com a mesma cara, a ponto de alguém olhar e pensar como era a criatividade visual de 50 anos antes.

Isso reforçou algumas decisões:

- reset interno deliberado;
- dependência mínima de CSS externo;
- self-hosting de recursos quando possível;
- tema como contrato controlado;
- evitar depender de frameworks de UI efêmeros no contrato;
- browser primitives e standards como base quando possível.

---

# 13. Trecho integral da conversa atual

A partir daqui, preserva-se a sequência da conversa que levou de componentes encapsulados a eventos, Event Bus, Event Bridge, BLE e à nova definição de Dock.

---

## 13.1 “O que ainda está impedindo?”

**Elias:**

> Tá, você.

**ChatGPT:**

> Tô aqui. Continua daí.

**Elias:**

> quis dizer que você falou que tá chegando perto. E aí eu quero saber o que que tá impedindo ainda.

**ChatGPT:**

> Quase nada impede tecnicamente. O que ainda separa “ideia boa” de “plataforma confiável” são alguns contratos que você precisa fechar muito bem.
>
> O principal é este: **o componente precisa saber exatamente o que é responsabilidade dele e o que é responsabilidade do renderer/contexto**. Se isso ficar borrado, em seis meses você recria CSS spaghetti só que com ontologia no meio.
>
> Os pontos críticos são:
>
> - **Contrato de propriedades**: label, icon, action, disabled rule, theme, variant, density etc. precisam ter uma forma estável e pequena.
> - **Máquina de estados**: separar estado real de evento. `hovered` pode ser estado; `click` é evento; `opening`, `loading`, `error`, `disabled` podem ser estados. Isso tem que ser formalizado.
> - **Eventos semânticos**: não ficar preso a `onclick`. O componente deveria emitir algo como `NavigateRequested`, `SelectionChanged`, `ActionTriggered`, porque isso sobrevive a HTML, Flutter, voz e PDF.
> - **Contexto externo**: o seu exemplo do botão habilitar conforme o componente principal exige uma forma padronizada de observar contexto. Ou seja, ele é encapsulado visualmente, mas não pode ser uma ilha comportamental.
> - **Temas**: light, dark, high contrast, system precisam ser tokens/roles, não CSS arbitrário. Senão o encapsulamento vira ficção.
> - **Acessibilidade**: focus, teclado, ARIA, contraste, reduced motion. Isso parece detalhe até você começar a fazer componente realmente reutilizável.
> - **Fallback entre renderers**: um renderer pode não saber representar aquele componente. Precisa existir degradação semântica previsível.
> - **Versionamento do contrato**: se um briefcase de hoje abrir daqui a cinco anos, o renderer precisa saber interpretar aquela versão da especificação.
>
> E há uma sutileza técnica no Shadow DOM: ele isola muito bem, mas não é uma cápsula termodinâmica perfeita. Algumas coisas são herdadas, como fonte e certas custom properties; e você pode deliberadamente expor partes via `::part`. Então, se você quer “mesma cara em qualquer HTML”, precisa fazer um reset interno e controlar explicitamente o que é herdável.
>
> Mas isso tudo é engenharia. Não vejo um bloqueio conceitual sério.
>
> Na verdade, depois do exemplo do botão, eu mudaria minha frase anterior: **não está “chegando perto” de ser viável. Já é viável.**
>
> O perigo agora é outro: você pode facilmente tentar definir, de uma vez, botão, tabela, Gantt, árvore, formulário, renderer HTML, Flutter, PDF, voz, eventos, temas, ontologia e máquina de estados. Aí o projeto vira uma constituição federal antes de ter um botão funcionando.
>
> Eu começaria por três componentes: **Button, List e Detail**. Um renderer HTML. Um tema. Um EventBus. E provaria o ciclo completo: Response semântica → renderer → componente encapsulado → evento → mudança de contexto → re-render.
>
> Se isso ficar limpo, o resto vira expansão.

---

## 13.2 A cobrança por menos “dourada na pílula” e a entrada definitiva em eventos

**Elias:**

> É, cara, você falou, falou e veio chegando, nem considerar, tá? Acho que você deu uma dourada na pílula aí, só acho. Tá, vamos lá. Então, eu vou fazer resetando. Eu quero um negócio amarrado. Quero que daqui a 50 anos ele abra com a mesma cara. Ele vai olhar e vai falar assim, nossa, como 50 anos atrás eles eram criativos. Não sei o quê e tal. Beleza. Aí você falou aí da parte dos eventos e tal. Bom, eu ainda não cheguei nessa parte, ainda não cheguei. Vou chegar agora. Como que resolveria essa questão de eventos? Primeiro, como que eu poderia fazer um evento no HTML que todos os componentes conseguissem ouvir e enviar? Eu teria que fazer um bus, né, dentro do navegador. E aí a segunda parte é, como que esses eventos podem ser propagados além do navegador?

**ChatGPT:**

> Sim. E dá para fazer isso quase todo em cima de primitivas nativas do navegador, sem enfiar um framework no meio.
>
> Dentro do HTML, eu faria um bus semântico central baseado em `EventTarget`, que já é API padrão do browser. Cada componente conhece apenas esse bus. Ele publica eventos e assina tipos de eventos. Um botão não conhece a tabela, a tabela não conhece o painel principal.
>
> E existe ainda uma segunda possibilidade muito útil: o próprio componente emitir `CustomEvent` pelo DOM. Com `bubbles` e `composed`, o evento consegue inclusive atravessar a fronteira do Shadow DOM. Então um botão encapsulado pode dizer algo semanticamente equivalente a “NavigationRequested”, e um listener no nível da aplicação captura isso.
>
> Eu usaria os dois papéis de forma diferente. O DOM event serve muito bem para interação imediata do componente com seu ambiente. O bus serve para os **eventos semânticos da aplicação**.
>
> A parte importante é: eu não chamaria os eventos de `onclick`, `onmouseover` etc. Isso é linguagem do renderer HTML. O componente HTML transforma essas coisas em eventos do seu protocolo.
>
> Por exemplo, o mouse clicou. Internamente isso é `click`. Externamente o componente publica algo como “ActionInvoked”, dizendo qual ação, qual componente originou, em qual contexto e com qual payload.
>
> No Flutter, não existe `click`; talvez exista `onPressed`. Mas ele publica o mesmo “ActionInvoked”.
>
> Na Alexa, o usuário fala. E pode terminar produzindo exatamente o mesmo “ActionInvoked”.
>
> Aí está a interoperabilidade.
>
> Para os eventos saírem do navegador, eu colocaria uma peça entre o bus e o mundo externo: um **Event Bridge**.
>
> O componente não sabe se existe servidor, WebSocket, SSE, Flutter, processo Python ou pombo-correio. Ele publica no bus.
>
> O bridge escuta os eventos que devem sair, serializa e transmite.
>
> E no sentido contrário, ele recebe um evento externo, desserializa e publica no bus local. Então, conceitualmente:
>
> componente → bus → bridge → transporte → mundo externo.
>
> E na volta:
>
> mundo externo → transporte → bridge → bus → componentes interessados.
>
> O transporte vira completamente substituível.
>
> Para browser falando com servidor, você tem algumas opções muito naturais.
>
> Se precisa de bidirecional realmente contínuo, WebSocket.
>
> Se o servidor principalmente empurra modificações e o navegador apenas manda ações ocasionalmente, eu gosto muito de SSE para entrada e `fetch`/POST para saída. É bem mais simples operacionalmente.
>
> Entre abas ou janelas do mesmo navegador, existe `BroadcastChannel`.
>
> Entre página e iframe ou worker, `postMessage`/`MessagePort`.
>
> Então o bridge poderia ter adapters diferentes sem mexer no protocolo de eventos.
>
> E aqui eu colocaria uma coisa desde o primeiro dia, porque depois é uma desgraça acrescentar: **um envelope padrão de evento**.
>
> Todo evento deveria carregar pelo menos uma identidade única, tipo do evento, origem, timestamp, payload, versão do contrato e talvez `correlationId` e `causationId`.
>
> Esses dois últimos parecem frescura até você querer saber:
>
> “Por que essa tela mudou?”
>
> Porque recebeu `PersonSelected`.
>
> “Quem gerou `PersonSelected`?”
>
> Foi o componente X.
>
> “E por que ele fez isso?”
>
> Porque recebeu `SearchResultActivated`.
>
> Aí você consegue reconstruir uma cadeia inteira de interação.
>
> E tem uma distinção que vale ouro: **evento não é estado**.
>
> “ButtonDisabled” pode ser um evento informando que alguma coisa aconteceu. Mas o fato de o botão estar atualmente disabled é estado.
>
> Se um componente nasceu cinco segundos depois do evento, ele não pode depender de ter ouvido algo que aconteceu antes de existir. Para isso você precisa de contexto/state store ou de eventos persistidos/replay.
>
> No seu caso, eu suspeito que isso vai acabar casando lindamente com o que você já tem de Event Sourcing: determinados eventos podem ser efêmeros, puramente de UI, e outros podem virar eventos persistentes do OntoBDC.
>
> E aí aparece uma possibilidade interessante para os briefcases: o mesmo protocolo pode trabalhar **totalmente offline**. O bus funciona localmente. Um event store pode registrar o que interessa. Quando existir conectividade, o bridge sincroniza eventos externos.
>
> Portanto, respondendo de forma seca às duas perguntas:
>
> **Sim**, dentro do navegador eu faria um semantic event bus, preferencialmente em cima de `EventTarget`/`CustomEvent`, sem dependência externa.
>
> E **sim**, para sair do navegador eu faria um bridge com adapters de transporte. SSE, WebSocket, HTTP, BroadcastChannel etc. são detalhes desse bridge. Os componentes jamais deveriam saber qual deles está sendo usado.
>
> Essa separação é importante para o seu “abrir daqui a 50 anos”: o botão pode continuar entendendo `ActionInvoked` mesmo que o mecanismo usado em 2076 para transportar esse evento não tenha absolutamente nada a ver com WebSocket.

---

## 13.3 Desafio: explicar Bus e Bridge sem código

**Elias:**

> Cara, vou te dar um desafio, tá? Vou te dar um mega desafio bizarro, que é o seguinte, me explicar essas duas formas aí do Buzz e da Bid e caralha quatro, me explicar porque eu não conheço. Então, você tem a missão de me fazer entender, sem mostrar código, né, porque eu não posso ler. Só tô aqui no Bluetooth. Então, o desafio começa em 3, 2, 1...

**ChatGPT:**

> Beleza. Vou te explicar como se estivéssemos desenhando isso no guardanapo, só falando.
>
> Tem três ideias aí, e é fácil misturar porque os nomes são parecidos: evento do DOM, Event Bus e Event Bridge.
>
> Primeiro, o evento do DOM. Imagina que cada componente está dentro de uma sala de um prédio. O botão está numa sala, a tabela em outra, o Gantt em outra. Quando o botão é clicado, ele pode simplesmente gritar para fora da sala: “fui acionado”. Esse grito vai subindo pela estrutura da página. Quem estiver acima e quiser escutar, escuta. Isso já existe nativamente no navegador. É o mesmo mecanismo que faz um clique num botão poder ser percebido pelo botão, pela div que contém o botão, pela página e assim por diante.
>
> O detalhe importante é que, mesmo com Shadow DOM, você pode permitir que determinados eventos atravessem a parede do componente. Então o botão continua encapsulado visualmente, mas consegue avisar o mundo exterior de que alguma coisa aconteceu.
>
> Isso é muito bom para coisas locais. O usuário apertou este botão, selecionou esta linha, abriu este menu. O evento naturalmente nasce naquele componente e sobe.
>
> Agora vem o Event Bus.
>
> O Bus é diferente porque ele não depende de onde o componente está na página.
>
> Pensa numa frequência de rádio interna.
>
> Todos os componentes têm acesso à mesma rádio. O botão não precisa saber onde está a tabela. Ele simplesmente transmite: “PersonSelected, pessoa 123”.
>
> Quem estiver interessado nessa frequência escuta.
>
> A tabela pode estar do outro lado da página. Um painel pode nem ser filho daquele botão. Outro componente pode ter sido criado depois. Não importa a árvore visual.
>
> Então a diferença fundamental é esta:
>
> O evento do DOM diz mais ou menos “aconteceu alguma coisa aqui”.
>
> O Event Bus diz “aconteceu alguma coisa no sistema”.
>
> Para o que você está desenhando, eu provavelmente usaria o DOM para os eventos físicos de interface e o Bus para os eventos semânticos.
>
> O mouse clicou no botão. Isso é um evento físico.
>
> O botão interpreta aquilo e publica no Bus: “NavigationRequested para página X”.
>
> A partir daquele momento acabou botão, acabou mouse, acabou HTML.
>
> No Flutter, alguém apertou um widget. Ele publica exatamente “NavigationRequested para página X”.
>
> Na Alexa, o usuário falou “abra a página X”. O sistema publica exatamente o mesmo evento.
>
> Aí entra a interoperabilidade que você quer.
>
> Agora o Bridge.
>
> O Bridge é literalmente a ponte entre essa rádio interna e o mundo exterior.
>
> Dentro do navegador, o Bus está funcionando e os componentes estão conversando.
>
> Mas imagine que alguém publica: “TaskApproved”.
>
> Talvez esse evento precise chegar ao OntoBDC rodando em Python. Ou a outro navegador. Ou a um servidor. Ou a um Flutter. Ou ser persistido.
>
> O Bridge fica escutando o Bus.
>
> Quando aparece um evento que deve sair, ele pega o evento, empacota e manda para fora.
>
> Do outro lado pode existir outro Bridge, que recebe aquilo e coloca o evento no Bus daquele ambiente.
>
> Então imagine dois computadores.
>
> No computador A, o usuário seleciona João.
>
> O componente publica “PersonSelected: João”.
>
> O Bus local recebe.
>
> O Bridge percebe que esse evento precisa ser compartilhado e manda para a rede.
>
> No computador B, o Bridge recebe.
>
> Ele joga “PersonSelected: João” no Bus local.
>
> E os componentes do computador B reagem como se o evento tivesse nascido ali.
>
> Esse é o pulo do gato.
>
> O componente não sabe que existe internet.
>
> Não sabe que existe WebSocket.
>
> Não sabe que existe SSE.
>
> Não sabe que existe Python.
>
> Não sabe nem que existe outro computador.
>
> Ele só conhece o Bus.
>
> E o Bridge não precisa conhecer botão, Gantt, tabela nem Pessoa. Ele conhece eventos e transportes.
>
> Amanhã você decide que o transporte é WebSocket. O Bridge usa WebSocket.
>
> Depois troca por SSE.
>
> Depois Bluetooth.
>
> Depois algum protocolo que inventarem em 2043.
>
> Os componentes continuam iguais.
>
> E tem uma analogia ainda melhor.
>
> O Bus é o **barramento CAN de um carro**.
>
> Cada módulo publica mensagens no barramento sem precisar ligar fio diretamente em todos os outros módulos.
>
> O Bridge é o **gateway** que pega determinadas mensagens daquele barramento e manda para outra rede.
>
> Então, resumindo em três frases:
>
> O DOM Event é o componente dizendo: “alguma coisa aconteceu comigo”.
>
> O Event Bus é o sistema dizendo: “este fato aconteceu”.
>
> O Event Bridge é dizendo: “esse fato precisa atravessar a fronteira deste sistema”.
>
> E, para o que você está imaginando, eu acho que essa distinção vai ser importantíssima. Porque você pode encapsular completamente o componente sem isolá-lo do universo.

---

## 13.4 “Me fala as tecnologias”: EventTarget, CustomEvent, BroadcastChannel e transports

**Elias:**

> Bom, eventos do DOM eu já sabia o que era. Agora, uma coisa que me ocorreu, eu sempre associei eventos do DOM a JavaScript. Mas os eventos do DOM, eles não precisam de JavaScript, né? O HTML5, eles executam por ele mesmo. Outra coisa, ok, legal tua explicação, um monte de analogia, algumas analogias baratas, mas beleza, tá valendo. Mas, cara, eu continuo sem conseguir visualizar o que que é esse bus e o que que é esse bridge, tá? Me fala as tecnologias, fala o nome da tecnologia. Ó, essa é a tecnologia tal que faz isso. Igual você começou falando do bridge, tanto que o bridge eu entendi melhor. Ah, o bridge ele entende WebSockets, ele entende o SSE, e aí ele ouve o evento do bus e interage com o mundo externo. Beleza. Inclusive essa parte aí do, ah, de ser web, ser Bluetooth e tal, é importantíssima para aquela parte dos periféricos não precisarem de internet. Então, outra coisa também que dá pra fazer interessante é imputar dado em alguma coisa e receber no outro. Por exemplo, uma Alexa que não tem TV, botar uma TVzinha do lado, aí você fala com ela aqui e ela recebe do outro lado. Mas ainda preciso entender melhor o bus e talvez também o bridge.

**ChatGPT:**

> Agora ficou claro o que estava faltando: eu estava te explicando **papéis arquiteturais**, e você queria saber **qual porra de API faz aquilo**. 😄
>
> Primeiro, uma correção importante sobre DOM Events. O navegador possui o sistema de eventos nativamente, sim. Clique, hover, foco, mudança de input etc. existem independentemente de você implementar um framework. Mas, para **reagir programaticamente** a um evento ou criar seus próprios eventos semânticos, você normalmente usa JavaScript. Um link abrir outra página sem JS é comportamento nativo do HTML; `:hover` mudar aparência é CSS. Mas “quando ocorrer PersonSelected, faça X” precisa de alguma lógica — normalmente JS. Até `onclick="..."` no HTML é JavaScript escrito dentro do atributo.
>
> Agora o **Bus**. “Event Bus” não é o nome de uma tecnologia específica; é um padrão. Mas o navegador já tem uma API perfeita para implementá-lo, chamada **EventTarget**.
>
> `EventTarget` é a mesma infraestrutura sobre a qual funcionam os eventos do DOM. Um botão é um EventTarget. A janela é um EventTarget. O documento é um EventTarget. E você também pode criar um EventTarget que não tenha absolutamente nada visual.
>
> Esse EventTarget pode ser o seu Bus.
>
> Então imagine que existe, em memória, um objeto chamado “OntoBDC Event Bus”. Ele não aparece na tela. Não é um servidor. Não é uma thread. É só um objeto mantido pelo navegador.
>
> A tabela diz a ele: “quero ser avisada sempre que ocorrer PersonSelected”.
>
> O botão ou qualquer outro componente diz: “publique PersonSelected, pessoa João”.
>
> O EventTarget pega esse evento e entrega para todos que registraram interesse em PersonSelected.
>
> As tecnologias concretas aí são **EventTarget**, `addEventListener`, `dispatchEvent` e, para eventos criados por você, **CustomEvent**.
>
> Pronto. Isso é o Bus no browser.
>
> E você poderia inclusive não criar um EventTarget novo e usar o próprio `document` como Bus. Tecnicamente funciona. Eu provavelmente criaria um separado para não misturar eventos da aplicação com a árvore DOM, mas são exatamente as mesmas primitivas.
>
> Agora existe uma segunda tecnologia parecida que você provavelmente vai gostar: **BroadcastChannel**.
>
> BroadcastChannel é um Bus fornecido pelo navegador para comunicação **entre contextos diferentes da mesma origem**. Por exemplo: duas abas, duas janelas, um iframe e potencialmente workers.
>
> Uma aba publica “PersonSelected João” no canal OntoBDC. Outra aba que esteja ouvindo aquele canal recebe.
>
> Então:
>
> EventTarget é excelente como Bus **dentro daquela aplicação**.
>
> BroadcastChannel serve como Bus **entre partes separadas do navegador**.
>
> Para comunicação com Web Workers, Service Workers, iframes e janelas, existem ainda `postMessage`, `MessageChannel` e `MessagePort`.
>
> Agora o **Bridge**.
>
> Bridge também não é uma tecnologia. É um pedaço seu de software que conecta o Event Bus a **uma tecnologia de transporte**.
>
> Ele teria um lado virado para o Bus e outro lado virado para algum driver.
>
> Por exemplo, Bridge WebSocket.
>
> Do lado interno ele escuta `PersonSelected`.
>
> Do lado externo ele possui uma conexão WebSocket.
>
> Chegou `PersonSelected` no Bus? Ele serializa e manda pelo WebSocket.
>
> Chegou uma mensagem pelo WebSocket? Ele converte aquilo novamente num evento e publica no EventTarget.
>
> Outro Bridge poderia usar **SSE**. Nesse caso, `EventSource` recebe eventos do servidor e o Bridge publica no Bus. Para mandar na direção contrária, usa HTTP normal com `fetch`.
>
> Outro Bridge poderia usar **WebRTC DataChannel**. Aí você tem comunicação peer-to-peer entre dispositivos, inclusive muito interessante para comunicação local.
>
> Outro poderia usar **Web Bluetooth**. O Bridge pega eventos do Bus e escreve numa característica BLE; quando recebe uma notificação BLE, transforma em evento OntoBDC.
>
> Também existem **Web Serial** e **WebUSB** para periféricos físicos.
>
> E aí acho que finalmente chegamos naquela ideia sua dos dispositivos sem internet.
>
> Você poderia ter, por exemplo, um tablet funcionando como display. O OntoBDC daquele tablet tem seu Bus local.
>
> Algum periférico manda uma informação por Bluetooth. O Bluetooth Bridge recebe e publica “MeasurementReceived”.
>
> Um componente na tela escuta isso e atualiza.
>
> Nenhum componente sabe o que é Bluetooth.
>
> Se amanhã aquele mesmo dado vier pela internet, você troca o Bridge Bluetooth por WebSocket e **a interface não muda uma vírgula**.
>
> E no exemplo da Alexa com uma telinha ao lado, conceitualmente seria exatamente isso. O sistema que interpreta a fala produz um evento, por exemplo “ShowSchedule”. Algum transporte leva isso para a tela. O Bridge da tela recebe, publica `ShowSchedule` no Bus local e o renderer reage.
>
> Você poderia transportar aquilo por rede local, WebSocket, WebRTC ou outra tecnologia disponível. Para o modelo semântico, tanto faz.
>
> Então grave estas duas associações:
>
> **Bus no navegador = EventTarget + CustomEvent.**
>
> **Bridge = adapter entre esse EventTarget e WebSocket, SSE/EventSource, WebRTC, Bluetooth, Serial, USB etc.**
>
> E tem um detalhe arquitetural muito bonito: `EventTarget` existe há muito tempo, é uma primitiva da plataforma Web, não uma dependência npm. Para o seu objetivo de “abrir daqui a 50 anos”, isso é uma propriedade bastante atraente.

---

## 13.5 BLE Advertising como transporte de eventos OntoBDC

**Elias:**

> final não, mas eu vou perguntar uma coisa aqui, que é mais fácil. A questão do handshake do Bluetooth, lembra? Do Nurb, Nurb device? Eu esqueci o nome dela lá. Que você falou que o Bluetooth recebe uma mensagem, você pode mandar uma mensagenzinha aqui e a máquina já recebe. Eu posso botar um evento, um evento padrão no OtoBC nessa mensagenzinha, desde que caiba, claro, e o OtoBC aplicativo ouvir isso e aplicar? Claro, eu sei que vai ter que ter uma permissão para ele ouvir isso, permissão para rodar em segundo plano, e nhenhenhém. Mas, dado que todas as permissões necessárias estão autorizadas, dá para fazer isso?

**ChatGPT:**

> Sim. **Dá para fazer exatamente isso.**
>
> E o ponto-chave é distinguir duas situações Bluetooth que a gente estava misturando um pouco antes.
>
> Se você está falando daquela “mensagenzinha” que um dispositivo BLE fica anunciando sem conexão, isso é **BLE Advertising**. O dispositivo transmite pequenos pacotes periodicamente e um celular próximo, estando em scan, consegue recebê-los sem fazer uma conexão GATT tradicional.
>
> Nesse pacote você pode colocar um **evento OntoBDC compacto**.
>
> Por exemplo, conceitualmente: versão do protocolo, tipo do evento, identificador da origem e algum valor curto. Nem precisa mandar JSON-LD ali; seria desperdício de bytes. Você cria uma codificação binária pequena e o aplicativo OntoBDC traduz aquilo para o evento semântico completo quando recebe.
>
> Algo como: “protocolo OntoBDC versão 1; evento 37; dispositivo 142; valor 3”.
>
> O app recebe e reconstrói semanticamente: “ToolEnteredArea”, “PersonDetected”, “EmergencyTriggered”, “MeasurementChanged” ou seja lá qual evento 37 representa.
>
> No BLE clássico, o advertising legado permite só **31 bytes de dados por pacote**. Bluetooth LE Extended Advertising pode transportar muito mais — até 1.650 bytes no conjunto de advertising, embora o suporte real varie entre hardware e sistemas.
>
> Para o que você está propondo, eu **preferiria deliberadamente os 31 bytes** como contrato mínimo. Se couber ali, você ganha compatibilidade com um universo gigantesco de dispositivos.
>
> E aqui aparece uma arquitetura bem bonita:
>
> O beacon ou periférico **não precisa conhecer OntoBDC inteiro**.
>
> Ele só precisa conhecer uma espécie de “wire protocol” mínimo do OntoBDC.
>
> Ele anuncia um evento.
>
> O aplicativo recebe pelo BLE Bridge.
>
> O Bridge transforma aqueles bytes num evento do Event Bus.
>
> E daí para frente todos os componentes tratam aquilo exatamente como tratariam um evento vindo de SSE, WebSocket ou do próprio usuário.
>
> Ou seja:
>
> **BLE não seria uma funcionalidade especial da aplicação. Seria só mais um transporte do protocolo de eventos.**
>
> E sim, isso permite exatamente aquelas coisas de obra que você estava imaginando outro dia: crachá entra numa região, ferramenta aparece perto de determinado receptor, equipamento muda de estado, botão físico é pressionado, sensor acusa alguma coisa. O dispositivo transmite; um telefone/tablet/gateway próximo recebe; OntoBDC reage. Sem internet.
>
> No Android atual, as APIs permitem scan, advertising e conexão BLE, com permissões específicas como `BLUETOOTH_SCAN`, `BLUETOOTH_ADVERTISE` e `BLUETOOTH_CONNECT`.
>
> E no iOS existe Core Bluetooth e suporte a determinadas operações em background, embora a Apple imponha regras próprias e seja mais restritiva.
>
> Então sua ressalva está correta: **assumindo que o sistema operacional concedeu e mantém as permissões necessárias**, tecnicamente o fluxo é perfeitamente possível.
>
> E tem uma coisa que eu faria desde já: não mandar “comandos” crus tipo “abra a tela 4”.
>
> Mandaria **eventos/fatos semânticos**.
>
> Por exemplo, não: “mostre vermelho”.
>
> Mas: “EmergencyActivated”.
>
> Não: “abra a página do João”.
>
> Mas: “PersonDetected, João”.
>
> Porque aí aquele mesmo pacote BLE pode fazer o tablet mostrar uma tela, outro dispositivo tocar um alerta, um logger registrar o fato e um gateway sincronizar depois com a nuvem.
>
> Uma única mensagenzinha de poucos bytes pode disparar comportamentos completamente diferentes dependendo de quem estiver ouvindo.
>
> Aí a ideia do Event Bridge começa a ficar bem mais poderosa do que simplesmente “conectar WebSocket”.

---

## 13.6 “Vamos começar a viagem?”

**Elias:**

> E agora estava falando sério. Vamos começar a viagem?

**ChatGPT:**

> Vamos.
>
> E agora a viagem ficou séria porque as peças começaram a se encaixar de um jeito perigoso: resposta semântica, renderer independente, componentes autocontidos, máquina de estados, eventos semânticos, bus local e bridges para Web, Bluetooth, Flutter, PDF, voz e o que mais aparecer.
>
> A partir daqui eu trataria isso como uma coisa só: **um protocolo de interação semântico independente de interface e transporte**.
>
> Ou seja, não começar pelo botão, nem pelo HTML, nem pelo BLE. Começar pelo que precisa sobreviver a todos eles.
>
> Pode mandar a próxima. Eu vou seguindo o raciocínio sem tentar fechar a arquitetura antes da hora.

---

## 13.7 Retomada da ideia antiga da Dockstation

**Elias:**

> Você lembra, lembra, lembra da ideia do Dockstation, dela responder ao celular? Aí tinha dockstation de carro, né, dockstation e tal, que trocava dados com o aparelho celular?

**ChatGPT:**

> Lembro da linha geral da ideia, mas não achei agora um registro confiável dos detalhes específicos dessa conversa.
>
> O que você está descrevendo é: uma **dockstation como dispositivo ativo**, não só suporte físico/energia. O celular encosta ou se conecta, e dock e telefone **trocam dados e eventos**. No carro, por exemplo, a dock poderia identificar o contexto “estou no veículo”, fornecer dados do carro ou do ambiente, receber estado do telefone e alterar o comportamento do aparelho.
>
> E agora, pelo caminho que a conversa tomou, já estou vendo uma conexão bem óbvia: essa dockstation poderia ser simplesmente **mais um nó falando o protocolo de eventos**, por BLE, USB, NFC ou outro bridge local. O celular encaixa, recebe um evento/contexto e passa a se comportar de acordo com aquilo.
>
> Se você estava lembrando de uma versão mais específica da ideia, manda a próxima peça que eu encaixo.

**Elias:**

> Como não schou? Olha lá no ontobdc-doc

Foi então consultado o repositório correto. A primeira busca havia sido feita no `OntoBDC/ontobdc-doc`, enquanto o registro histórico relevante estava em `EliasMPJunior/ontobdc-doc`, dentro das conversas sobre Briefcase.

O arquivo identificado foi:

`notes/domain-conversations/2026-08-02-briefcase-perspectives-transcript-continuation-01.md`

Nesse registro antigo, a Dock já aparecia com a seguinte concepção:

- a Dock não precisa carregar a identidade do usuário;
- ela oferece **corpo físico**;
- energia;
- microfone;
- alto-falante;
- eventualmente tela;
- conexão com TV, luz, carro ou ambiente;
- o celular leva a “mente”;
- a Briefcase leva memória e contexto;
- ao tirar o telefone, o usuário “vai embora dali inteiro”;
- a Dock não deve reter conta, histórico, voz, preferências e identidade do usuário.

Também estavam registrados exemplos de uso:

- sala;
- cozinha;
- carro;
- mesa de reunião;
- hotel.

No carro, o exemplo era pedir para ir a um compromisso e encontrar combustível no caminho.

No hotel, o princípio era:

- hotel fornece corpo e serviços;
- celular fornece identidade, idioma, preferências, pagamento e inteligência;
- personalização entra com o celular e sai com o celular.

A resposta após recuperar o arquivo foi:

**ChatGPT:**

> Achei. Você estava certo. Eu procurei primeiro no `OntoBDC/ontobdc-doc` público e pelo termo literal “dockstation”; o registro está no **`EliasMPJunior/ontobdc-doc`**, naquela transcrição das conversas sobre Briefcase.
>
> E a ideia era mais específica do que eu lembrei.
>
> A **dock não carrega a identidade do usuário**. Ela oferece o **corpo físico**: energia, microfone, alto-falante, eventualmente tela e conexão com TV, luzes, carro ou outros elementos do ambiente. O celular leva a “mente”; a Briefcase leva memória e contexto.
>
> Inclusive está lá o exemplo do carro: você entra e pode pedir algo como ir para o compromisso e procurar combustível no caminho. A mesma identidade/assistente que estava na sala passa a operar naquele novo corpo/contexto.
>
> E o princípio central estava escrito praticamente do jeito que você acabou de me lembrar: **quando tira o telefone, você vai embora inteiro**. A dock não fica com suas contas, histórico, preferências ou identidade. O ambiente empresta periféricos; a pessoa digital continua pertencendo ao celular/Briefcase.
>
> Também tínhamos levado isso para hotel: a dock do quarto fornece hardware e capabilities do ambiente; o celular fornece identidade, idioma, preferências, pagamento e inteligência. Quando o hóspede sai, a personalização sai junto.
>
> E agora eu entendi por que você puxou isso **justo depois de Event Bus + Bridge + BLE**.
>
> Porque o que faltava naquela discussão da dock era precisamente uma maneira elegante de fazer:
>
> **dock anuncia capabilities/eventos → bridge do celular recebe → bus OntoBDC publica → componentes/assistente reagem.**
>
> E no sentido contrário:
>
> **assistente gera intenção/evento → bus → bridge BLE/USB/Wi-Fi → dock/periférico executa.**
>
> Ou seja: a conversa de hoje acabou de fornecer uma peça arquitetural que naquela época estava descrita mais como experiência de produto. A dock pode literalmente virar **um periférico semântico OntoBDC**.

---

## 13.8 A mudança conceitual: Dock não entende o carro; Agent entende o carro

**Elias:**

> Sim. Mas ao mesmo tempo, falamos da dock enviar dados dela. Por exemplo, a do carro, enviar dados do carro. Mas agora eu penso ligeiramente different. A dock ser um conceito, físico ou digital, para armazenamento e despacho de eventos (ainda com zero inteligência). O emissor, no caso do carro, ser um Agent que troca dados com a dock

**ChatGPT:**

> Sim. E eu acho que essa versão ficou **muito mais limpa**.
>
> A Dock deixa de ser “o negócio que sabe falar com o carro”. Ela vira uma infraestrutura burra de **entrada, armazenamento temporário e despacho de eventos**.
>
> No carro, quem sabe o que é velocidade, combustível, porta aberta, ignição, CAN bus, OBD etc. é um **Agent do carro**. Esse Agent observa o veículo e transforma aquilo em eventos OntoBDC. A Dock não entende nenhum deles. Só recebe, guarda e disponibiliza.
>
> Então o fluxo seria, falando linearmente: o carro muda de estado; o Car Agent percebe; ele publica um evento na Dock; o celular chega perto ou se conecta; descobre aquela Dock; assina ou pede os eventos relevantes; a Dock entrega. No caminho contrário, o celular publica uma intenção ou evento na Dock; o Car Agent, se estiver escutando aquele tipo e estiver autorizado, recebe e age.
>
> Isso separa três coisas que antes estavam meio grudadas.
>
> O **Agent entende o domínio**.
>
> O **Bridge entende o transporte** — BLE, Wi-Fi, USB, WebSocket, mesh, seja o que for.
>
> A **Dock entende somente eventos**.
>
> E “zero inteligência” não precisa significar “zero comportamento”. A Dock ainda pode ter comportamento infraestrutural: guardar eventos por um tempo, identificar origem, manter ordem, permitir assinatura, retransmitir, confirmar recebimento, talvez replay. Mas ela não decide que “combustível baixo significa procurar posto”. Isso é Agent ou outro consumidor.
>
> Eu chamaria isso de **store-and-forward semântico**.
>
> E fica legal porque Dock deixa de ser necessariamente hardware. Uma Dock pode ser uma caixinha física no carro. Pode ser um processo rodando num computador. Pode ser um serviço local num hotel. Pode até ser um diretório/endpoint digital que funciona como caixa postal de eventos.
>
> A definição passa a ser funcional:
>
> **Dock é um ponto de encontro persistente entre Agents, onde eventos podem ser depositados e posteriormente consumidos, independentemente de os participantes estarem simultaneamente presentes.**
>
> Isso é forte pra caralho para offline.
>
> Porque o celular nem precisa estar no carro quando determinado evento nasceu. O Car Agent pode ter colocado eventos na Dock durante horas. Quando o telefone entra no carro, sincroniza o que interessa.
>
> E aí aquela ideia antiga da dock física ganha uma característica nova: ela não é mais “um periférico inteligente”. Ela pode ser literalmente o **porto local do ambiente**.
>
> O hotel tem uma Dock. O carro tem uma Dock. A mesa de reunião tem uma Dock. A casa tem uma Dock.
>
> Os Agents daqueles ambientes conversam com suas Docks.
>
> Você chega carregando sua Briefcase e seus Agents, se conecta temporariamente à Dock, troca eventos e vai embora.
>
> Acho que essa versão está conceitualmente melhor que a anterior porque **o ambiente deixa de precisar entender o usuário e o usuário deixa de precisar entender o ambiente**. Os dois lados só precisam concordar sobre eventos e capabilities.

---

# 14. Estado conceitual alcançado ao final deste registro

Sem acrescentar uma nova camada de análise além do que já foi dito na conversa, as peças que ficaram explicitamente separadas até aqui são estas.

## 14.1 Response

Objeto semântico devolvido por um Command.

Não descreve a tela concreta. Descreve o significado do resultado: lista, detalhe, ajuda, entidade, registros etc.

## 14.2 Renderer

Traduz um Response para uma superfície concreta:

- HTML;
- Flutter;
- PDF;
- terminal;
- widget;
- voz/Alexa;
- totem;
- outras superfícies futuras.

Pode usar bibliotecas específicas internamente, sem contaminar o protocolo.

## 14.3 Componente semântico

Contrato reutilizável que pode incluir:

- propriedades;
- fonte de dados;
- ação;
- estado semântico;
- regras de disponibilidade;
- eventos emitidos;
- eventos observados;
- apresentação/hints;
- integração com contexto.

Não deve confundir estado universal com estados efêmeros específicos do renderer, como hover.

## 14.4 Componente HTML concreto

Pode ser implementado como Web Component usando:

- Custom Element;
- Shadow DOM;
- CSS interno;
- reset deliberado;
- tema controlado por tokens/atributos;
- eventos próprios.

Objetivo: ser inserido em HTML arbitrário e manter aparência e comportamento previsíveis, inclusive para preservação de longo prazo.

## 14.5 DOM Event

Evento físico/local da superfície HTML:

- click;
- focus;
- input;
- pointer/mouse;
- outros.

Pode ser capturado internamente e convertido em evento semântico.

## 14.6 Event Bus

Papel arquitetural de comunicação desacoplada entre partes do sistema.

No browser, implementação natural discutida:

- `EventTarget`;
- `CustomEvent`;
- `addEventListener`;
- `dispatchEvent`.

Pode existir como objeto independente do DOM visual.

## 14.7 BroadcastChannel e mensagens locais

Para comunicação entre contextos do browser:

- `BroadcastChannel`;
- `postMessage`;
- `MessageChannel`;
- `MessagePort`;
- workers/iframes/janelas conforme o caso.

## 14.8 Event Bridge

Adapter entre o Bus e um transporte externo.

Pode implementar comunicação através de:

- WebSocket;
- SSE / `EventSource`;
- HTTP / `fetch`;
- WebRTC DataChannel;
- BLE / Web Bluetooth;
- Serial;
- USB;
- rede local;
- mesh;
- outros transportes futuros.

O componente não deve saber qual transporte está em uso.

## 14.9 Evento semântico

Não deve ser um comando visual concreto como “pinte de vermelho” ou “abra a tela 4”.

Deve representar um fato/intenção semanticamente reutilizável, por exemplo:

- `ActionInvoked`;
- `NavigationRequested`;
- `SelectionChanged`;
- `PersonSelected`;
- `PersonDetected`;
- `EmergencyActivated`;
- `MeasurementReceived`;
- `TaskApproved`;
- `ShowSchedule`.

Um envelope de evento foi considerado desejável desde o início, contendo potencialmente:

- id único;
- tipo;
- origem;
- timestamp;
- payload;
- versão do contrato;
- `correlationId`;
- `causationId`.

## 14.10 Estado e evento não são a mesma coisa

Exemplo discutido:

- `ButtonDisabled` pode informar que ocorreu uma mudança;
- “o botão está disabled” é estado atual.

Um componente criado depois do evento não pode depender de ter escutado o passado. Para isso, entram state store, contexto persistente, event store ou replay.

## 14.11 BLE Advertising

Pode transportar um wire protocol OntoBDC extremamente compacto.

A preferência discutida foi considerar **31 bytes** do advertising legado como contrato mínimo, por compatibilidade, mesmo existindo Extended Advertising maior.

O pacote pode carregar identificadores compactos que o receptor expande para um evento semântico completo.

Isso permite:

- periféricos sem internet;
- crachás;
- ferramentas;
- sensores;
- botões físicos;
- beacons;
- dispositivos locais;
- integração posterior com event bus e renderers.

BLE é tratado como **transporte**, não como feature especial do domínio.

## 14.12 Agent

É a peça que conhece o domínio.

No exemplo do carro:

- entende CAN bus/OBD ou outra fonte;
- entende velocidade, combustível, ignição, portas etc.;
- observa o domínio;
- transforma fatos em eventos OntoBDC;
- pode consumir eventos/intenções autorizados e agir no domínio.

A inteligência de domínio pertence ao Agent, não à Dock.

## 14.13 Dock — definição no ponto atual da conversa

A Dock foi redefinida.

Ela não é necessariamente uma dockstation física, nem deve saber falar especificamente com carro, hotel, TV ou usuário.

Ela pode ser **física ou digital**.

Função discutida:

- receber eventos;
- armazenar temporariamente eventos;
- manter metadados infraestruturais mínimos;
- disponibilizar eventos;
- despachar/retransmitir;
- permitir assinatura/consulta;
- eventualmente confirmar recebimento;
- eventualmente oferecer replay;
- funcionar mesmo quando produtor e consumidor não estão simultaneamente conectados.

Ela tem **zero inteligência de domínio**.

A frase funcional alcançada foi:

> **Dock é um ponto de encontro persistente entre Agents, onde eventos podem ser depositados e posteriormente consumidos, independentemente de os participantes estarem simultaneamente presentes.**

Foi sugerido o termo **store-and-forward semântico** para esse comportamento.

Exemplos possíveis mencionados:

- Dock física no carro;
- Dock em hotel;
- Dock em casa;
- Dock em mesa de reunião;
- processo local em computador;
- serviço local;
- diretório/endpoint digital equivalente a uma caixa postal de eventos.

No exemplo do carro:

1. veículo muda de estado;
2. Car Agent percebe;
3. Car Agent gera evento;
4. evento é depositado na Dock;
5. celular pode chegar depois;
6. celular/Agent assina ou solicita os eventos relevantes;
7. Dock entrega;
8. no sentido inverso, o celular deposita intenção/evento;
9. Car Agent autorizado consome e reage.

O celular não precisa estar presente no instante em que o evento nasce.

Isso reforça o uso offline e desacopla tempo, transporte e domínio.

## 14.14 Relação final entre Agent, Dock, Bridge e Bus

A separação estabelecida até este ponto é:

- **Agent entende o domínio**;
- **Dock entende eventos e persistência/encaminhamento infraestrutural**;
- **Bridge entende transporte**;
- **Bus distribui eventos no contexto local**;
- **Renderer entende apresentação**;
- **Componente entende seu contrato de interação/apresentação**;
- **Response entende o significado do resultado de um Command**.

Nenhuma dessas peças deve assumir desnecessariamente a responsabilidade da outra.

---

# 15. Continuidade com a concepção anterior da Dock

A nova definição não elimina a ideia física anterior; ela a generaliza.

Antes, a Dock havia sido imaginada principalmente como “corpo do ambiente”:

- energia;
- áudio;
- tela;
- conexão com periféricos;
- presença temporária do celular;
- identidade pertencente ao usuário;
- saída do usuário sem deixar suas contas e preferências armazenadas no ambiente.

Agora, a hipótese é que **Dock possa ser uma abstração anterior ao hardware**.

Uma dockstation física de hotel ou carro pode implementar essa abstração, mas não é a abstração em si.

A dock física pode conter ou acessar:

- storage/event queue;
- bridges locais;
- rádio BLE/Wi-Fi/USB etc.;
- interfaces com Agents do ambiente;
- periféricos de apresentação.

Mas a inteligência que interpreta “combustível baixo”, “pedido de água”, “temperatura inadequada”, “reunião começando” etc. deve pertencer aos Agents/capabilities correspondentes.

---

# 16. Princípios arquiteturais que atravessaram toda a conversa

Os seguintes princípios apareceram repetidamente e não devem se perder em implementações futuras:

1. **Não amarrar semântica à apresentação concreta.** `List` não significa `table`; `Schedule` não significa necessariamente `Gantt`.
2. **Não amarrar evento semântico a evento físico de UI.** `ActionInvoked` não significa `click`.
3. **Não amarrar protocolo a transporte.** Um mesmo evento pode atravessar WebSocket, SSE, BLE, USB, WebRTC, mesh ou algo ainda inexistente.
4. **Não amarrar componente ao CSS da página hospedeira.** Web Component/Shadow DOM é a abordagem HTML considerada para encapsulamento forte.
5. **Não amarrar identidade ao ambiente.** O ambiente oferece capacidades; identidade/contexto permanecem com o usuário/Briefcase.
6. **Não colocar inteligência de domínio na Dock.** Agent conhece o carro, hotel, sensor, ferramenta, pessoa ou serviço.
7. **Não exigir simultaneidade entre produtor e consumidor.** A Dock pode armazenar e encaminhar depois.
8. **Preservar operação offline como propriedade fundamental, não exceção.**
9. **Preferir primitives e standards duráveis quando o objetivo é longevidade.**
10. **Projetar para degradação/fallback entre superfícies diferentes.**
11. **Separar estado de evento.**
12. **Separar estado semântico de estado efêmero de interação.**
13. **Permitir bibliotecas de terceiros somente como detalhes substituíveis de renderer/adapter.**
14. **Manter o contrato pequeno, explícito e versionável.**
15. **A meta declarada é longevidade extrema:** um artefato deve poder ser reaberto décadas depois mantendo significado e, quando necessário, identidade visual previsível.

---

# 17. Ponto exato onde a conversa foi interrompida para o primeiro registro

O último conceito discutido antes do primeiro pedido de gravação foi:

> A **Dock** pode ser um conceito físico ou digital para **armazenamento e despacho de eventos**, ainda com **zero inteligência**; no caso do carro, quem emite e interpreta dados do veículo é um **Agent**, que troca eventos com a Dock.

E a decomposição correspondente ficou:

> **Agent = domínio**  
> **Dock = store-and-forward de eventos**  
> **Bridge = transporte**  
> **Bus = distribuição local**

A conversa continuou imediatamente depois desse ponto, e as seções seguintes registram a evolução posterior.

---

# 18. A grande revelação seguinte: o navegador como dDock

A conversa prosseguiu com a inversão conceitual de que **o navegador pode assumir o papel de uma Dock digital — uma dDock**.

A formulação foi refinada para evitar confundir o host com a abstração:

- `dDock` é um **papel/runtime**;
- o navegador é um **host capaz de executar esse papel**;
- o mesmo host pode, simultaneamente, executar Agents, Renderer HTML, Web Components e Bridges;
- a dDock em si continua sem inteligência de domínio.

O navegador já fornece várias primitivas compatíveis com esse papel:

- `EventTarget` para distribuição local;
- `BroadcastChannel` para comunicação entre contextos;
- `MessageChannel` / `MessagePort`;
- `IndexedDB` para persistência;
- Service Workers e Web Workers;
- SSE / WebSocket;
- WebRTC;
- Web Bluetooth;
- WebUSB;
- Web Serial.

Isso levou a uma distinção importante:

- **Bus** = distribuição local, normalmente efêmera e em processo;
- **dDock** = fronteira persistente/assíncrona de store-and-forward entre Agents/contextos;
- **Bridge** = adaptação para um transporte concreto;
- **Agent** = participante que interpreta domínio e produz/consome eventos semânticos.

O navegador, portanto, deixou de ser visto apenas como “a coisa que desenha HTML” e passou a ser considerado um possível **porto digital/runtime de interação**.

---

# 19. Inversão da apresentação: a tela como Scene / Presentation Surface

A próxima ideia foi inverter o modelo tradicional de UI.

Em vez de o desenvolvedor construir antecipadamente uma página, colocar componentes em posições fixas e fazer esses componentes buscarem dados, a proposta passou a ser considerar a tela como uma **superfície vazia que é montada em runtime por eventos**.

Os nomes usados na discussão foram:

- **scene / scene graph** para o estado visual composto;
- **Presentation Surface** para a superfície de apresentação em si.

A analogia feita pelo usuário foi “praticamente como um jogo”.

Um evento de apresentação poderia solicitar, por exemplo:

- materialize uma ação/componente;
- tente posicioná-lo em determinada região;
- informe a posição efetivamente obtida;
- informe o espaço ocupado;
- informe quais regiões continuam disponíveis;
- informe configuração/capacidades da superfície.

A responsabilidade precisa continuar separada:

- a **dDock não monta interface**;
- um **Presentation Agent / Renderer** observa os eventos e materializa a representação concreta;
- o **browser** executa o layout real;
- a geometria resultante pode ser medida e devolvida como novo evento.

Assim, o browser funciona como um **layout/scene engine real**, em vez de se tentar escrever do zero um motor geométrico paralelo.

A geometria concreta pode incluir:

- `x`;
- `y`;
- largura;
- altura;
- regiões disponíveis;
- scroll;
- visibilidade;
- colisões/restrições quando necessário.

A ideia de “espaço restante” foi refinada: não deveria ser apenas uma porcentagem, mas um conjunto de **regiões geométricas utilizáveis**.

---

# 20. A2UI e AG-UI: pesquisa, utilidade e correção de escopo

Durante a investigação apareceram dois projetos contemporâneos relevantes:

- **A2UI**, voltado a descrições declarativas de UI e renderização por catálogo;
- **AG-UI**, protocolo de eventos/comunicação para aplicações com Agents.

Num primeiro momento, a aderência deles à arquitetura em discussão foi **superestimada**. A conversa posteriormente corrigiu isso de maneira explícita.

A distinção final foi:

- A2UI pode ser útil como referência ou peça de **Presentation IR / catálogo / renderer**;
- AG-UI pode ser útil como protocolo de integração em aplicações com agentes de IA;
- **nenhum dos dois entrega a arquitetura inteira discutida aqui**;
- nenhum deles fornece, por si só, a dDock física/digital, store-and-forward universal, BLE/USB/mesh, Briefcase, persistência/replay, negociação geométrica ou a semântica geral dos Agents determinísticos.

Mais importante: **A2UI não resolve automaticamente o requisito de encapsulamento visual determinístico**.

A2UI descreve um componente como `Button`, consulta um catálogo e materializa uma implementação concreta. O CSS e o comportamento pertencem à implementação do renderer/catalog. Isso é diferente de garantir que uma peça possa ser jogada em uma página arbitrária e manter exatamente a mesma aparência independentemente do CSS hospedeiro.

A correção arquitetural registrada foi:

> A2UI se aproxima de parte da ideia no nível de protocolo declarativo e catálogo. O requisito de componente visual fechado e invariável precisa ser resolvido pela implementação concreta — por exemplo, Web Components + Shadow DOM — e não é uma propriedade automática do A2UI.

Essa correção levou à decisão informal expressa em francês, em referência a Édith Piaf:

> **Je repars à zéro. Je ne regrette rien.**

Ou seja: construir a arquitetura própria, usando bibliotecas externas apenas quando realmente forem úteis como implementação periférica.

---

# 21. Mecânica real observada no A2UI

Para eliminar abstrações vagas, foi inspecionado o funcionamento concreto do renderer Lit do A2UI.

O fluxo observado foi:

1. a descrição cria um `componentModel.type`, por exemplo `Button`;
2. o renderer consulta o catálogo (`catalog.components.get(type)`);
3. a implementação registrada informa uma tag concreta, como `a2ui-basic-button`;
4. Lit cria esse Custom Element;
5. a implementação do botão produz um `<button>` nativo;
6. o CSS vem dos `static styles` do componente Lit;
7. propriedades de tema podem entrar por CSS custom properties;
8. a ação declarada é transformada em função pelo binder;
9. click DOM chama a ação;
10. a ação percorre `ComponentContext` / `SurfaceModel` e chega ao callback público de ação.

Isso confirmou que o JSON não “vira botão magicamente”. Existe um runtime, um catálogo e uma implementação concreta carregados no cliente.

Também confirmou que o sample oficial de desenvolvimento depende de packages/build tooling. Isso não significa que o usuário final precise de npm: apenas significa que a distribuição standalone precisa ser preparada deliberadamente.

---

# 22. npm, bundle e a exigência de Briefcase standalone

Houve preocupação explícita de que cada Briefcase pudesse acabar carregando ou instalando `node_modules`.

A distinção ficou:

- npm/Node podem existir **somente no ambiente de desenvolvimento/build**;
- dependências podem ser compiladas/bundladas uma vez;
- o artefato final pode carregar apenas `index.html` e um ou poucos runtimes JavaScript congelados;
- o usuário final não precisa instalar npm nem manter `node_modules`.

Para longevidade extrema, a direção considerada mais segura é:

- vendor/freeze de runtime versionado;
- evitar CDN obrigatória;
- recursos necessários carregados junto do artefato;
- minimizar dependências cujo comportamento possa desaparecer.

Ao discutir CSS próprio dentro de bundles, também ficou registrado que CSS global no `<head>` **não penetra automaticamente Shadow DOM**.

Duas estratégias foram separadas:

- **theming por tokens/custom properties** quando se quer variar apenas parâmetros expostos;
- **componente próprio encapsulado** quando se quer identidade visual totalmente controlada.

---

# 23. Prova prática: botão InfoBIM totalmente encapsulado

A discussão chegou então ao requisito concreto, sem ambiguidade:

> colocar um botão em uma página branca sem CSS ou em uma página cheia de CSS arbitrário e ele continuar com a mesma aparência.

Foi montado um HTML único, dependency-free, com um Custom Element do InfoBIM usando:

- `Custom Element`;
- `Shadow DOM` em modo fechado;
- HTML interno;
- CSS interno;
- comportamento interno;
- emissão de `CustomEvent` para o exterior.

O componente de uso externo ficou conceitualmente simples:

`<infobim-button action="openProject">Abrir projeto</infobim-button>`

A aparência foi derivada do botão principal do site InfoBIM: pill, gradiente ciano, borda, sombra e tipografia forte.

O teste funcionou na prática. Isso foi tratado como uma validação importante porque provou que **não era necessário A2UI, Lit, React, npm ou framework algum para obter a propriedade essencial de encapsulamento visual**.

O HTML de prova foi salvo também no repositório:

- repositório: `EliasMPJunior/my-desktop`;
- arquivo: `infobim-encapsulated-button.html`;
- branch: `master`;
- commit: `d34c543825339b487b051f401638b0902b2ff9c3`.

A conclusão operacional desse experimento foi:

> **um componente visual pode ser uma unidade autossuficiente, portátil e visualmente determinística dentro de uma página arbitrária, usando somente primitivas nativas da Web.**

---

# 24. Ressurreição dos Live Tiles do Windows 8 / Windows Phone

Depois da prova do botão, surgiu deliberadamente outra referência histórica: **Live Tiles**, especialmente do Windows 8 e Windows Phone.

A característica valorizada não é apenas estética. O Live Tile ocupava um espaço intermediário entre:

- ícone;
- botão;
- widget;
- representação viva de informação.

Um Tile podia mostrar:

- texto;
- imagem;
- animação;
- contador;
- estado;
- previsão do tempo;
- conteúdo atualizado.

A propriedade considerada especialmente útil para a arquitetura atual é que **Tiles se encaixam naturalmente em superfícies e tamanhos de tela diferentes**.

O conceito deixa de ser “uma aplicação tem um ícone” e passa a permitir que entidades, informações e ações tenham **representações espaciais vivas**.

---

# 25. Tile como unidade espacial baseada em grid

A ideia foi refinada com um grid abstrato, independente de pixels.

Exemplo hipotético citado para um telefone:

- largura lógica: `8` unidades;
- altura lógica: `16` unidades.

Os Tiles ocupam células ou múltiplos de células dessa superfície.

A representação depende do espaço disponível.

Exemplos conceituais discutidos:

- `1×1`: pode ser um ícone, botão, contador, temperatura ou qualquer informação que caiba em uma unidade;
- um Tile em forma de “tripa”/linha pode funcionar como widget compacto horizontal;
- formatos mais largos podem mostrar mais informação;
- formatos quadrados maiores podem começar a expor dados ricos;
- um Tile pode chegar a ocupar a superfície inteira.

Importante: **1×1 não significa necessariamente botão**. Pode ser puramente informativo ou informativo-interativo.

A decisão de modelagem ainda precisa ser formalizada entre duas alternativas próximas:

1. considerar cada tamanho/representação como um tipo distinto de Tile; ou
2. considerar um mesmo Tile com múltiplos modos de representação conforme o espaço recebido.

O ponto já estabelecido é que **o tamanho disponível participa da escolha da representação**, sem exigir uma página diferente para cada dispositivo.

Isso sugere uma abstração muito mais estável que pixels fixos: a superfície oferece uma capacidade espacial lógica, e os Tiles declaram/negociam dimensões ou perfis compatíveis.

---

# 26. Component versus Tile

A conversa separou duas granularidades que não devem ser misturadas:

- **Component** = unidade interna de UI, encapsulada, responsável por uma peça concreta de interação/apresentação;
- **Tile** = unidade espacial que a Presentation Surface organiza.

Um Tile pode:

- conter um único Component;
- conter vários Components;
- ser puramente informativo;
- ser interativo;
- ter representação compacta ou rica;
- responder a eventos sem que a superfície conheça sua implementação interna.

O Tile, portanto, não precisa expor seu CSS nem seu DOM para o layout geral. A superfície precisa conhecer principalmente:

- identidade;
- tamanho lógico;
- constraints;
- posição;
- prioridade/recência;
- estado de materialização;
- eventos relevantes;
- eventualmente capabilities espaciais.

---

# 27. A Presentation Surface começa vazia e é construída pelo uso

A UX imaginada não é a de um usuário montando manualmente um dashboard arrastando widgets.

A superfície começa essencialmente vazia:

- fundo branco em modo claro;
- fundo preto/escuro em modo escuro;
- algum ponto inicial mínimo para iniciar navegação/interação.

À medida que o usuário **usa a informação**, Tiles vão sendo materializados.

O comportamento sugerido é temporal/contextual:

- Tiles novos ou recém-acessados aparecem na região prioritária;
- Tiles antigos são empurrados para baixo / regiões menos prioritárias;
- ao reacessar algo, seu Tile volta a ganhar prioridade e sobe;
- com o tempo, a superfície passa a refletir a maneira real como aquele usuário trabalha naquele contexto.

Isso transforma a UI de algo previamente desenhado em uma **memória espacial de interação**.

A organização automática ainda precisa de regras explícitas para evitar instabilidade visual excessiva, mas a intenção conceitual está clara: **a tela é formada progressivamente pelo uso, não entregue pronta como uma página fixa**.

---

# 28. Contextos persistidos de apresentação

Depois de algum tempo de uso, a superfície pode ser persistida como um **contexto**.

Exemplos mencionados:

- contexto de obra;
- outro contexto de trabalho;
- qualquer conjunto recorrente de informações e Tiles.

Persistir um contexto pode envolver:

- conjunto de Tiles ativos;
- ordem/prioridade;
- dimensões;
- estado semântico necessário para reconstrução;
- filtros/seleções relevantes;
- vínculos com as entidades que originaram os Tiles.

Posteriormente o usuário pode solicitar a retomada daquele contexto e a Presentation Surface é reconstruída.

Isso aproxima a ideia de um workspace recuperável, mas sem obrigar a existência de “aplicações” ou “páginas” tradicionais.

---

# 29. LLM como mais uma fonte de intenção, não como fundamento da UI

Foi imaginada uma barra de busca/entrada, possivelmente no rodapé, com texto e voz.

Exemplo:

> “me mostra minhas tarefas de hoje”

A LLM interpreta essa entrada e produz uma intenção que materializa o Tile correspondente.

A LLM não precisa possuir a arquitetura de apresentação. Ela funciona como **mais uma forma de gerar intenção/eventos**.

Isso preserva a arquitetura mesmo sem IA:

- clique pode produzir intenção;
- voz pode produzir intenção;
- LLM pode produzir intenção;
- horário pode produzir intenção;
- localização pode produzir intenção;
- uma Dock pode produzir intenção/contexto.

O resultado pode convergir para o mesmo mecanismo de Tiles.

---

# 30. Tiles acionados por tempo, posição, proximidade e Dock

Além do uso interativo, Tiles podem ser materializados ou reorganizados por eventos contextuais.

Exemplos explicitamente mencionados:

- **tempo:** “todo dia às 10h coloque minhas tarefas”;
- **posição/localização:** ao chegar a determinado lugar, reorganizar ou apresentar Tiles pertinentes;
- **Dock:** ao colocar o celular em determinada Dock/dDock, mudar a composição da superfície;
- outros eventos do protocolo podem produzir o mesmo efeito.

A consequência importante é que **a mesma Presentation Surface pode reagir ao contexto físico e digital sem incorporar a lógica de cada transporte**.

Localização, BLE, Dock, agenda ou LLM são fontes diferentes de eventos/intenção; o mecanismo de apresentação permanece o mesmo.

---

# 31. Estado conceitual atualizado

Depois desta continuação, a arquitetura de apresentação pode ser descrita, provisoriamente, pelas seguintes responsabilidades:

- **Domain/Command** produz significado e intenção;
- **Response** representa resultado semântico quando aplicável;
- **Agent** conhece um domínio e produz/consome eventos;
- **Bus** distribui eventos localmente;
- **Bridge** adapta transporte;
- **Dock/dDock** recebe, persiste e despacha eventos sem inteligência de domínio;
- **Presentation Agent / Renderer** interpreta eventos/intenção de apresentação;
- **Presentation Surface** é a superfície/scene onde representações são materializadas;
- **Tile** é a unidade espacial da superfície;
- **Component** é a unidade interna encapsulada de UI;
- **browser** pode hospedar simultaneamente dDock, Agents, Renderer, Surface e Components, sem que esses papéis se confundam.

Uma sequência possível é:

`evento/intenção -> dDock/Bus -> Presentation Agent -> escolha/materialização de Tile -> Web Component encapsulado -> layout real do browser -> geometria/estado -> novo evento`

O fluxo também pode começar por evento de tempo, posição, BLE, outra Dock, voz ou LLM.

---

# 32. Princípios adicionais preservados nesta continuação

Além dos princípios da seção 16, esta etapa acrescentou pontos que devem ser lembrados em futuras implementações:

1. **O navegador pode ser runtime, não apenas tela.** Ele pode hospedar a dDock e os demais papéis, mas isso não transforma a dDock em renderer.
2. **A Presentation Surface pode começar vazia e ser construída por eventos.** Não é obrigatório existir uma página pré-combinada.
3. **Usar o layout engine do browser.** Medir a geometria real é preferível a recriar um motor de layout paralelo sem necessidade.
4. **Tile é unidade espacial; Component é unidade interna de UI.**
5. **Tamanho lógico deve influenciar representação.** Um Tile 1×1 pode ser tão válido quanto um Tile full-screen.
6. **Grid lógico ajuda portabilidade entre telas.** A superfície pode ser descrita em unidades, não em pixels absolutos.
7. **A superfície pode se auto-organizar pelo uso**, desde que regras de estabilidade sejam posteriormente definidas.
8. **Contextos de apresentação devem poder ser persistidos e retomados.**
9. **LLM é um produtor de intenção, não o núcleo arquitetural.** O sistema deve funcionar sem ela.
10. **Tempo, localização, BLE e Dock são gatilhos equivalentes do ponto de vista da apresentação.**
11. **A2UI/AG-UI são referências/adapters possíveis, não fundações obrigatórias.**
12. **O encapsulamento visual foi validado na prática com Web Components + Shadow DOM, sem framework.**
13. **A aparência fixa pertence ao componente concreto.** Protocolos declarativos por si só não garantem determinismo visual.
14. **Construir do zero o contrato não significa reinventar primitives da Web.** EventTarget, CustomEvent, Shadow DOM, Custom Elements, IndexedDB e demais standards continuam sendo blocos fundamentais.

---

# 33. Ponto da conversa após a primeira expansão de Tiles

O conceito naquele ponto era uma **Presentation Surface contextual de Tiles**, inspirada deliberadamente nos Live Tiles do Windows 8/Windows Phone, mas sem ficar presa ao modelo de aplicativos daquela plataforma.

A superfície:

- pode ser expressa como grid lógico apropriado ao dispositivo;
- começa vazia;
- recebe Tiles conforme o usuário pede ou acessa informação;
- reorganiza prioridade conforme uso/recência;
- pode reagir a gatilhos de tempo, posição e Dock;
- pode receber intenções por clique, voz ou LLM;
- pode ser persistida como contexto e retomada posteriormente.

O Tile:

- pode ser minúsculo (`1×1`) e mostrar apenas um ícone, número ou estado;
- pode assumir formatos horizontais/verticais compactos;
- pode mostrar dados mais ricos conforme cresce;
- pode chegar a ocupar a superfície inteira;
- pode ser informativo, interativo ou ambos;
- encapsula ou contém Components, mas não é sinônimo deles.

A questão ainda aberta era como formalizar **representações por tamanho**: múltiplos tipos de Tile versus um Tile com múltiplos modos/capabilities de representação.

O ponto central já estava estabelecido:

> **a interface deixa de ser uma coleção de páginas pré-construídas e passa a poder emergir, em runtime, como uma superfície contextual de unidades vivas de informação.**

---

# 34. Recência deixa de ser ordenação e passa a ser navegação

A discussão seguinte corrigiu uma preocupação levantada com “memória espacial”. O usuário observou que, se Tiles novos ou recém-acessados não subirem, eles necessariamente aparecerão abaixo do conteúdo anterior e o usuário terá de rolar para encontrá-los. Como a proposta é justamente **não navegar por páginas fixas nem ficar abrindo e fechando telas**, colocar o que está ativo no topo não é apenas uma preferência de ordenação: é parte do mecanismo de navegação.

O modelo passa a ser aproximadamente um **working set visual ordenado por último acesso**:

- ao materializar informação nova, seu Tile entra na região prioritária;
- ao acessar um Tile antigo, ele volta para cima;
- os Tiles anteriormente ativos descem;
- rolar para baixo permite reencontrar aquilo que foi visto pouco antes;
- a própria superfície mantém o passado recente visível, sem exigir um comando `Back` tradicional.

Isso ataca uma limitação comum de navegação por páginas: depois de abrir A, depois B, voltar, abrir C etc., o usuário perde facilmente o caminho para um estado anterior. Na Surface, o histórico operacional recente continua fisicamente presente abaixo.

A formulação que emergiu foi:

> **topo = agora; abaixo = recentemente; mais abaixo = passado ainda acessível.**

A preocupação com memória espacial continua válida para elementos deliberadamente fixos, mas perde força como objeção geral, pois nessa arquitetura **a recência é a própria navegação temporal da superfície**.

---

# 35. Pinning e compactação como exceções controladas

A ideia de **pinning** foi mantida como recurso útil, mas com uma ressalva prática: em telas pequenas, sobretudo celulares, cada Tile fixado consome espaço muito escasso.

Portanto, `pin` não precisa significar “preserve eternamente este retângulo grande nesta coordenada”. Pode significar algo mais abstrato:

- manter o Tile no conjunto prioritário;
- impedir que ele seja descartado/arquivado por envelhecimento;
- permitir uma representação compacta quando o espaço for pequeno;
- expandi-lo novamente quando for acionado.

Também foi discutida como hipótese a possibilidade de **densidade adaptativa pelo envelhecimento**:

- Tile recém-acessado pode aparecer em representação rica;
- ao perder prioridade, pode assumir representação menor;
- ao ser reacessado, volta a ganhar prioridade e pode expandir novamente.

Exemplo conceitual: um Tile de tarefas que em destaque ocupa uma região grande poderia, com o tempo, virar uma faixa compacta e depois uma representação mínima, mantendo sua identidade.

Essa compactação ainda não foi adotada como regra definitiva; foi registrada como mecanismo possível para reduzir scroll e preservar histórico sem ocupar indefinidamente grandes áreas.

---

# 36. Benchmarking: sistemas que possuem pedaços do paradigma

A ideia foi comparada com interfaces e pesquisas anteriores, não para copiar arquitetura, mas como benchmarking.

## 36.1 Windows Phone / Windows 8 Live Tiles

É a referência visual mais direta:

- Tiles em tamanhos diferentes;
- conteúdo vivo;
- texto, imagem, contadores, clima etc.;
- representação mais rica que um ícone.

Diferença principal: eram essencialmente extensões/apresentações de aplicativos e ficavam onde o usuário os organizava. Não formavam automaticamente um fluxo temporal por último acesso.

## 36.2 Android Widgets

É uma referência forte para o **modelo de grid/células**:

- widgets ocupam múltiplos de células;
- podem declarar dimensões mínimas e alvos;
- podem escolher layouts diferentes conforme o espaço recebido;
- o launcher conhece a área concreta e resolve o tamanho final.

Isso se aproxima bastante da ideia de um Tile cuja representação muda conforme a capacidade espacial disponível.

## 36.3 Apple Smart Stack

É referência para **relevância contextual**:

- widgets podem subir/ser apresentados conforme horário, contexto e padrões de uso;
- o sistema tenta colocar informação pertinente na frente.

Diferença: os widgets compartilham essencialmente um mesmo slot/stack, em vez de formar uma superfície histórica contínua de Tiles.

## 36.4 Lifestreams, Yale, década de 1990

Foi o benchmark conceitualmente mais próximo da ideia de **recência como navegação**.

Lifestreams propunha substituir o desktop tradicional por um fluxo cronológico:

- novos itens entram no presente;
- o passado fica atrás/abaixo no stream;
- o usuário percorre o fluxo para recuperar informação anterior;
- existiam mecanismos de sumarização/compactação de grandes volumes.

A semelhança importante é que o histórico deixa de estar escondido atrás de uma pilha de páginas e passa a fazer parte da própria organização espacial/temporal da interface.

## 36.5 Windows Timeline

Oferecia recuperação visual de atividades anteriores, arquivos e sites. É referência para retomada de atividade, mas como uma **tela de histórico separada**, não como o workspace principal que está sendo continuamente reorganizado.

## 36.6 Giornata / activity-based computing

É referência para **contexto de atividade** como unidade de organização. A ideia de reunir recursos e estado em torno de uma atividade se aproxima dos contextos persistidos da Presentation Surface.

## 36.7 Combinação específica

Não foi identificado, durante o benchmarking, um paradigma consolidado que reúna simultaneamente:

- Tiles vivos e redimensionáveis;
- adaptação de conteúdo ao tamanho;
- superfície contínua única;
- ordenação por recência/último acesso como navegação;
- materialização automática por eventos/contexto;
- persistência/restauração de contextos;
- independência de aplicativo;
- mesma abstração em displays drasticamente diferentes.

Cada referência resolve uma parte. A combinação permanece específica desta linha arquitetural em discussão.

---

# 37. A Surface não precisa herdar o “chrome” de um sistema operacional ou site

Ao observar imagens do Windows Phone, apareceu outra diferença importante.

O Windows Phone precisava funcionar como **sistema operacional generalista**. Sua Start Screen tinha de acomodar ações e aplicativos estruturalmente esperados:

- telefone;
- SMS/mensagens;
- câmera;
- contatos;
- configurações;
- loja;
- launcher de aplicativos etc.

A Presentation Surface em discussão não possui essa obrigação.

Da mesma forma, por não ser concebida como um site tradicional, ela não precisa reservar espaço por padrão para:

- menu principal;
- sidebar;
- breadcrumb;
- barra institucional;
- hierarquia permanente de páginas;
- botão Home;
- launcher de aplicações.

Quase toda a superfície pode ser dedicada ao **conteúdo contextual materializado como Tiles**.

Controles universais ainda podem existir, mas de forma mínima — por exemplo:

- busca/voz;
- troca de contexto;
- configurações;
- algum mecanismo inicial para começar a navegar quando a Surface estiver vazia.

A implicação é importante: em vez de decidir antecipadamente “em qual seção mora cada coisa”, a informação pode simplesmente ser materializada quando solicitada.

---

# 38. Benchmark de dimensionamento: Android/Samsung versus Apple

A pergunta passou então de “qual grid usar?” para **como sistemas consolidados determinam o tamanho de ícones e widgets**.

## 38.1 Samsung / Android

A lógica relevante é predominantemente **cell-based**:

- a Home Screen possui uma grade;
- launchers Samsung historicamente oferecem opções como 4×5, 4×6, 5×5, 5×6, variando por versão/dispositivo;
- widgets ocupam N×M células;
- o launcher conhece a área útil, margens e gaps e resolve a dimensão concreta;
- APIs modernas de widgets Android permitem declarar alvos de largura/altura em células e intervalos de tamanho.

Ou seja, o widget não precisa conhecer a resolução física do aparelho para dizer “quero ocupar 2×1” ou “4×2”.

## 38.2 Apple

A Apple tende a expor famílias abstratas de tamanho, como:

- Small;
- Medium;
- Large;
- em algumas plataformas/contextos, Extra Large e outras famílias.

O desenvolvedor diz quais famílias suporta, e o sistema determina a dimensão concreta daquela família no dispositivo atual.

## 38.3 Possível combinação para a arquitetura

A discussão apontou para aproveitar as duas ideias:

- **internamente:** grid/células como no Android, porque é simples para packing e geometria;
- **externamente/semanticamente:** famílias ou capabilities de representação, para o Tile não depender de pixels nem de um modelo específico de dispositivo.

Assim, o Tile pode conhecer algo como `micro`, `compact`, `wide`, `medium`, `large`, `full`, enquanto a Surface decide quantas células concretas correspondem àquela representação naquele host.

---

# 39. O grid não deve ser “telefone = 8×16”: ele deve ser calculado

A hipótese inicial de declarar, por exemplo, “um celular possui 8×16 slots” foi substituída por uma regra mais geral.

A Surface conhece:

- largura útil disponível (`W`);
- tamanho lógico mínimo desejado para um slot (`S`);
- espaçamento/gutter (`G`).

Uma aproximação discutida para o número de colunas foi:

`C = floor((W + G) / (S + G))`

Depois de descobrir quantas colunas cabem, a Surface pode redistribuir o espaço restante e calcular a largura real das células para preencher a área sem sobras desagradáveis.

O mesmo princípio pode ser aplicado à altura quando uma Surface tiver dimensão vertical limitada, embora uma superfície rolável não precise necessariamente fixar o número de linhas.

A propriedade importante é:

> **a arquitetura não precisa saber previamente se está em “mobile”, “tablet” ou “desktop”; ela precisa saber quanto espaço utilizável existe e quais são as capacidades daquele contexto de apresentação.**

Isso reduz a dependência de breakpoints clássicos por categoria de dispositivo.

A unidade de `S` também deve ser lógica, não pixel físico cru:

- CSS logical pixels na Web;
- `dp`/unidade equivalente em plataformas móveis;
- outra unidade lógica no renderer correspondente.

---

# 40. Presentation Profile: resolução não é a única variável

Uma TV 4K não deve necessariamente produzir dezenas de colunas minúsculas só porque possui muitos pixels físicos.

Foi introduzida a necessidade de um **perfil de apresentação** que considere, além da dimensão da Surface:

- distância típica de visualização;
- modalidade de entrada — touch, mouse, teclado, controle remoto, botões físicos etc.;
- densidade/pixel ratio;
- legibilidade mínima;
- contraste/cor;
- restrições de acessibilidade;
- eventualmente contexto de segurança, como uso em veículo.

Assim, `minimumSlotSize` não precisa ser universalmente idêntico.

Exemplos:

- celular/touch pode exigir alvos confortáveis para dedo;
- desktop/mouse pode trabalhar com maior densidade;
- TV vista a metros de distância precisa de elementos visualmente maiores;
- painel automotivo precisa de leitura rápida e baixo esforço cognitivo;
- display industrial pode ter restrições de cor/resolução.

A estrutura do grid continua igual; o perfil altera os parâmetros usados para calculá-lo.

---

# 41. A consequência em telas gigantes: capacidade espacial cresce sem mudar o modelo

Uma consequência que animou a discussão foi que uma TV, monitor ultrawide ou videowall simplesmente oferece **mais capacidade espacial**.

O mesmo Tile que ocupa, por exemplo, quatro unidades de largura em um celular pode continuar ocupando quatro unidades no modelo lógico. A diferença é que uma Surface enorme comporta muitos outros Tiles simultaneamente.

Isso permite uma progressão natural:

- relógio: talvez um ou poucos Tiles;
- mini display: uma faixa ou uma informação por vez;
- celular: pequeno working set;
- tablet: vários Tiles simultâneos;
- desktop/ultrawide: grande contexto operacional;
- TV/videowall: grande quantidade de informação coexistindo.

A frase espontânea da conversa foi que, numa TV gigante, seria possível **“botar o universo todo ali”** — não porque o Tile muda de natureza, mas porque a Surface passa a ter enorme capacidade para manter contexto simultâneo.

---

# 42. Relógios, carros, mini telas e displays de equipamentos

A discussão então extrapolou celulares/computadores para superfícies muito menores ou especializadas:

- smartwatch;
- display de equipamento;
- painel de carro;
- pequenas telas embarcadas;
- OLED/LCD simples;
- e-ink;
- displays industriais;
- totens;
- TVs e videowalls.

Nesse modelo, eles não são necessariamente “versões diferentes da aplicação”. São **Presentation Surfaces com capacidades diferentes**.

Um relógio pode ter apenas espaço suficiente para um Tile dominante.

Um display horizontal minúsculo pode materializar uma única faixa com texto/estado.

Um carro pode usar poucos Tiles grandes e legíveis.

Um desktop pode materializar muitos.

Uma TV pode abrir um contexto muito mais amplo simultaneamente.

A pergunta deixa de ser “qual aplicação devo construir para esse dispositivo?” e passa a ser:

> **quais representações deste Tile são compatíveis com as capabilities desta Surface?**

---

# 43. Tile como candidata à unidade universal de apresentação

Nesse ponto apareceu explicitamente a ligação com a busca que iniciou toda a conversa.

O objetivo inicial era **interoperabilidade visual/de apresentação**: descrever significado uma vez e permitir sua materialização em superfícies muito diferentes.

O Tile passou a ser visto como uma candidata concreta à **unidade universal de apresentação espacial**.

Exemplo com uma mesma informação de temperatura:

- display mínimo: `23°`;
- relógio: `23° · chuva`;
- Tile compacto no celular: temperatura + próxima hora;
- Tile maior: previsão horária;
- Tile grande: gráfico, tendência e detalhes;
- TV/videowall: visualização ainda mais rica.

A identidade semântica da informação pode permanecer a mesma. O que muda é sua **materialização conforme espaço e capabilities**.

Isso fecha uma lacuna que estava aberta desde o início: havia um protocolo semântico, Renderers e componentes, mas faltava uma unidade espacial simples que sobrevivesse a superfícies radicalmente diferentes.

Uma ressalva permanece importante: `Tile` é naturalmente uma abstração **espacial/visual**. Para superfícies não espaciais, como voz pura, a camada de Response/Renderer continua necessária para fallback não visual. Portanto, “universal” aqui significa universal dentro do domínio de superfícies de apresentação espacial, sem eliminar os demais renderers.

---

# 44. Dockstation física com display monocromático barato

A conexão com a Dock física apareceu novamente.

Uma dockstation pode incorporar uma **Presentation Surface extremamente simples**, por exemplo:

- OLED monocromático pequeno;
- LCD de poucas linhas;
- e-ink;
- display 128×64 ou equivalente;
- nenhum touch;
- poucos botões ou nenhum controle local.

A dockstation pode declarar capabilities como:

- largura/altura lógica ou física;
- profundidade de cor — inclusive 1-bit/monocromática;
- suporte ou não a imagens;
- quantidade de linhas/caracteres quando aplicável;
- tipos de entrada disponíveis;
- taxa de atualização;
- restrições energéticas.

Isso **não adiciona inteligência de domínio à Dock**.

A separação permanece:

- Dock/dDock recebe, guarda e despacha eventos;
- o display é uma capability/periférico físico do host;
- Presentation Agent/Renderer decide o que materializar;
- o Tile fornece representação compatível com aquela Surface.

Exemplos de informação que um display minúsculo poderia materializar, dependendo dos eventos/contexto:

- usuário conectado;
- próxima reunião;
- combustível;
- porta aberta;
- quantidade de eventos pendentes;
- estado de equipamento;
- alerta operacional.

A Dock não precisa compreender “reunião”, “combustível” ou “porta”. Ela apenas oferece infraestrutura e superfície; a interpretação pertence aos Agents/Renderers apropriados.

Isso abre a possibilidade de **hardware muito barato participar da mesma arquitetura de apresentação** sem exigir uma aplicação visual dedicada para cada dispositivo.

---

# 45. Consolidação do cálculo de apresentação

A arquitetura passa a ter, provisoriamente, três níveis distintos para responder “quanto e como mostrar?”:

1. **Surface Capability / Presentation Profile** informa espaço, densidade, cor, entrada, distância de visualização e restrições;
2. **Grid/Slot Engine** transforma essa capacidade em células lógicas utilizáveis;
3. **Tile** escolhe ou negocia uma representação compatível com o espaço que recebeu.

Em forma resumida:

`capabilities da Surface -> cálculo de slots -> espaço disponível -> representação do Tile -> layout real -> medição/feedback`

Isso mantém separadas três responsabilidades que poderiam facilmente se misturar:

- dispositivo não decide semântica;
- Tile não precisa conhecer resolução/dispositivo concreto;
- Surface não precisa conhecer implementação interna do Tile.

---

# 46. Consolidação da navegação sem páginas

A partir das últimas correções, a Presentation Surface deixa de ser apenas “um dashboard que se monta sozinho”.

Ela passa a assumir também o papel de **histórico operacional imediatamente acessível**.

A sequência conceitual é:

- informação pedida agora sobe/materializa no topo;
- informação que estava ativa continua logo abaixo;
- informação antiga permanece mais distante no fluxo;
- reacessar algo antigo traz aquilo de volta ao presente;
- pinning permite declarar exceções persistentes;
- contextos permitem congelar e retomar determinados estados de trabalho.

Portanto, mecanismos tradicionais podem se tornar opcionais ou desaparecer em determinadas superfícies:

- `Back`;
- Home;
- abas permanentes;
- árvore de navegação;
- menus por aplicação.

Não porque navegação deixou de existir, mas porque **ela foi incorporada ao próprio arranjo temporal/contextual da Surface**.

---

# 47. Estado conceitual atual

A arquitetura de apresentação, no ponto atual, pode ser resumida assim:

- **Response** preserva significado independente da representação;
- **Agent** conhece domínio e produz/consome eventos;
- **Bus** distribui eventos localmente;
- **Bridge** transporta eventos entre fronteiras;
- **Dock/dDock** armazena e despacha eventos sem inteligência de domínio;
- **Presentation Agent / Renderer** interpreta intenção e capabilities de apresentação;
- **Presentation Surface** oferece espaço e um perfil de apresentação;
- **Grid/Slot Engine** transforma esse espaço em unidades lógicas;
- **Tile** é a unidade espacial viva que materializa informação/ação em diferentes densidades;
- **Component** implementa peças internas encapsuladas do Tile;
- **Context** persiste working set, recência/prioridade, Tiles e estado necessário para retomada.

O fluxo geral continua podendo ser acionado por:

- interação direta;
- tempo;
- localização;
- proximidade;
- BLE;
- Dock;
- outro Agent;
- voz;
- LLM;
- eventos externos em geral.

A Surface deixa de ser “uma tela desenhada” e passa a ser uma **capacidade de apresentação que se materializa conforme eventos, espaço e contexto**.

---

# 48. Questões ainda abertas para experimentação

A conversa ainda não fechou alguns pontos que deverão ser provados empiricamente:

- valor inicial adequado de `minimumSlotSize` por perfil;
- conjunto canônico de formatos/tamanhos de Tile;
- quanto um Tile pode variar continuamente versus trabalhar com famílias discretas;
- algoritmo de packing/reflow;
- regras exatas de último acesso, criação e prioridade;
- compactação automática de Tiles antigos;
- semântica de `pin` em telas pequenas versus grandes;
- quantidade de histórico mantida materializada;
- virtualização de Tiles muito antigos;
- transições que preservem orientação espacial sem impedir recência;
- acessibilidade e alto contraste;
- segurança/limites para superfícies automotivas;
- capabilities mínimas para displays monocromáticos/textuais;
- persistência de contexto sem misturar estado visual efêmero com estado semântico;
- fallback para voz e outras superfícies não espaciais.

O que deixou de ser questão aberta é a direção geral:

> **Tile aparece como a unidade espacial que faltava para transformar interoperabilidade de apresentação em algo concreto: a mesma informação pode se materializar de forma mínima ou rica conforme a Surface, de um display monocromático barato a um videowall, sem obrigar a existência de páginas ou aplicações visuais diferentes para cada dispositivo.**
