# LifeSteel

LifeSteel e uma base jogavel em Python + Pygame-CE para um RPG top-down de sobrevivencia, coleta, construcao, economia, NPCs e progressao.

## Como rodar

```bash
pip install -r requirements.txt
python main.py
```

O projeto usa `pygame-ce>=2.5,<3`. No PyPI, a linha 2.5.x e a linha estavel atual em junho de 2026.

## Controles

- `W A S D`: mover
- `Shift`: correr
- `Mouse esquerdo`: atacar, usar ferramenta ou abrir estrutura clicada
- `Mouse direito`: colocar construcao equipada no chao
- `E`: interagir com NPC, loja ou recurso proximo
- `I`: inventario
- `C`: status/personagem
- `J`: missoes
- `M`: mapa expandido
- `Q`: consumir 1 unidade do item consumivel equipado
- `F`: pegar item do chao
- `B`: menu de construcao por materiais
- `K`: arvore de habilidades
- `Esc`: pausa/configuracoes
- `1` a `5`: selecionar hotbar
- `Tab`: alternar abas abertas
- `F3`: overlay de debug/performance
- `F5`: salvar
- `F9`: carregar

## O que ja existe nesta primeira versao

- Tela inicial, configuracoes e criacao de personagem.
- Seis classes iniciais com arma, vantagens, desvantagens e atributos.
- Mundo top-down 4x maior que a versao inicial, com camera seguindo o jogador.
- Mundo dividido em chunks ativos/visiveis para reduzir processamento fora da regiao do jogador.
- Geracao procedural por seed com biomas de floresta, clareira, campo, lago, pantano, floresta densa e areas rochosas.
- Povoados gerados no mapa com zonas seguras, placas e vendedores especializados por local.
- Cavernas aleatorias com entrada no mundo, saida interna, escuridao reforcada, recursos, baus e loot por raridade.
- HUD com HP, XP, fome, sede, energia, mana, moedas, relogio, clima, hotbar e minimapa.
- Aba de missoes em `J`, com lista de quests liberadas, ativas, completas e recompensas para resgatar.
- Missões iniciais dos niveis 1 a 5 carregadas de `src/data/quests.json`, com progresso salvo junto do save.
- Recompensas de quests sao resgatadas manualmente e incluem itens unicos especiais.
- Inventario com slots, hotbar, descricao, usar, equipar, dropar e drag-and-drop.
- Mochila equipavel com inventario lateral; se for dropada, o conteudo continua dentro dela.
- Sistema modular de alimentos, bebidas e pocoes carregado de `src/data/foods.json`.
- Consumo por `Q` do item consumivel equipado, sempre 1 unidade por vez.
- Consumiveis aplicam `Vida`, `Fome`, `Sede`, `Energia`, `Mana` e `mana_percent`, com efeitos positivos e negativos respeitando os limites do jogador.
- Coleta com ferramentas: arvores, pedras, minerio, arbustos e solo.
- NPCs vendedores fisicos no mapa; loja abre apenas por proximidade e cada vendedor tem estoque/compra por especialidade.
- Precos com desconto por Comunicacao e bonus de venda por Comercio/Politica.
- XP geral, level, skills individuais e desbloqueios de loja/crafting.
- Monstros definidos em `src/data/mobs.json`, com spawn aleatorio por dia/noite, bioma, caverna, limite por chunk e escalonamento de HP/dano.
- Animais iniciais: porcos, vacas e galinhas, com drops de carne, couro, pele, penas e ovos.
- Sistema de fome/sede ajustado: fome cai 1 a cada 10s; sede cai 2 a cada 10s e 5 a cada 10s correndo.
- Corrida fica bloqueada se fome ou sede estiverem abaixo de 30%.
- Loja vende Copo de Agua barato, que recupera 15 de sede, Copo Vazio e itens compraveis liberados pelo JSON conforme vendedor, level e raridade.
- Copo Vazio pode ser equipado e enchido com `E` perto de rios ou lagos.
- Morte real: ao chegar a 0 HP, o jogador dropa os itens no chao, volta ao spawn e recebe mensagem "Voce morreu".
- Particulas para coleta, impacto, corrida, magia e coleta de itens.
- Crafting em grade: mostra todas as receitas liberadas, com ficha lateral de materiais, uso e botao Criar.
- Crafting bloqueia corretamente se faltar material ou se inventario/mochila estiver cheio.
- Bancada inicial perto do spawn para comecar a craftar imediatamente.
- Construcoes equipaveis: equipe fogueira, bancada, tocha, fogao etc. e clique com botao direito no mundo para colocar.
- Estruturas colocadas com interface, como bancada, fogao e bau, abrem com `E` quando o personagem esta perto.
- Bau Pequeno craftavel com 12 slots, drag-and-drop com inventario/mochila, save/load do conteudo e quebra com machado dropando tudo.
- XP de recursos rebalanceado: arvores e arbustos 1 XP, pedras 3 XP, minerios 5 XP; combate escala mais XP por nivel do inimigo.
- Fogueira e Fogao de pedra com interface de cozinha para assar carnes/peixes crus e preparar receitas, sucos e pocoes permitidos pela estacao.
- Receitas craftaveis do JSON verificam estacao, habilidade, ingredientes, espaco no inventario e dao XP na habilidade relacionada.
- Drops de alimentos podem ser rolados por fonte usando raridade, chance e quantidade do JSON.
- Tochas iluminam a noite e apagam durante chuva/tempestade.
- Ciclo de dia/noite com fases `day`, `sunset`, `night` e `dawn`.
- Sistema de iluminacao por camada preta com recortes transparentes para jogador, tochas, fogueira e fogao, sem halos brancos.
- Mapa/minimapa com exploracao revelada, cache de desenho e icones de povoados/cavernas no mapa expandido.
- Sistema de agua: nadar reduz velocidade, drena energia e causa dano progressivo se a energia chegar a zero.
- Level up aumenta atributos maximos por classe usando `src/data/level_growth.json`.
- Ferramentas e armas tem durabilidade real, tooltip, persistencia no save e quebram quando chegam a zero.
- Missoes especificas por local/NPC sao liberadas ao descobrir povoados ou atender requisitos.
- Otimizacoes de render/update com chunks ativos, culling de entidades fora da tela, limite de particulas e cache de mascaras de luz.
- Overlay `F3` com FPS, tempo de update/render, entidades, particulas e luzes processadas.
- Save/load em JSON em `saves/save_01.json`, incluindo chunks modificados, cavernas, povoados, exploracao por area, mobs, agua, quests e durabilidade.
- Assets placeholder gerados por codigo e pastas de assets organizadas para substituicao futura.

## Testes manuais sugeridos

- Criar um jogo novo e confirmar que o mapa abre 320x320 tiles, com spawn seguro e bancada/fogueira iniciais.
- Andar ate um povoado, ver a notificacao de descoberta, falar com cada vendedor e conferir estoque especializado.
- Entrar em uma caverna, abrir bau, coletar loot, sair com `E` e salvar/carregar dentro e fora da caverna.
- Esperar dia/noite em biomas diferentes e confirmar spawn de mobs sem nascerem dentro de agua ou de zona segura.
- Entrar na agua ate zerar energia e verificar dano progressivo; sair da agua deve interromper o afogamento.
- Usar ferramentas corretas e erradas em recursos, observar durabilidade no tooltip e confirmar quebra ao chegar em zero.
- Subir de nivel e confirmar aumento dos atributos maximos conforme a classe.

## Estrutura

```text
LifeSteel/
  main.py
  requirements.txt
  src/
    core/
    entities/
    systems/
    items/
    world/
    ui/
    data/
  assets/
  saves/
```

Os sprites sao placeholders procedurais no `AssetLoader`. Para trocar por pixel art real, mantenha os nomes de classe e coloque spritesheets nas pastas em `assets/sprites/player/<classe>/`.
