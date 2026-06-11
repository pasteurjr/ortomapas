# Guia Completo: Configuracao do DJI Mini 3 para Ortomapas

**Versao:** 1.0 | **Data:** Marco 2026

---

## Sumario

1. [Visao Geral do DJI Mini 3 para Mapeamento](#1-visao-geral)
2. [Softwares Necessarios](#2-softwares-necessarios)
3. [Planejamento de Voo com Litchi + Drone Grid Planner](#3-planejamento-de-voo)
4. [Configuracoes da Camera para Ortomapeamento](#4-configuracoes-da-camera)
5. [Parametros de Voo Otimizados](#5-parametros-de-voo)
6. [Fluxo de Trabalho Completo: Do Planejamento ao Voo](#6-fluxo-de-trabalho-completo)
7. [Alternativas ao Litchi](#7-alternativas-ao-litchi)
8. [Checklist Pre-Voo e Dicas de Campo](#8-checklist-pre-voo)
9. [Processamento das Imagens (Geracao do Ortomapa)](#9-processamento-das-imagens)
10. [Regulamentacao Brasileira para Drones](#10-regulamentacao-brasileira)

---

## 1. Visao Geral

O DJI Mini 3 e um drone excelente para ortomapeamento amador e semi-profissional por varios motivos:

| Especificacao | Valor |
|---|---|
| **Peso** | 248g (abaixo do limite de 250g da ANAC) |
| **Sensor** | CMOS 1/1.3 polegadas |
| **Resolucao Maxima** | 48 MP (8064 x 6048 px) |
| **Distancia Focal** | 24mm equivalente (~6.7mm real) |
| **Abertura** | f/1.7 (fixa) |
| **Campo de Visao** | 82.1 graus |
| **Foco** | 1m ao infinito |
| **Formatos de Foto** | JPEG, DNG (RAW) |
| **Gimbal** | Estabilizacao mecanica 3 eixos |
| **Tempo de Voo (bateria padrao)** | ~38 min (25-28 min efetivo em mapeamento) |
| **Tempo de Voo (bateria Plus)** | ~51 min (35-40 min efetivo em mapeamento) |

### Vantagem Regulatoria no Brasil

Com 248g, o DJI Mini 3 esta **isento de registro na ANAC** para uso recreativo (RBAC-E No. 94). Nao exige seguro obrigatorio nem licenca de piloto remoto para voos recreativos abaixo de 120m AGL.

> **ATENCAO:** A bateria Intelligent Flight Battery Plus aumenta o peso para ~290g, ultrapassando o limite de 250g. Com ela, registro ANAC e seguro passam a ser obrigatorios.

---

## 2. Softwares Necessarios

### 2.1 Aplicativo de Voo: Litchi Pilot

**Site:** https://flylitchi.com/

- Usar a versao **"Litchi Pilot"** (NAO a versao antiga "Litchi for DJI Drones")
- Disponivel para iOS e Android
- Custo: ~US$25 (compra unica)
- Versao 5.0.0+ (dezembro 2025) suporta retomada de missao apos troca de bateria
- Suporta ate 99 waypoints por missao

**Por que Litchi e nao o DJI Fly?**
O aplicativo oficial DJI Fly **nao possui** modo de missao automatizada para mapeamento. Nao gera grids, nao calcula sobreposicao e nao automatiza a captura de fotos para ortomosaicos.

### 2.2 Planejador de Missao Web: Litchi Mission Hub

**URL:** https://flylitchi.com/hub

Interface web onde voce:
1. Planeja missoes de waypoints no mapa satelital
2. Define altitude, velocidade, direcao, angulo do gimbal e acoes em cada waypoint
3. Salva e sincroniza automaticamente com o app Litchi Pilot no celular

### 2.3 Gerador de Grid: Drone Grid Mission Planner (RECOMENDADO)

**URL:** https://www.dronegrid.web.id/

O Litchi Mission Hub **nao possui** gerador de grid automatico. O Drone Grid Mission Planner e uma ferramenta web **gratuita** que gera rotas de mapeamento:

**Funcionalidades:**
- 6 modos de missao: Grid (cortador de grama), Corredor, Fachada, Orbita, Helice, Panorama
- Modo Grid ideal para ortomosaicos
- Selecao de drone (possui preset do DJI Mini 3)
- Calculo automatico de GSD
- Calculo automatico de espacamento entre linhas e intervalos de foto
- Seguimento de terreno usando dados DEM do Copernicus
- Divisao automatica para multiplas baterias (limite de 99 waypoints)
- Modo double-grid para cobertura cruzada 3D
- **Exporta em formato CSV do Litchi**

---

## 3. Planejamento de Voo com Litchi + Drone Grid Planner

### Passo 1: Acessar o Drone Grid Mission Planner

1. Abrir https://www.dronegrid.web.id/ no navegador
2. Selecionar o drone: **DJI Mini 3**
3. Navegar no mapa ate a area de interesse

### Passo 2: Desenhar a Area de Mapeamento

1. Clicar no icone de poligono no mapa
2. Clicar nos vertices da area que deseja mapear
3. Fechar o poligono clicando no primeiro ponto novamente

### Passo 3: Configurar Parametros de Voo

| Parametro | Valor Recomendado | Observacao |
|---|---|---|
| **Altitude** | 50m AGL | Equilibrio entre resolucao e cobertura |
| **Sobreposicao Frontal** | 75% | Minimo 65%, ideal 75-80% |
| **Sobreposicao Lateral** | 70% | Minimo 60%, ideal 70-75% |
| **Velocidade** | 4 m/s (~14 km/h) | Mais lento = fotos mais nitidas |
| **Angulo do Gimbal** | -90 graus (nadir) | Apontando diretamente para baixo |
| **Modo de Foto** | Intervalo de tempo ou distancia | Conforme calculado pelo planner |

**Tabela de GSD por Altitude (48 MP):**

| Altitude (AGL) | GSD Aproximado | Uso Recomendado |
|---|---|---|
| 30m | ~0.7 cm/px | Inspecao detalhada, areas pequenas |
| 40m | ~1.0 cm/px | Mapeamento de alta resolucao |
| **50m** | **~1.2 cm/px** | **Mapeamento geral (recomendado)** |
| 60m | ~1.4 cm/px | Mapeamento de media resolucao |
| 80m | ~1.9 cm/px | Cobertura de areas maiores |
| 100m | ~2.4 cm/px | Cobertura maxima por bateria |
| 120m | ~2.9 cm/px | Visao geral de grandes areas |

**Formula do GSD:**
```
GSD (cm/px) = (Largura Sensor mm x Altitude m x 100) / (Distancia Focal mm x Largura Imagem px)

Para DJI Mini 3 a 48MP:
GSD = (9.6 x H x 100) / (6.7 x 8064) = 0.01776 x H cm/px
```

### Passo 4: Exportar CSV para o Litchi

1. Revisar a missao no Drone Grid Planner:
   - Verificar numero de waypoints (max 99 por missao)
   - Verificar numero estimado de fotos
   - Verificar tempo estimado de voo vs. bateria disponivel
2. Clicar em **"Download CSV"**
3. O arquivo sera salvo no formato compativel com Litchi

### Passo 5: Importar no Litchi Mission Hub

1. Acessar https://flylitchi.com/hub
2. Fazer login na sua conta Litchi
3. Ir em **Missions > Import**
4. Selecionar o arquivo CSV exportado
5. Verificar os waypoints no mapa:
   - Confirmar que a rota cobre toda a area
   - Verificar altitudes dos waypoints
   - Confirmar acoes em cada waypoint (tirar foto)
6. Salvar a missao com um nome descritivo (ex: "Serra_Moeda_Grid_50m_20260325")

### Passo 6: Sincronizar com o App Litchi Pilot

1. Abrir o aplicativo **Litchi Pilot** no celular/tablet
2. Estar conectado a internet
3. A missao sincroniza automaticamente com o app
4. Verificar que a missao aparece na lista de missoes

### Passo 7: Executar a Missao no Campo

1. **IMPORTANTE:** Forcar parada do app DJI Fly antes de abrir o Litchi
2. Conectar o drone ao controle e ao celular
3. Abrir Litchi Pilot
4. Selecionar a missao
5. Verificar waypoints no mapa sobrepostos ao terreno real
6. Iniciar a missao

---

## 4. Configuracoes da Camera para Ortomapeamento

### Configuracoes Obrigatorias

| Configuracao | Valor | Motivo |
|---|---|---|
| **Resolucao** | 48 MP | Maximo de resolucao para GSD otimo |
| **Formato** | JPEG (ou DNG+JPEG se houver espaco) | JPEG suficiente; DNG para pos-processamento avancado |
| **Angulo do Gimbal** | -90 graus (nadir) | Olhando diretamente para baixo |
| **Modo de Exposicao** | Manual (preferido) | Exposicao consistente entre fotos |
| **ISO** | 100-200 (o mais baixo possivel) | Minimizar ruido |
| **Velocidade do Obturador** | 1/500s ou mais rapido | Evitar motion blur |
| **Foco** | Infinito (travar apos foco inicial) | Consistencia entre fotos |
| **Balanco de Branco** | Fixo (Ex: Ensolarado, Nublado) | NAO usar Auto WB |

### Por Que NAO Usar Auto em Nada

- **Auto Exposicao:** Muda entre fotos, criando faixas claras/escuras no ortomosaico
- **Auto Foco:** Pode focar em objetos proximos ou perder foco entre fotos
- **Auto Balanco de Branco:** Muda tonalidade entre fotos, dificultando stitching
- **Solucao:** Tudo manual e fixo durante toda a missao

### Procedimento de Configuracao no Campo

1. Decolar e subir ate a altitude de mapeamento
2. Apontar camera para baixo (-90 graus)
3. Usar Auto Foco para focar no terreno
4. **Travar o foco** (mudar para modo manual)
5. Ajustar ISO e velocidade do obturador manualmente
6. Fixar balanco de branco (Ensolarado em dias claros)
7. Tirar uma foto teste e verificar exposicao
8. Iniciar a missao

---

## 5. Parametros de Voo Otimizados

### Velocidade de Voo por Altitude

| Altitude | Velocidade Recomendada | Observacao |
|---|---|---|
| 30-50m | 3-4 m/s (~7-9 mph) | Mais lento para fotos nitidas |
| 50-80m | 4-6 m/s (~9-13 mph) | Bom equilibrio |
| 80-120m | 5-8 m/s (~11-18 mph) | Pode ir mais rapido |

### Cobertura e Fotos por Hectare

**A 50m de altitude, 75% frontal / 70% lateral, 48MP:**

| Metrica | Valor Aproximado |
|---|---|
| Footprint da imagem | ~72m x 54m |
| Avanco efetivo por foto | ~13.5m |
| Espacamento entre linhas | ~21.6m |
| **Fotos por hectare** | **35-45 fotos** |
| **Cobertura/bateria (padrao, ~25 min)** | **5-8 hectares** |
| **Cobertura/bateria (Plus, ~35 min)** | **8-12 hectares** |

**A 80m de altitude, 75%/70%:**

| Metrica | Valor Aproximado |
|---|---|
| Fotos por hectare | ~15-20 fotos |
| Cobertura/bateria (Plus) | ~15-25 hectares |

### Gestao de Bateria

- **Sempre pousar com >20% de bateria** restante
- Kit Fly More Combo com 3 baterias e altamente recomendado
- Litchi Pilot v5.0+ suporta retomada de missao apos troca de bateria
- Drone Grid Planner divide automaticamente missoes para multiplas baterias
- Voar primeiro os pontos mais distantes, mais proximos por ultimo
- Ventos fortes reduzem significativamente o tempo efetivo de voo

---

## 6. Fluxo de Trabalho Completo: Do Planejamento ao Voo

```
FASE 1: PLANEJAMENTO (Em Casa)
================================
1. Definir area de interesse no Google Maps/Earth
2. Anotar coordenadas GPS dos limites da area
3. Acessar dronegrid.web.id
4. Selecionar DJI Mini 3
5. Desenhar poligono da area
6. Configurar: 50m altitude, 75%/70% overlap, 4 m/s
7. Exportar CSV
8. Importar no Litchi Mission Hub (flylitchi.com/hub)
9. Verificar e salvar missao
10. Sincronizar com app Litchi Pilot

FASE 2: VERIFICACAO (Em Casa)
================================
11. Verificar previsao do tempo (vento < 20 km/h)
12. Verificar SARPAS/DECEA para restricoes de espaco aereo
13. Carregar todas as baterias
14. Formatar cartao SD (V30 ou superior)
15. Verificar lista de equipamentos

FASE 3: NO CAMPO
================================
16. Chegar ao local, avaliar condicoes
17. Identificar ponto de decolagem seguro
18. Marcar GCPs (Ground Control Points) se necessario
19. Montar drone e controle
20. FORCAR PARADA do DJI Fly
21. Abrir Litchi Pilot
22. Conectar drone
23. Configurar camera: 48MP, manual, ISO 100-200, 1/500+, foco infinito
24. Verificar missao no mapa
25. Tirar foto teste
26. Iniciar missao

FASE 4: DURANTE O VOO
================================
27. Monitorar progresso da missao
28. Observar nivel de bateria
29. Se necessario, trocar bateria e retomar missao (Litchi 5.0+)
30. Manter VLOS (linha de visada visual) com o drone

FASE 5: POS-VOO
================================
31. Verificar fotos no cartao SD (quantidade, qualidade)
32. Copiar fotos para backup imediato
33. Registrar metadados do voo (data, hora, condicoes, area)
34. Processar em WebODM (ver secao 9)
```

---

## 7. Alternativas ao Litchi

### 7.1 Dronelink

**URL:** https://www.dronelink.com/
- Suporta DJI Mini 3
- Subscription: ~US$15+/mes
- Grid de mapeamento integrado
- Simulacao de voo virtual antes do voo real
- Mais poderoso que Litchi para missoes complexas
- Baixar app do site (NAO do Google Play)

### 7.2 Maven

**URL:** https://www.mavenpilot.com/
- Suporta DJI Mini 3
- Freemium (recursos basicos gratuitos)
- Divisao automatica por tempo de voo para fotogrametria
- MavenRoute (planejador web) sincroniza com app mobile

### 7.3 QGIS UAV Mapping Path Generator Plugin

**URL:** https://plugins.qgis.org/plugins/drone_path/
- Plugin gratuito para QGIS
- Gera CSV compativel com Litchi a partir de poligonos do QGIS
- Bom se voce ja tem limites de levantamento em formato GIS

### 7.4 DJIFlightPlanner

**URL:** https://www.djiflightplanner.com/
- Ferramenta desktop/web para grids
- Exporta waypoints compativeis com Litchi
- Calculos de GSD e estimativas de cobertura

### 7.5 Comparativo

| Software | Suporta Mini 3 | Grid Nativo | Custo | Facilidade |
|---|---|---|---|---|
| **Litchi + Grid Planner** | SIM | Via CSV | ~US$25 unico | Media |
| **Dronelink** | SIM | SIM | Assinatura ($15+/mes) | Media-Alta |
| **Maven** | SIM | SIM | Freemium | Media |
| **DJI Fly** | SIM (manual) | NAO | Gratis | Facil |

---

## 8. Checklist Pre-Voo e Dicas de Campo

### Equipamentos Essenciais

- [ ] DJI Mini 3 + controle remoto
- [ ] 3x baterias carregadas (Fly More Combo)
- [ ] Cartao microSD de alta velocidade (V30+, 64GB+)
- [ ] Celular/tablet com Litchi Pilot instalado
- [ ] Cabo de conexao drone-celular
- [ ] Heliponto portatil (pad de pouso)
- [ ] Protetor solar e chapeu (voce ficara ao sol)
- [ ] Cadeira de campo (voos longos)
- [ ] Powerbank para celular
- [ ] Caderneta de campo para anotacoes
- [ ] GPS de mao ou celular com GPS para marcar GCPs
- [ ] Alvos de GCP (se usar pontos de controle)

### Condicoes Ideais de Voo

| Condicao | Ideal | Aceitavel | Evitar |
|---|---|---|---|
| **Vento** | < 10 km/h | 10-20 km/h | > 20 km/h |
| **Ceu** | Nublado uniforme | Parcialmente nublado | Sombras duras (sol forte com nuvens) |
| **Horario** | 10h-14h (sol alto) | 9h-16h | Nascer/por do sol (sombras longas) |
| **Chuva** | Nenhuma | - | Qualquer chuva |
| **Visibilidade** | > 5 km | > 2 km | Neblina densa |

> **DICA:** O melhor cenario e ceu **nublado uniforme** - eliminates sombras duras e garante iluminacao homogenea em todas as fotos.

### Dicas Importantes no Campo

1. **Sempre forca a parada do DJI Fly** antes de abrir o Litchi Pilot (conflito de apps)
2. **Resete controles para padrao DJI** no DJI Fly antes de usar Litchi (configuracoes de controle customizadas causam erros "Flight Ended")
3. Verifique o espaco livre no cartao SD antes de iniciar
4. Faca backup das fotos imediatamente apos o voo
5. Anote condicoes meteorologicas e horarios
6. Em areas de montanha, considere altitude AGL (acima do solo) vs. MSL (acima do nivel do mar)
7. O Drone Grid Planner tem seguimento de terreno usando DEM Copernicus

---

## 9. Processamento das Imagens (Geracao do Ortomapa)

### 9.1 Software Recomendado: WebODM / OpenDroneMap

**URL:** https://opendronemap.org/ | https://github.com/OpenDroneMap/WebODM

Software **gratuito e open source** para gerar ortomosaicos.

**Instalacao via Docker:**
```bash
git clone https://github.com/OpenDroneMap/WebODM
cd WebODM
./webodm.sh start
```

**Alternativa cloud (paga por tarefa):** https://webodm.net/

### 9.2 Produtos Gerados

| Produto | Formato | Uso |
|---|---|---|
| **Ortomosaico** | GeoTIFF | Mapa aereo georreferenciado |
| **DSM** (Modelo Digital de Superficie) | GeoTIFF | Elevacao incluindo edificios/arvores |
| **DTM** (Modelo Digital de Terreno) | GeoTIFF | Elevacao do terreno "nu" |
| **Nuvem de Pontos** | LAS/LAZ | Modelo 3D do terreno |
| **Malha 3D Texturizada** | OBJ | Visualizacao 3D |

### 9.3 Parametros de Processamento Recomendados

```
--dsm                        # Gerar modelo de superficie
--dtm                        # Gerar modelo de terreno
--orthophoto-resolution 2    # 2 cm/pixel
--dem-resolution 5           # 5 cm/pixel para DEM
--feature-quality high       # Qualidade das features
--mesh-octree-depth 11       # Profundidade da malha
--min-num-features 10000     # Minimo de features por imagem
```

### 9.4 Fluxo de Processamento

```
1. Transferir fotos do cartao SD para o computador
2. Abrir WebODM (http://localhost:8000)
3. Criar novo projeto
4. Upload das fotos (JPEG com EXIF/GPS intacto)
5. Configurar parametros de processamento
6. Iniciar processamento (pode levar horas dependendo do numero de fotos)
7. Baixar produtos (orthomosaic.tif, dsm.tif, dtm.tif)
8. Abrir no QGIS para analise
```

### 9.5 Outros Softwares de Processamento

| Software | Custo | Tipo | Ideal Para |
|---|---|---|---|
| **WebODM/ODM** | Gratis | Local | Orcamento limitado, controle total |
| **WebODM Lightning** | Pago por tarefa | Cloud | Uso ocasional |
| **Agisoft Metashape** | US$179 (Standard) | Local | Profissional, longo prazo |
| **Pix4Dmapper** | US$350/mes | Local/Cloud | Facilidade de uso |
| **DroneDeploy** | US$329/mes | Cloud | Equipes, empresas |

### 9.6 Resultados Esperados com DJI Mini 3

- GSD processado: ~1.4 cm a 40m de altitude, ~2 cm apos processamento
- Erro GPS sem GCPs: ~0.47m (precisao do GPS do drone)
- Erro GPS com GCPs: < 5 cm (com pontos de controle no solo)
- Tempo de processamento: 30 min a varias horas dependendo do hardware e numero de fotos

---

## 10. Regulamentacao Brasileira para Drones

### 10.1 ANAC - RBAC-E No. 94

**Regras para drones abaixo de 250g (DJI Mini 3 com bateria padrao):**
- Isento de registro ANAC para uso recreativo
- Sem seguro obrigatorio
- Sem licenca de piloto remoto

**Regras gerais (todas as categorias):**
- Altitude maxima: 120m AGL (sem autorizacao especial)
- Linha de visada visual (VLOS) obrigatoria
- Distancia minima de 30m de pessoas nao envolvidas
- Idade minima do piloto: 18 anos
- Voos noturnos requerem autorizacao especial
- Voos sobre pessoas proibidos sem autorizacao

### 10.2 DECEA - ICA 100-40

**Sistema SARPAS (Sistema de Acesso de Aeronaves Remotamente Pilotadas):**
- URL: https://servicos.decea.mil.br/sarpas/
- Todos os voos em espaco aereo controlado ou proximo a aeroportos devem ser registrados
- Solicitacoes de voo devem ser submetidas com antecedencia
- O sistema fornece autorizacao automatizada para voos de menor risco

**Restricoes de proximidade de aeroportos:**
- 5.4 km minimo de aeroportos em baixa altitude
- ~9 km minimo ao voar ate 120m AGL
- CTR e TMA requerem autorizacao SARPAS

### 10.3 Parques e Unidades de Conservacao

**Parques Nacionais (ICMBio):**
- Voos de drone sao **proibidos sem autorizacao previa do ICMBio**
- Autorizacao via sistema SISBIO
- Necessario: justificativa de pesquisa, plano de voo, detalhes do equipamento
- Processo pode levar semanas a meses
- Voos comerciais/turisticos geralmente negados

**Parques Estaduais (IEF-MG):**
- Autorizacao do IEF necessaria
- Cada administracao de parque pode ter regras adicionais

### 10.4 Aeroportos da Regiao Metropolitana de BH

| Aeroporto | ICAO | Localizacao | Impacto |
|---|---|---|---|
| **Confins Internacional** | SBCF | 35 km norte de BH | CTR/TMA extenso ao norte |
| **Pampulha** | SBBH | Dentro de BH | Restringe BH central |
| **Base Aerea Lagoa Santa** | SBLS | Proximo a Confins | Espaco aereo militar |

**Zonas menos restritas:** Areas ao sul e oeste de BH (Nova Lima, Brumadinho, Itabirito) geralmente tem menos conflito de espaco aereo.

---

## Apendice A: Formato CSV do Litchi

O formato CSV e simples com um waypoint por linha:

| Coluna | Descricao |
|---|---|
| 1 | Latitude (graus decimais) |
| 2 | Longitude (graus decimais) |
| 3 | Altitude (metros) |
| + | Heading, curve size, rotacao, gimbal pitch, acoes |

As acoes incluem: tirar foto, iniciar/parar gravacao de video, ajustar gimbal.

## Apendice B: Cartoes SD Recomendados

Para mapeamento a 48MP com o DJI Mini 3:

| Cartao | Capacidade | Fotos 48MP (~12MB cada) |
|---|---|---|
| SanDisk Extreme V30 | 64 GB | ~5.300 fotos |
| SanDisk Extreme V30 | 128 GB | ~10.600 fotos |
| Samsung EVO Plus V30 | 256 GB | ~21.300 fotos |

**Recomendacao minima:** 64 GB V30 (suficiente para um dia inteiro de mapeamento).

## Apendice C: Recursos e Links Uteis

| Recurso | URL |
|---|---|
| Litchi Pilot | https://flylitchi.com/ |
| Litchi Mission Hub | https://flylitchi.com/hub |
| Drone Grid Mission Planner | https://www.dronegrid.web.id/ |
| WebODM / OpenDroneMap | https://opendronemap.org/ |
| QGIS | https://qgis.org/ |
| SARPAS (DECEA) | https://servicos.decea.mil.br/sarpas/ |
| ANAC Drones | https://www.gov.br/anac/pt-br/assuntos/drones |
| ICMBio / SISBIO | https://www.gov.br/icmbio/ |
| Dronelink | https://www.dronelink.com/ |
| Maven Pilot | https://www.mavenpilot.com/ |
