# Atualização dos campeonatos

Mantenha as cinco planilhas na pasta `planilhas/`:

```text
planilhas/
├── Serie A2.xlsm
├── Serie B2.xlsm
├── Serie C2.xlsm
├── Serie D2.xlsm
└── Serie E2.xlsm
```

Depois de editar e salvar as planilhas, execute na raiz do projeto:

```powershell
python tools/atualizar_campeonatos.py
```

## Pontuações parciais

O arquivo `tools/atualizar_parciais.py` consulta a API pública do Cartola FC,
identifica a rodada ainda não preenchida nas cinco séries e grava o resultado em
`dados/parciais.json`. Os IDs encontrados para os participantes ficam em
`dados/times-cartola.json`. O cálculo considera capitão, substituição normal do
banco e Reserva de Luxo.

Execução manual:

```powershell
python tools/atualizar_parciais.py
```

No GitHub, o workflow `.github/workflows/atualizar-parciais.yml` executa a
consulta a cada 10 minutos e só cria um commit quando o estado do mercado ou as
pontuações realmente mudarem.

O comando lê as Séries A–E, valida os dados e atualiza os arquivos em `dados/`.

As validações incluem:

- 20 times por série;
- 19 rodadas e 10 confrontos por rodada;
- nomes duplicados ou desconhecidos;
- pontuação preenchida somente de um lado;
- pontos, jogos, vitórias, empates e derrotas;
- pontos marcados, sofridos, saldo e média;
- classificação compatível com os confrontos preenchidos.

Se qualquer série apresentar erro, nenhum JSON é substituído. Corrija a planilha indicada e execute o comando novamente.

## Imagens para divulgação (teste)

Para gerar um PNG da classificação e outro da última rodada concluída:

```powershell
python tools/gerar_imagens.py E
```

Troque `E` por `A`, `B`, `C` ou `D`. Os arquivos são criados na pasta
`imagens-geradas/`. Para escolher outro destino:

```powershell
python tools/gerar_imagens.py --serie E --saida C:\caminho\das\imagens
```

O gerador requer Pillow (`python -m pip install Pillow`).

## Atualização da Libertadores

Mantenha a planilha em `planilhas/LIBERTADORES.xlsm` e execute:

```powershell
python tools/atualizar_libertadores.py
```

O comando lê os grupos A–H, suas seis rodadas e a classificação de quatro
times. Os dois primeiros recebem o destino atual `oitavas`, o terceiro recebe
`copa-do-brasil` e o quarto fica como `eliminado`. A classificação usa, nesta
ordem, pontos, vitórias, saldo e pontos pró como critérios.

A aba `mata mata` é lida como confrontos de ida e volta. Se ela ainda possuir
nomes de outra edição, essas fases são mantidas como `aguardando` e os dados
antigos não são publicados. O arquivo gerado é `dados/libertadores.json`.

## Atualização da Copa do Brasil

Mantenha a planilha em `planilhas/Copa do Brasil.xlsx` e execute:

```powershell
python tools/atualizar_copa_do_brasil.py
```

O comando valida os 64 participantes, lê a chave da aba `Jogos`, localiza os
times no Cartola e grava `dados/copa-do-brasil.json`. O calendário usado é:

- primeira fase: rodadas 24 e 25;
- segunda fase: rodadas 26 e 27;
- terceira fase: rodadas 28 e 29;
- oitavas: rodadas 30 e 31;
- quartas: rodadas 32 e 33;
- semifinais: rodadas 34 e 35;
- final: rodadas 36 e 37.

Quando o mercado estiver fechado, a rodada atual é publicada como parcial. As
rodadas anteriores são consultadas pelo histórico do Cartola. Se houver empate
no agregado, o confronto permanece marcado como `desempate pendente`.
