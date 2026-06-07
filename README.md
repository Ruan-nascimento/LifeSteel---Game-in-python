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
- `M`: mapa expandido
- `Q`: consumir maca rapida
- `F`: pegar item do chao
- `B`: menu de construcao por materiais
- `K`: arvore de habilidades
- `Esc`: pausa/configuracoes
- `1` a `5`: selecionar hotbar
- `Tab`: alternar abas abertas
- `F5`: salvar
- `F9`: carregar

## O que ja existe nesta primeira versao

- Tela inicial, configuracoes e criacao de personagem.
- Seis classes iniciais com arma, vantagens, desvantagens e atributos.
- Mundo top-down de floresta com camera seguindo o jogador.
- HUD com HP, XP, fome, sede, energia, mana, moedas, relogio, clima, hotbar e minimapa.
- Inventario com slots, hotbar, descricao, usar, equipar, dropar e drag-and-drop.
- Mochila equipavel com inventario lateral; se for dropada, o conteudo continua dentro dela.
- Macas iniciais e consumo por `Q`.
- Coleta com ferramentas: arvores, pedras, minerio, arbustos e solo.
- NPC vendedor fisico no mapa; loja abre apenas por proximidade.
- Precos com desconto por Comunicacao e bonus de venda por Comercio/Politica.
- XP geral, level, skills individuais e desbloqueios de loja/crafting.
- Sete tipos de monstros com nome, nivel, bioma, escalonamento de HP/dano e alguns ataques a distancia.
- Animais iniciais: porcos, vacas e galinhas, com drops de carne, couro, pele, penas e ovos.
- Sistema de fome/sede ajustado: fome cai 1 a cada 10s, sede 1 a cada 15s, corrida acelera consumo e fica bloqueada abaixo de 30%.
- Morte real: ao chegar a 0 HP, o jogador dropa os itens no chao, volta ao spawn e recebe mensagem "Voce morreu".
- Particulas para coleta, impacto, corrida, magia e coleta de itens.
- Crafting em grade: mostra todas as receitas liberadas, com ficha lateral de materiais, uso e botao Criar.
- Crafting bloqueia corretamente se faltar material ou se inventario/mochila estiver cheio.
- Bancada inicial perto do spawn para comecar a craftar imediatamente.
- Construcoes equipaveis: equipe fogueira, bancada, tocha, fogao etc. e clique com botao direito no mundo para colocar.
- Estruturas colocadas com interface, como bancada e fogao, abrem com `E` quando o personagem esta perto.
- XP de recursos rebalanceado: arvores e arbustos 1 XP, pedras 3 XP, minerios 5 XP; combate escala mais XP por nivel do inimigo.
- Fogao de pedra com interface para assar carnes e peixes.
- Tochas iluminam a noite e apagam durante chuva/tempestade.
- Mapa/minimapa com exploracao revelada.
- Save/load em JSON em `saves/save_01.json`.
- Assets placeholder gerados por codigo e pastas de assets organizadas para substituicao futura.

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
