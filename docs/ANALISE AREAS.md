# Analise Completa de Areas Para Ortomapeamento com Drone DJI Mini 3

**Regiao:** Entorno de Belo Horizonte, Minas Gerais, Brasil
**Drone:** DJI Mini 3 (248g, bateria padrao)
**Data:** Marco 2026

---

## Sumario

1. [Marco Regulatorio Aplicavel a Todas as Areas](#1-marco-regulatorio)
2. [Serra do Cipo / APA Morro da Pedreira](#2-serra-do-cipo)
3. [Brumadinho / Inhotim](#3-brumadinho--inhotim)
4. [Serra da Piedade](#4-serra-da-piedade)
5. [Parque Nacional da Serra do Gandarela](#5-serra-do-gandarela)
6. [Serra do Curral](#6-serra-do-curral)
7. [Lagoa Santa / Cavernas de Peter Lund](#7-lagoa-santa)
8. [Serra da Moeda](#8-serra-da-moeda)
9. [Serra do Rola-Moca](#9-serra-do-rola-moca)
10. [Quadrilatero Ferrifero (Areas Gerais)](#10-quadrilatero-ferrifero)
11. [Bacia do Rio das Velhas](#11-bacia-do-rio-das-velhas)
12. [Serra do Caraca](#12-serra-do-caraca)
13. [Parque Estadual do Itacolomi](#13-itacolomi)
14. [Serra de Ouro Branco](#14-serra-de-ouro-branco)
15. [Parque Nacional da Serra da Canastra](#15-serra-da-canastra)
16. [Estacao Ecologica de Fechos](#16-ee-fechos)
17. [Areas Adicionais](#17-areas-adicionais)
18. [Tabela Comparativa Geral](#18-tabela-comparativa)
19. [Ranking de Viabilidade Para Voo](#19-ranking-de-viabilidade)
20. [Recomendacoes Finais](#20-recomendacoes-finais)

---

## 1. Marco Regulatorio

### 1.1 ANAC — RBAC-E No. 94

**DJI Mini 3 com bateria padrao (248g) — uso recreativo/pesquisa:**
- Isento de registro ANAC (abaixo de 250g)
- Sem seguro obrigatorio
- Sem licenca de piloto remoto
- Altitude maxima: 120m AGL
- VLOS (linha de visada visual) obrigatorio
- 30m de distancia de pessoas nao envolvidas
- Voos noturnos proibidos sem autorizacao especial
- Voos sobre aglomeracoes proibidos sem autorizacao

> **ATENCAO:** A bateria Intelligent Flight Battery Plus eleva o peso para ~290g, exigindo registro ANAC e seguro.

### 1.2 DECEA — ICA 100-40

**SARPAS NG** (https://servicos.decea.mil.br/sarpas/):
- Autorizacao obrigatoria em espaco aereo controlado
- Proibido dentro de 5.4 km de aeroportos (ate 30m AGL)
- Proibido dentro de 9 km de aeroportos (30-120m AGL)
- Verificar NOTAMs no AISWEB (https://aisweb.decea.mil.br/)
- Verificar zonas DJI GEO no app DJI Fly

### 1.3 Aeroportos da Regiao de BH

| Aeroporto | ICAO | Coordenadas | Elevacao | Tipo |
|---|---|---|---|---|
| **Pampulha** | SBBH | 19°51'07"S, 43°57'02"W | 789m | Civil, CTR Classe D |
| **Confins** | SBCF | 19°37'28"S, 43°58'19"W | 829m | Internacional, CTR Classe D |
| **Lagoa Santa** | SBLS | 19°39'40"S, 43°53'52"W | 852m | Militar |

**Estrutura do espaco aereo:**
- CTR-BH (Pampulha): Classe D, do solo ate ~5.500 ft, raio ~20 km
- CTR-CF (Confins): Classe D, do solo ate 5.500 ft
- TMA-BH1: Classe C, 5.500 ft ate FL145
- TMA-BH2: Classe C, 4.100 ft (~1.250m MSL) ate 5.500 ft

**Ferramenta de verificacao:** GEOAISWEB (https://geoaisweb.decea.mil.br/)

### 1.4 Unidades de Conservacao

| Categoria | Grupo | Drone permitido? | Autorizacao |
|---|---|---|---|
| **Parque Nacional** | Protecao Integral | NAO sem autorizacao | ICMBio via SISBIO |
| **Parque Estadual** | Protecao Integral | NAO sem autorizacao | IEF-MG |
| **Estacao Ecologica** | Protecao Integral | NAO (quase impossivel) | ICMBio/IEF |
| **Monumento Natural** | Protecao Integral | NAO sem autorizacao | IEF-MG |
| **RPPN** | Protecao Integral (privada) | NAO sem autorizacao | Proprietario + ICMBio/IEF |
| **APA** | Uso Sustentavel | **SIM** (regras gerais) | Apenas ANAC/DECEA |
| **ARIE** | Uso Sustentavel | **SIM** (com restricoes) | Orgao gestor |

### 1.5 Barragens e Mineracao

- Barragens de rejeitos sao **infraestrutura critica** — sobrevoo proibido sem autorizacao
- Minas ativas sao propriedade privada — necessaria anuencia da empresa
- Areas de remediacao (pos-Brumadinho/Mariana) podem ter NOTAMs ativos
- Verificar zona GEO da DJI — algumas barragens estao cercadas eletronicamente

### 1.6 Anomalia Magnetica

O Quadrilatero Ferrifero possui **abundancia de magnetita** (minerio de ferro) que causa anomalias magneticas locais fortes. Alem disso, toda a regiao sudeste do Brasil esta sob a **Anomalia Magnetica do Atlantico Sul (AMAS)**, com campo magnetico ~1/3 da media global.

**Impacto pratico para drones:**
- Bussola/magnetometro do drone pode apresentar leituras erraticas
- **Calibrar bussola no local de decolagem, longe de afloramentos de ferro**
- Evitar modo ATTI; preferir navegacao por GPS
- Em areas de itabirito/canga, considerar RTK para trabalho de precisao
- Risco real de queda se calibracao nao for feita

### 1.7 Processo SISBIO (Para Parques Nacionais)

1. Cadastro em https://sicae.sisicmbio.icmbio.gov.br/
2. Curriculo Lattes atualizado
3. Vinculo institucional (universidade facilita)
4. Projeto detalhado: equipamento, plano de voo, justificativa cientifica
5. Prazo de analise: 31-60 dias uteis
6. Tripla autorizacao necessaria: SISBIO + SISANT (ANAC) + SARPAS (DECEA)

---

## 2. Serra do Cipo

### 2.1 Dados Gerais

| Item | PARNA Serra do Cipo | APA Morro da Pedreira |
|---|---|---|
| **Tipo** | Parque Nacional (Protecao Integral) | APA (Uso Sustentavel) |
| **Area** | 31.639 ha | 131.770 ha (~66.200 ha excl. PARNA) |
| **Coordenadas** | 19°13'S-19°32'S, 43°27'W-43°37'W | 19°03'S-19°36'S, 43°22'W-43°42'W |
| **Criacao** | Decreto 90.223/1984 | Decreto 98.891/1990 |
| **Gestao** | ICMBio | ICMBio |
| **Municipios** | Jaboticatubas, Morro do Pilar, Santana do Riacho, Itambe do Mato Dentro | 8 municipios |
| **Distancia de BH** | ~100 km NE (1.5-2h via MG-010) | Idem |

### 2.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | ~60 km NE |
| Distancia de SBCF | ~45-50 km NE |
| Classificacao | Provavelmente Classe G (nao controlado) no nucleo |
| TMA-BH2 | Borda sul da APA pode tangenciar (~12 km de SBCF) |
| **Risco** | **BAIXO** para a maior parte da area |

### 2.3 Onde Pode Voar

**DENTRO DO PARNA: NAO** (sem SISBIO)

**NA APA (FORA DO PARNA): SIM** — regras gerais ANAC/DECEA apenas.

A APA envolve completamente o PARNA e se estende muito alem:
- ~18 km mais ao norte
- ~6 km mais ao sul
- ~8 km mais a oeste
- ~9 km mais a leste

**Arquivos de limites oficiais disponveis:**
- `parna_serra_cipo_boundary.geojson` (1.287 vertices)
- `apa_morro_pedreira_boundary.geojson` (2.839 vertices)
- WFS: `https://geoservicos.inde.gov.br/geoserver/ICMBio/wfs` (layer: `ICMBio:limiteucsfederais_a`)

### 2.4 Referências Praticas no Terreno

| Local | Dentro do PARNA? | Dentro da APA? | Pode voar? | Distancia do PARNA |
|---|---|---|---|---|
| **Lapinha da Serra** | Nao | Sim | **SIM** | ~20 km |
| **Congonhas do Norte / Serra Talhada** | Nao | Sim | **SIM** | ~15 km |
| **Santana do Riacho (cidade)** | Nao | Nao | **SIM** | ~21 km |
| **Cardeal Mota / Vila Serra do Cipo** | Nao | Sim | **SIM** | ~4 km |
| **MG-010 (toda a extensao)** | Nao | Sim | **SIM** | 1-4 km |
| **Estatua do Juquinha (km 116)** | Nao | Sim | **SIM** | ~1.2 km |
| **Posto de gasolina Serra do Cipo** | Nao | Sim | **SIM** | ~3.3 km |
| **Ponte sobre Rio Cipo (km 94)** | Nao | Sim | **SIM** | ~1.3 km |
| **Chapeu de Sol** | Nao | Sim | **SIM** | ~1.2 km |
| **Portaria Areias (portao do parque)** | Nao (limite) | Sim | **SIM** (com margem) | ~300m |
| **Cachoeira da Farofa** | **SIM** | Sim | **NAO** | 200m dentro |
| **Canyon das Bandeirinhas** | **SIM** | Sim | **NAO** | 3.3 km dentro |
| **Veu da Noiva** | **SIM** | Sim | **NAO** | 1.2 km dentro |
| **Alto do Palacio** | **SIM** | Sim | **NAO** | 1.1 km dentro |
| **Tabuleiro** | **SIM** | Sim | **NAO** | ~5.5 km dentro |

### 2.5 Limite Oeste do PARNA (Regra Pratica)

O limite oeste (voltado para a MG-010 e Cardeal Mota) segue uma **linha de cumeada** de ~19°13'S a 19°32'S, em longitudes entre 43°59'W e 43°63'W.

- A **MG-010 inteira** esta fora do PARNA
- **Cardeal Mota** esta 4 km a oeste do limite
- Tudo a **oeste da MG-010** e seguro
- Na duvida, usar os GeoJSON no QField (QGIS mobile) com GPS ligado

### 2.6 Sites Recomendados Para Voo

#### Site 1: Lapinha da Serra (RECOMENDADO PARA COMECAR)

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19°07'S, 43°40'W |
| **Altitude** | 1.100 - 1.687m (Pico do Breu) |
| **Acesso** | Via Santana do Riacho, estrada pavimentada |
| **Dentro do PARNA?** | Nao — APA Morro da Pedreira |
| **Espaco aereo** | Classe G, ~50 km de Confins |
| **Anomalia magnetica** | Baixa (quartzito, nao ferro) |

Por que comecar aqui:
- Campos rupestres sobre quartzito identicos aos do parque
- Sem burocracia ICMBio
- Terreno aberto, ideal para decolagem
- Diversidade: quartzito exposto, campos rupestres, mata de galeria, veredas
- **Area sugerida:** ~10-15 ha nos campos acima de 1.200m, gradiente altitudinal campo rupestre → mata de galeria. 2-3 baterias a 50m.

#### Site 2: Congonhas do Norte / Serra Talhada

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19°02'S, 43°28'W |
| **Altitude** | 1.000 - 1.400m |
| **Dentro do PARNA?** | Nao — APA norte |

Area mais remota, menos estudada. Potencial alto para contribuicao original.

#### Site 3: Cardeal Mota / Serra Morena

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19°18'S, 43°36'W |
| **Acesso** | Diretamente na MG-010 |

Bom para voos de teste — acessivel, cerrado com transicao para campos rupestres.

### 2.7 Janela Temporal

| Periodo | Condicao | Adequacao |
|---|---|---|
| **Maio-Agosto** | Seca, ceu limpo, ar estavel | **MELHOR para mapeamento** |
| **Abril-Maio** | Fim da chuva, vegetacao verde | Melhor para indices de vegetacao |
| **Julho-Setembro** | Seco, rocha exposta | Melhor para mapeamento geologico |
| **Agosto-Setembro** | Pico de risco de fogo | Monitoramento de queimadas |
| **Outubro-Novembro** | Inicio das chuvas, floracao | Melhor para fenologia |
| **Nov-Marco** | Chuvoso, instavel | Evitar |

Voo diario ideal: **08:00 - 14:00** (sol alto, antes dos ventos de altitude da tarde).

### 2.8 Vegetacao e Geologia

**Vegetacao:** 59% cerrado, 28% contato floresta-savana, 13% vegetacao refugial (campos rupestres). Mais de 1.600 especies catalogadas. Endemismo extraordinario (mais especies endemicas que qualquer outra ecorregiao brasileira).

**Geologia:** Quartzito do Supergrupo Espinhaco (~1.7 Ga). Afloramentos dramaticos, canyons, cachoeiras. Solos arenosos derivados de quartzito.

### 2.9 Pesquisa Existente (Para Nao Repetir)

- **Medeiros, Morellato & Silva (2023, Frontiers in Environmental Science):** Mapearam 64 ha de campos rupestres mensalmente por 1 ano com drone de asa fixa a 5 cm/px GSD, acuracia de classificacao >0.95.
- **PELD-CRSC (UFMG, Prof. Geraldo Wilson Fernandes):** Opera na Reserva Vellozia com fenocameras e drones desde 2010.

**Diferencie-se com:** IA/deep learning, pipeline automatizado, deteccao de mudancas temporal, analise geologica.

### 2.10 Valor Cientifico e Potencial de Publicacao

| Aspecto | Avaliacao |
|---|---|
| Valor cientifico | **MUITO ALTO** — hotspot global de biodiversidade |
| Potencial de publicacao | **ALTO** |
| Tema sugerido | Deteccao automatizada de mudancas em campos rupestres com drone consumer-grade e deep learning |
| Journals-alvo | Remote Sensing (MDPI, Q1), Drones (MDPI, Q1), Frontiers in Environmental Science (Q1) |

---

## 3. Brumadinho / Inhotim

### 3.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas Inhotim** | ~20°07'S, 44°13'W |
| **Coordenadas Brumadinho** | ~20°09'S, 44°12'W |
| **Coord. Barragem B1** | 20°07'18"S, 44°07'18"W |
| **Distancia de BH** | ~60 km oeste (1.5h de carro) |
| **Unidades de Conservacao** | APA Sul RMBH (uso sustentavel), RPPN Inhotim (protecao integral privada) |

### 3.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | ~30 km — **fora da CTR** (raio ~20 km) |
| Distancia de SBCF | ~57 km — sem impacto |
| TMA-BH | Dentro da TMA, mas piso em 2.000-3.500 ft AGL. Drone a 120m (400 ft) fica **abaixo** |
| **Risco** | **BAIXO** |
| NOTAMs | Verificar area da barragem B1 — pode ter restricao ativa |
| DJI GEO | Verificar se area da barragem esta cercada eletronicamente |

### 3.3 Onde Pode Voar

| Local | Coordenadas | Pode voar? | Restricao | Interesse |
|---|---|---|---|---|
| **Area rural oeste de Brumadinho** | ~20°08'S, 44°16'W | **SIM** | Nenhuma especial | Paisagem agricola |
| **Rio Paraopeba (jusante da barragem)** | ~20°10'S, 44°07'W rio abaixo | **SIM** | APA Sul (sem restricao real) | **Impacto ambiental do rompimento** |
| **Ribeirao da Prata / Casa Branca** | ~20°05'S, 44°15'W | **SIM** | Minima | Rural, corregos |
| **Serra da Moeda (face oeste)** | ~20°08'S, 44°05'W | **SIM** | APA Sul apenas | **Geologia espetacular** |
| **Entorno de Brumadinho** | ~20°09'S, 44°12'W | **SIM** | Regras padrao ANAC | Interface urbano-rural |
| **Piedade do Paraopeba** | ~20°08'S, 44°16'W-44°20'W | **SIM** | Poucas restricoes | Rural, Paraopeba |

### 3.4 Onde Precisa Autorizacao

| Local | De quem | Dificuldade |
|---|---|---|
| **Dentro do Inhotim** | Instituto Inhotim (inhotim@inhotim.org.br / 31 3571-9700) | Media |
| **RPPN Inhotim** | Instituto + ICMBio/IEF | Media-Alta |
| **Area da barragem B1** | Vale S.A. + verificar NOTAM | Alta |
| **Minas ativas** | Empresa mineradora | Alta |

### 3.5 O Grande Atrativo: Rio Paraopeba Pos-Desastre

O Rio Paraopeba a jusante da barragem e o alvo mais interessante cientificamente:

- **Nao e UC de protecao integral** — regras padrao
- 12 milhoes de m3 de rejeitos toxicos liberados em janeiro 2019
- Contaminacao rastreada por 300+ km rio abaixo
- Mudanca de morfologia fluvial, depositos de sedimento, vegetacao riparia impactada
- **Alto potencial de publicacao** — tema urgente, alta visibilidade
- Acesso via margens com permissao de proprietarios rurais

### 3.6 Inhotim — Detalhes

| Item | Detalhe |
|---|---|
| Area total | 786 ha (visitavel: 140 ha, RPPN: 250 ha) |
| Jardim botanico | 4.300+ especies nativas |
| Arte | ~24 pavilhoes, 500+ obras de 100+ artistas de 30 paises |
| Distancia da barragem B1 | ~10 km (areas operacionais diferentes) |

Voar **dentro** do Inhotim requer autorizacao escrita do Instituto. A RPPN e protecao integral. Obras de arte sao protegidas por direitos autorais — fotografia aerea pode ter implicacoes de PI.

### 3.7 Cuidados Especificos

1. **NOTAMs:** Verificar AISWEB antes de qualquer voo — area da barragem pode ter restricao ativa
2. **DJI GEO Zone:** Verificar no app DJI Fly se a barragem esta cercada eletronicamente
3. **Anomalias magneticas:** Quadrilatero Ferrifero = **muito ferro no solo**. Calibrar bussola no local. Risco real de queda
4. **Ventos na Serra da Moeda:** Escarpamento cria efeito orografico. Mini 3 (248g) e sensivel a rajadas
5. **Seguranca da Vale:** Areas de remediacao tem seguranca ativa. Evitar confronto

### 3.8 Anomalia Magnetica: **ALTO**

Toda a regiao de Brumadinho esta no Quadrilatero Ferrifero. Itabirito e magnetita abundantes.

### 3.9 Valor Cientifico e Potencial de Publicacao

| Aspecto | Avaliacao |
|---|---|
| Valor cientifico | **ALTO** — monitoramento pos-desastre |
| Potencial de publicacao | **ALTO** — tema urgente, alta relevancia social |
| Tema sugerido | Monitoramento de impacto ambiental no Paraopeba por drone de baixo custo |
| Journals-alvo | Science of the Total Environment, Journal of Environmental Management, Environmental Monitoring and Assessment |

---

## 4. Serra da Piedade

### 4.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19°49'S, 43°40'W (topo) |
| **Altitude** | 1.746m |
| **Distancia de BH** | ~50 km leste |
| **Status** | Monumento Natural Estadual (Protecao Integral) — 1.945 ha |
| **Patrimonio** | IEPHA (estadual) + IPHAN (federal) — Conjunto Paisagistico |
| **Gestao** | IEF-MG |
| **Municipios** | Caete, Sabara, Santa Luzia |
| **Acesso** | Estrada pavimentada de Caete (16 km via BR-381/MG-435) |

### 4.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | ~30 km ENE |
| Distancia de SBCF | ~35 km ESE |
| Distancia de SBLS | ~25 km leste |
| Classificacao | Provavelmente fora dos CTRs laterais |
| Atencao | Topo a 1.746m MSL pode entrar na TMA-BH2 (piso 4.100 ft = ~1.250m MSL) |
| **Risco** | **BAIXO a MEDIO** |

### 4.3 Onde Pode Voar

| Local | Pode voar? | Observacao |
|---|---|---|
| **Dentro do Monumento Natural** | NAO sem autorizacao IEF | Protecao integral |
| **Estrada de acesso a partir de Caete** | **SIM** | ~19°50'30"S, 43°42'W — antes do limite da UC |
| **Lado de Barao de Cocais (leste)** | **SIM** | ~19°48'S, 43°38'W — areas rurais fora do monumento |
| **Areas rurais ao redor** | **SIM** | APA Sul ou sem UC |

### 4.4 Anomalia Magnetica: **MUITO ALTO**

Serra da Piedade e composta de **itabirito** (formacao ferrifera bandada) rica em magnetita. E uma das areas com maior anomalia magnetica no Quadrilatero Ferrifero.

- Bussola do drone **SERA** afetada
- Calibrar longe de afloramentos de ferro
- Usar navegacao por GPS primariamente
- RTK recomendado para trabalho de precisao

### 4.5 Geologia

Itabirito da Formacao Caue, Supergrupo Minas. Intercalacoes de camadas ricas em ferro e silica. Estruturas ducteis: dobras, zonas de cisalhamento, falhas. Canga ferrica acima de ~1.200m. Uma das melhores exposicoes geologicas de itabirito do Quadrilatero Ferrifero. Idade >2.4 Ga.

### 4.6 Pesquisas Possiveis

- Mapeamento de afloramentos geologicos em 3D (geologia estrutural)
- Mapeamento do ecossistema de canga
- Avaliacao de proximidade de mineracao
- Estudos de erosao e intemperismo
- Documentacao do Santuario (patrimonio religioso)
- Transectos altitudinais de vegetacao (base ao topo)

### 4.7 Valor Cientifico: **MUITO ALTO**

Interesse geologico excepcional. Ideal para modelos 3D de afloramentos de itabirito para geologia estrutural.

---

## 5. Serra do Gandarela

### 5.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°00'S, 43°40'W |
| **Area** | 31.270 ha |
| **Distancia de BH** | ~40-60 km SE |
| **Status** | Parque Nacional (Protecao Integral) — ICMBio |
| **Criacao** | 13/outubro/2014 |
| **Municipios** | Nova Lima, Raposos, Caete, Santa Barbara, Mariana, Ouro Preto, Itabirito, Rio Acima |
| **Zona de Amortecimento** | Definida pela Portaria ICMBio 1.962 de 23/05/2025 |
| **Contato** | parna.gandarela@icmbio.gov.br / (31) 3545-1883 |

### 5.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | ~25-35 km SSE |
| Distancia de SBCF | ~50 km sul |
| **Risco** | **BAIXO** para a maioria do parque |

### 5.3 Contexto: Mineracao vs. Agua

Criado especificamente para **proteger fontes de agua de BH da mineracao de ferro**. Aquiferos criticos. Canga funciona como filtro e reservatorio natural. Vale S.A. busca construir minas adjacentes. Limite do parque controversamente desenhado para excluir concessoes minerarias.

### 5.4 Onde Pode Voar

**DENTRO DO PARQUE: NAO** (sem SISBIO)

**Fora do parque (zona de amortecimento / APA Sul RMBH): SIM**

| Local | Coordenadas | Pode voar? | Observacao |
|---|---|---|---|
| **Rio Acima (cidade e arredores)** | ~20°02'S, 43°47'W | **SIM** | Fora do parque, APA Sul, acesso via MG-030 |
| **Raposos (Rio das Velhas)** | ~19°58'S, 43°48'W | **SIM** | Fora do parque |
| **Itabirito (lado sul)** | ~20°10'S, 43°40'W | **SIM** | Areas rurais/mineracao fora do parque |
| **MG-030 entre Nova Lima e Rio Acima** | — | **SIM** | Areas rurais com vista para o parque |

### 5.5 Anomalia Magnetica: **ALTO**

Coracao do Quadrilatero Ferrifero. Itabirite/magnetita abundante.

### 5.6 Pesquisas Possiveis

- Monitoramento de zonas-tampao de mineracao
- Mapeamento de nascentes, zonas umidas, areas de recarga
- Avaliacao de integridade da canga
- Monitoramento de barragens de rejeitos
- Corredores ecologicos

### 5.7 Valor Cientifico: **MUITO ALTO**

Conflito mineracao-conservacao-agua e o tema central. Altamente publicavel.

---

## 6. Serra do Curral

### 6.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19°58'S, 43°54'W |
| **Altitude** | 1.538m (Pico Belo Horizonte) |
| **Distancia de BH** | ~5-10 km sul |
| **Status** | Tombado IPHAN (1960). Patrimonio estadual (2022). APA Sul no lado de Nova Lima |
| **Agua** | Nascentes fornecem ~70% da agua de BH capital, ~40% da regiao metropolitana |

### 6.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | **~8-12 km sul** |
| CTR-BH | **Quase certamente dentro** dos limites laterais (porcao norte) |
| Corredores de aproximacao | Pista 13/31 de SBBH tem corredores ao sul |
| **Risco** | **MUITO ALTO** |
| SARPAS | Obrigatorio. Pode ser negado ou restrito |

### 6.3 Conflito Mineracao

- Tamisa Mineracao: 7+ anos tentando instalar complexo minerador em Nova Lima
- Gute Sicht: multada em R$1.2+ milhao, continua operando
- Taquaril Mineracao: licenciada pelo COPAM para extrair 31 milhoes de toneladas. Justica Federal restaurou protecoes e multou ANM em R$4 milhoes
- Batalha judicial ativa

### 6.4 Onde Pode Voar

| Local | Coordenadas | Pode voar? | Observacao |
|---|---|---|---|
| **Mirante Mangabeiras / Praca do Papa** | ~19°57'S, 43°56'W | Dificil | Dentro da CTR provavel. SARPAS necessario |
| **Face norte (BH)** | — | **NAO** | Urbano, CTR, muito restrito |
| **Face sul (Nova Lima)** | ~19°59'S, 43°53'W | Dificil | Ainda proximo a SBBH |
| **Topo do Mundo (extremo oeste, direcao Brumadinho)** | ~20°03'S, 43°58'W | **POSSIVEL** | ~15 km de SBBH, paragliders presentes |
| **Extremo leste (direcao Sabara)** | ~19°58'S, 43°50'W | **POSSIVEL** | ~12-15 km de SBBH, possivel fora da CTR |

### 6.5 Anomalia Magnetica: **MODERADO a ALTO**

Formacoes ferriferas presentes. Calibrar longe de afloramentos.

### 6.6 Pesquisas Possiveis

- Monitoramento de avanco de mineracao (multitemporal) — **alto valor para litigio ambiental**
- Analise de expansao urbana
- Documentacao da paisagem cultural (patrimonio)
- Mapeamento de nascentes
- Saude da vegetacao (impacto de poeira de mineracao)

### 6.7 Valor Cientifico: **ALTO**

Conflito ativo com relevancia juridica. Documentacao por drone pode servir como evidencia legal.

### 6.8 Veredicto Pratico

**Area mais dificil para voo livre** entre todas as analisadas. Espaco aereo muito restrito. Recomendado apenas com SARPAS aprovado e para fins especificos de pesquisa/documentacao.

---

## 7. Lagoa Santa

### 7.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19°38'S, 43°53'W (cidade) |
| **Distancia de BH** | ~30 km norte |
| **Status** | APA Carste de Lagoa Santa (federal, ICMBio) — 37.736 ha |
| **Municipios** | Lagoa Santa, Pedro Leopoldo, Matozinhos, Funilandia, Confins |
| **Patrimonio** | Cavernas protegidas como patrimonio federal. Sitios arqueologicos sob IPHAN |

### 7.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBCF | **~8 km** |
| Distancia de SBLS | **SOBRE** a area carstica (base aerea na cidade) |
| CTR-CF | **Cobre quase toda a area** |
| **Risco** | **MUITO ALTO / PROIBITIVO** |
| SARPAS | Extremamente dificil de obter para a area central |

### 7.3 Interesse Arqueologico

- Peter Lund (1833-1843): megafauna extinta, associacao com restos humanos
- **Lapa Vermelha IV:** "Luzia", um dos esqueletos mais antigos das Americas (11.000-11.500 anos)
- **Lapa do Santo:** Sepultamentos e arte rupestre do Holoceno inicial
- 1.000+ cavernas documentadas
- Paisagem carstica: calcarios da Formacao Sete Lagoas (Grupo Bambui)

### 7.4 Onde PODE Voar (Bordas)

| Local | Coordenadas | Pode voar? | Distancia de SBCF | Observacao |
|---|---|---|---|---|
| **Matozinhos (noroeste)** | ~19°33'S, 44°05'W | **POSSIVEL** | ~15 km | Melhor opcao. Contem Lapa Vermelha |
| **Pedro Leopoldo (oeste)** | ~19°37'S, 44°03'W | Marginal | ~10 km | Verificar SARPAS |
| **Funilandia (norte)** | ~19°22'S, 44°04'W | **SIM** | ~25 km | **Melhor opcao para voo livre** |
| **Borda leste (Vespasiano/Santa Luzia)** | — | **NAO** | Proximo a SBLS | Evitar |
| **Area central (Lagoa Santa cidade)** | ~19°38'S, 43°53'W | **NAO** | ~8 km + SBLS | Proibitivo |

### 7.5 Anomalia Magnetica: **BAIXO**

Terreno carstico e calcario, sem ferro. Sem interferencia magnetica significativa.

### 7.6 Pesquisas Possiveis

- Geomorfologia carstica (dolinas, sumidouros) via DTM de alta resolucao
- Inventario aereo de entradas de cavernas
- Documentacao de sitios arqueologicos
- Expansao urbana sobre carste (risco de subsidencia)
- Mudanca de uso do solo em areas sensiveis

### 7.7 Valor Cientifico: **MUITO ALTO**

Importancia arqueologica e geomorfologica de nivel mundial. Porem, restricao de espaco aereo torna operacao muito dificil.

### 7.8 Veredicto Pratico

**Praticamente zona de exclusao aerea para drones** na area central. Foco em Matozinhos e Funilandia nas bordas. Considerar parcerias com universidades que ja tenham autorizacoes na area.

---

## 8. Serra da Moeda

### 8.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°10'S, 43°55'W |
| **Extensao** | ~70 km norte-sul |
| **Distancia de BH** | ~40-50 km SO |
| **Status** | APA Sul RMBH (uso sustentavel). UC especifica criada por acordo IEF |
| **Municipios** | Nova Lima, Brumadinho, Itabirito, Belo Vale, Ouro Preto |

### 8.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | ~25-35 km SSO |
| Distancia de SBCF | ~55 km sul |
| Atencao | Topos a ~1.700m MSL podem entrar na TMA-BH2 (piso 4.100 ft = ~1.250m MSL) |
| **Risco** | **BAIXO a MEDIO** |

### 8.3 Unidades de Conservacao Adjacentes (NAO VOAR)

| UC | Tipo | Distancia |
|---|---|---|
| **Estacao Ecologica de Fechos** | Protecao integral — fechada ao publico | Encosta NE da serra |
| **PE Serra do Rola-Moca** | Estadual — requer IEF | Adjacente ao norte |

### 8.4 Onde Pode Voar

| Local | Coordenadas | Pode voar? | Observacao |
|---|---|---|---|
| **Topo do Mundo (Brumadinho)** | ~20°05'S, 43°57'W | **SIM** | **Recomendado.** Ponto de decolagem de parapente. Amplo. Atencao parapentes |
| **Estrada de acesso de Moeda** | ~20°17'S, 43°52'W | **SIM** | Elevacoes menores, rural |
| **Face leste (Itabirito, BR-040)** | ~20°13'S, 43°50'W | **SIM** | Rural, ao longo da BR-040 |
| **MG-040 entre Brumadinho e Nova Lima** | ~20°06'S, 43°58'W | **SIM** | Terreno aberto, fora dos parques |

### 8.5 Anomalia Magnetica: **ALTO**

Sinclinal da Moeda e uma estrutura classica de formacao ferrifera. Itabirito com magnetita abundante. Calibracao critica.

### 8.6 Geologia

- Quartzitos da Formacao Moeda (2.62 Ga)
- Itabiritos da Formacao Caue
- Depositos cenozoicos nas terras altas
- **Estrutura sinclinal dramatica visivel do ar**
- Escarpamento com vistas panoramicas
- Perfis de intemperismo cenozoico sobre rochas pre-cambrianas

### 8.7 Pesquisas Possiveis

- Mapeamento de estruturas geologicas (sinclinal)
- Documentacao de impacto de mineracao
- Monitoramento de erosao de escarpamento
- Mapeamento de depositos cenozoicos
- Correlacao vegetacao-geologia
- Planejamento de rotas de geoturismo

### 8.8 Valor Cientifico: **MUITO ALTO**

Geologia estrutural espetacular. Escarpamento visivel e acessivel.

### 8.9 Veredicto Pratico

**MELHOR AREA PARA COMECAR (junto com Lapinha da Serra).** Sem burocracia de parque, espaco aereo favoravel, geologia dramatica, acesso facil. Topo do Mundo e excelente ponto de decolagem.

---

## 9. Serra do Rola-Moca

### 9.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°02'S, 44°00'W |
| **Area** | 3.941 ha |
| **Distancia de BH** | ~15-20 km sul (dentro da RMBH) |
| **Status** | Parque Estadual (Protecao Integral) — IEF-MG |
| **Municipios** | Belo Horizonte, Nova Lima, Ibirite, Brumadinho |

### 9.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | ~15-20 km sul |
| **Risco** | **MEDIO** — borda da CTR-BH, porcoes sul mais livres |

### 9.3 Onde Pode Voar

**DENTRO DO PARQUE: NAO** (sem autorizacao IEF-MG)

**Entorno (APA Sul RMBH): SIM** — regras gerais.

A porcao sul (lado de Brumadinho/Ibirite) e mais distante de Pampulha e tem menor restricao de espaco aereo.

### 9.4 Vegetacao Unica

**Campos rupestres ferruginosos (campos ferruginosos)** — vegetacao extremamente rara que cresce sobre canga ferrica. Existe globalmente apenas no Quadrilatero Ferrifero (MG) e Serra dos Carajas (PA). Interesse cientifico extraordinario.

### 9.5 Anomalia Magnetica: **ALTO**

Canga ferrica = alta concentracao de ferro. Mesmo cuidado das demais areas do QF.

### 9.6 Pesquisas Possiveis

- Mapeamento de canga e campos ferruginosos (raro globalmente)
- Interface urbano-silvestre
- Protecao de nascentes (abastecimento de BH)
- Cicatrizes de fogo
- Impacto de mineracao nas bordas
- Corredores de biodiversidade

### 9.7 Valor Cientifico: **MUITO ALTO** (vegetacao globalmente rara)

---

## 10. Quadrilatero Ferrifero

### 10.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | 19°30'S-20°30'S, 43°20'W-44°10'W |
| **Area** | ~7.000-15.000 km2 |
| **Distancia de BH** | BH fica na borda norte |

### 10.2 Areas Acessiveis Para Voo Livre

#### Proximo a Ouro Preto

| Local | Coordenadas | Pode voar? | Observacao |
|---|---|---|---|
| **Lavras Novas** | ~20°28'S, 43°28'W | **SIM** | Rural, poucas restricoes, terreno geologico rico |
| **Estrada Real (trechos rurais)** | ~20°23'S, 43°30'W | **SIM** | Fora do centro historico |
| **Centro historico de Ouro Preto** | — | **NAO** | Patrimonio Mundial IPHAN |
| Espaco aereo | — | **BAIXO** | ~80 km de SBBH |

#### Proximo a Mariana

| Local | Coordenadas | Pode voar? | Observacao |
|---|---|---|---|
| **Passagem de Mariana** | ~20°23'S, 43°24'W | **SIM** | Sitio historico de mineracao |
| **Estrada Real Ouro Preto-Mariana** | ~20°22'S, 43°25'W | **SIM** | Rural |
| Centro historico | — | **NAO** | Patrimonio IPHAN |

#### Proximo a Itabirito

| Local | Coordenadas | Pode voar? | Observacao |
|---|---|---|---|
| **Rural ao longo da BR-040** | ~20°18'S, 43°48'W | **SIM** | Acessivel, afloramentos |
| **Pico do Itabirito** | ~20°14'S, 43°50'W | Verificar | Interesse geologico, verificar status de protecao |

#### Area do Desastre de Mariana (Samarco/Fundao)

| Item | Detalhe |
|---|---|
| Data | 05/novembro/2015 |
| Volume liberado | 43.7 milhoes de m3 de rejeitos |
| Impacto | Rio Doce, 668 km ate o oceano |
| Restricoes | Barragens = infraestrutura critica. NOTAMs possiveis |
| **Area para voo livre** | Rio Doce a jusante (~20°15'S, 43°10'W, proximo a Barra Longa) — rural, fora de perimetros de seguranca |

### 10.3 Anomalia Magnetica: **ALTO em todo o QF**

Regiao nomeada por suas formacoes ferriferas. Magnetita ubiqua. AMAS agravando.

### 10.4 Valor Cientifico: **MUITO ALTO**

Monitoramento multitemporal de mineracao, barragens, reabilitacao, patrimonio geologico.

---

## 11. Bacia do Rio das Velhas

### 11.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Area da bacia** | 27.850 km2 |
| **Comprimento** | 806.84 km |
| **Nascente** | Cachoeira das Andorinhas, Ouro Preto |
| **Foz** | Rio Sao Francisco |
| **Importancia** | Abastece ~50% da populacao metropolitana de BH (~2 milhoes) |

### 11.2 Mapa de Viabilidade por Trecho

| Trecho | Coordenadas | Espaco Aereo | Pode voar? | Qualidade Agua |
|---|---|---|---|---|
| **Ouro Preto - Itabirito (alto)** | ~20°15'S, 43°48'W | **BAIXO** | **SIM** | Impactada (mineracao) |
| **Rio Acima** | ~20°05'S, 43°47'W | **BAIXO** | **SIM** | Media |
| **Raposos** | ~19°58'S, 43°48'W | **MEDIO** (~18 km SBBH) | **SIM** (com cuidado) | Media |
| **Sabara (margem leste)** | ~19°53'S, 43°46'W | **MEDIO** (~15 km SBBH) | Verificar SARPAS | Ruim |
| **Trecho urbano BH (Arrudas/Onca)** | — | **MUITO ALTO** (CTR-BH) | **NAO** | Pessima |
| **Santa Luzia** | — | **MUITO ALTO** (SBLS) | **NAO** | Ruim |
| **Abaixo de Pedro Leopoldo** | ~19°30'S, 44°00'W | **BAIXO** | **SIM** | Melhorando |
| **Jequitiba - Santana de Pirapama** | ~19°20'S, 44°00'W | **BAIXO** | **SIM** | Boa |

### 11.3 Melhores Trechos Para Monitoramento

1. **Rio Acima** (~20°05'S, 43°47'W) — **MELHOR OPCAO.** Baixo risco aereo, acesso via MG-030, pontes e estradas ao longo do rio, periurbano. Excelente para monitoramento de qualidade da agua.
2. **Raposos** (~19°58'S, 43°48'W) — Boa opcao, risco aereo moderado.
3. **Itabirito (alto curso)** (~20°15'S, 43°48'W) — Nascentes, impacto de mineracao.
4. **Jequitiba** (~19°20'S, 44°00'W) — Rural, sem restricoes, rio mais limpo.

### 11.4 Anomalia Magnetica: Variavel

ALTO proximo a Itabirito/Rio Acima (formacoes ferriferas). BAIXO em areas calcareas a jusante.

### 11.5 Pesquisas Possiveis

- Mapeamento de zonas riparias e saude da vegetacao ciliar
- Indices de turbidez e cor da agua por RGB
- Identificacao de pontos de despejo de esgoto
- Mapeamento de planicie de inundacao
- Monitoramento de restauracao (Projeto Manuelzao)
- Sedimentos de mineracao em tributarios
- Ocupacoes irregulares em APPs

### 11.6 Valor Cientifico: **MUITO ALTO**

Aplicacao pratica direta em gestao de recursos hidricos. Expedicao "Rio das Velhas, te quero vivo" ja usou imagens aereas.

---

## 12. Serra do Caraca

### 12.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°06'S, 43°29'W |
| **Area** | 12.403 ha |
| **Altitude** | 720 - 2.070m (Pico do Sol — mais alto da regiao) |
| **Distancia de BH** | ~120 km leste |
| **Status** | RPPN Santuario do Caraca (Protecao Integral privada) |
| **Proprietario** | Congregacao da Missao (Lazaristas) |
| **Municipios** | Catas Altas, Santa Barbara |

### 12.2 Espaco Aereo

| Fator | Detalhe |
|---|---|
| Distancia de SBBH | ~70 km leste |
| Aeroportos proximos | Nenhum significativo |
| **Risco** | **BAIXO** |

### 12.3 Onde Pode Voar

| Local | Pode voar? | Observacao |
|---|---|---|
| **Dentro da RPPN** | NAO | Autorizacao escrita dos Lazaristas necessaria |
| **Areas rurais ao redor** | **SIM** | Estradas de acesso, fazendas |
| Coordenadas sugeridas | ~20°05'S, 43°32'W | Areas rurais a oeste da RPPN |

### 12.4 Anomalia Magnetica: **MODERADO a ALTO** (Quadrilatero Ferrifero)

### 12.5 Pesquisas Possiveis

- Transectos altitudinais de vegetacao (720m a 2.070m — gradiente notavel)
- Transicao Mata Atlantica / cerrado / campos rupestres
- Documentacao de patrimonio historico-religioso

### 12.6 Valor Cientifico: **ALTO**

Gradiente altitudinal excepcional. Pico do Sol e o mais alto da regiao.

---

## 13. Itacolomi

### 13.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°25'S, 43°29'W |
| **Area** | 7.543 ha |
| **Distancia de BH** | ~100 km SE |
| **Status** | Parque Estadual — IEF-MG |
| **Municipios** | Ouro Preto, Mariana |

### 13.2 Espaco Aereo: **BAIXO** (~80 km de SBBH)

### 13.3 Onde Pode Voar

| Local | Pode voar? | Observacao |
|---|---|---|
| **Dentro do parque** | NAO | Autorizacao IEF necessaria |
| **Areas rurais entre Ouro Preto e Mariana** | **SIM** | ~20°24'S, 43°27'W — fora dos limites do parque |
| **Estrada Passa Dez** | **SIM** | Acesso ao parque, areas fora dos limites |

### 13.4 Anomalia Magnetica: **ALTO** (formacoes ferriferas)

### 13.5 Pesquisas Possiveis

- Geomorfologia de quartzito
- Campos rupestres
- Paisagem de mineracao historica

### 13.6 Valor Cientifico: **ALTO**

---

## 14. Serra de Ouro Branco

### 14.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°30'S, 43°42'W |
| **Area** | 7.520 ha |
| **Distancia de BH** | ~100 km sul |
| **Status** | Parque Estadual (Decreto 45.180/2009) — IEF-MG |
| **Municipios** | Ouro Branco, Ouro Preto |

### 14.2 Espaco Aereo: **BAIXO** (~60 km de SBBH)

### 14.3 Onde Pode Voar

| Local | Pode voar? | Observacao |
|---|---|---|
| **Dentro do parque** | NAO | Autorizacao IEF |
| **Areas rurais norte/sul ao longo BR-356 e BR-482** | **SIM** | ~20°32'S, 43°41'W |
| **Arredores de Ouro Branco (cidade)** | **SIM** | Regras padrao |

### 14.4 Anomalia Magnetica: **MODERADO** (quartzito dominante, algum ferro)

### 14.5 Pesquisas Possiveis

- Campos rupestres com alto endemismo (Cadeia do Espinhaco)
- 19 especies de pequenos mamiferos documentadas
- Geologia do Espinhaco

### 14.6 Valor Cientifico: **ALTO**

---

## 15. Serra da Canastra

### 15.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°15'S, 46°30'W |
| **Distancia de BH** | ~320 km (4-5h de carro) |
| **Status** | Parque Nacional — ICMBio |
| **Destaque** | Nascente do Rio Sao Francisco |

### 15.2 Espaco Aereo: **BAIXO** (aeroporto mais proximo: Passos MG, ~160 km)

### 15.3 Onde Pode Voar

| Local | Pode voar? | Observacao |
|---|---|---|
| **Dentro do parque** | NAO | SISBIO necessario |
| **Areas rurais ao redor de Sao Roque de Minas** | **SIM** | ~20°14'S, 46°22'W |

### 15.4 Anomalia Magnetica: **BAIXO** (quartzito/xisto, sem ferro significativo)

### 15.5 Pesquisas Possiveis

- Mapeamento hidrologico (nascente do Sao Francisco)
- Cerrado e campos rupestres
- Mapeamento de paisagem em grande escala

### 15.6 Valor Cientifico: **MUITO ALTO**

Significancia hidrologica nacional. Porem, distancia de BH exige expedicoes dedicadas.

---

## 16. EE Fechos

### 16.1 Dados Gerais

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°03'S, 43°57'W |
| **Area** | 602.95 ha |
| **Distancia de BH** | ~15 km sul (Nova Lima) |
| **Status** | Estacao Ecologica (Protecao Integral) — IEF/Copasa |
| **Criacao** | 1994 |

### 16.2 Espaco Aereo: **MEDIO** (~12 km de SBBH)

### 16.3 Onde Pode Voar

**DENTRO: NAO** — Estacao Ecologica e fechada ao publico. Praticamente impossivel obter autorizacao para drone exceto pesquisa aprovada.

**Entorno (APA Sul RMBH): SIM** — Areas ao redor na APA Sul.

### 16.4 Destaques

- 15 nascentes, 432 ha de Mata Atlantica/Cerrado
- Encosta NE da Serra da Moeda
- Area politicamente sensivel (expansao aprovada pela assembleia mas vetada pelo governador)

### 16.5 Valor Cientifico: **ALTO** (mas acesso quase impossivel)

---

## 17. Areas Adicionais

### 17.1 Parque Estadual do Sumidouro

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~19°32'S, 43°56'W |
| **Status** | Parque Estadual — IEF |
| **Espaco aereo** | **MUITO ALTO** (proximo a SBCF) |
| **Interesse** | Arqueologico/paleontologico (Peter Lund) |
| **Veredicto** | Melhor acessar pelo lado de Matozinhos |

### 17.2 Serra do Espinhaco (Ampla)

| Item | Detalhe |
|---|---|
| **Extensao** | Do QF ate Diamantina e alem |
| **Areas rurais** | Multiplas, com baixa restricao aerea |
| **Conceicao do Mato Dentro** | ~19°02'S, 43°25'W — ~100 km de BH, baixo risco aereo |
| **Interesse** | Mineracao Anglo American, campos rupestres |

### 17.3 Parque Estadual do Rio Preto

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~18°07'S, 43°20'W |
| **Distancia de BH** | ~150 km norte |
| **Status** | Parque Estadual — IEF |
| **Espaco aereo** | **BAIXO** |
| **Interesse** | Cerrado, campos rupestres |

### 17.4 Area da Comunidade de Casa Branca (Brumadinho)

| Item | Detalhe |
|---|---|
| **Coordenadas** | ~20°05'S, 44°15'W |
| **Status** | Sem UC restritiva |
| **Espaco aereo** | **BAIXO** |
| **Interesse** | Rural, corregos, terreno pouco perturbado ao norte de Inhotim |
| **Veredicto** | **Excelente para voos livres** |

---

## 18. Tabela Comparativa Geral

| # | Area | Dist. BH | Espaco Aereo | Autorizacao UC | Anomalia Mag. | Valor Cientifico | Voo Livre? |
|---|---|---|---|---|---|---|---|
| 1 | **Serra do Cipo (APA)** | 100 km | BAIXO | Nao (APA) | Baixo | Muito Alto | **SIM** |
| 2 | **Brumadinho / Paraopeba** | 60 km | BAIXO | Nao (APA Sul) | Alto | Alto | **SIM** |
| 3 | **Inhotim (dentro)** | 60 km | BAIXO | Sim (privado) | Alto | Alto | NAO (pedir) |
| 4 | **Serra da Piedade (fora)** | 50 km | BAIXO-MEDIO | Sim (Monumento) | **Muito Alto** | Muito Alto | Entorno SIM |
| 5 | **Serra do Gandarela (fora)** | 40-60 km | BAIXO | Sim (PN) | Alto | Muito Alto | Buffer SIM |
| 6 | **Serra do Curral** | 5-10 km | **MUITO ALTO** | Varia | Mod-Alto | Alto | Muito dificil |
| 7 | **Lagoa Santa (centro)** | 30 km | **MUITO ALTO** | Varia | Baixo | Muito Alto | Bordas apenas |
| 8 | **Serra da Moeda** | 40-50 km | BAIXO-MEDIO | Nao (APA Sul) | Alto | Muito Alto | **SIM** |
| 9 | **Serra do Rola-Moca (fora)** | 15-20 km | MEDIO | Sim (PE) | Alto | Muito Alto | Entorno SIM |
| 10 | **Quadrilatero Ferrifero** | 0-100 km | Variavel | Variavel | **Alto** | Muito Alto | Areas rurais |
| 11 | **Rio das Velhas (Rio Acima)** | 30 km | BAIXO | Nao | Variavel | Muito Alto | **SIM** |
| 12 | **Serra do Caraca (fora)** | 120 km | BAIXO | Sim (RPPN) | Mod-Alto | Alto | Entorno SIM |
| 13 | **Itacolomi (fora)** | 100 km | BAIXO | Sim (PE) | Alto | Alto | Entorno SIM |
| 14 | **Serra Ouro Branco (fora)** | 100 km | BAIXO | Sim (PE) | Moderado | Alto | Entorno SIM |
| 15 | **Serra da Canastra (fora)** | 320 km | BAIXO | Sim (PN) | Baixo | Muito Alto | Entorno SIM |
| 16 | **EE Fechos** | 15 km | MEDIO | Sim (EE) | Mod-Alto | Alto | Impossivel |
| 17 | **Lavras Novas (Ouro Preto)** | 100 km | BAIXO | Nao | Alto | Alto | **SIM** |
| 18 | **Funilandia (carste)** | 50 km | BAIXO | Nao | Baixo | Alto | **SIM** |
| 19 | **Casa Branca (Brumadinho)** | 65 km | BAIXO | Nao | Alto | Medio | **SIM** |

---

## 19. Ranking de Viabilidade Para Voo

### Tier 1: Voo Livre, Sem Burocracia, Alto Valor Cientifico

| # | Area | Coordenadas de Lancamento | Por Que |
|---|---|---|---|
| 1 | **Lapinha da Serra (Serra do Cipo APA)** | 19°07'S, 43°40'W | Campos rupestres, espaco aereo livre, sem ferro, sem UC restritiva |
| 2 | **Serra da Moeda / Topo do Mundo** | 20°05'S, 43°57'W | Geologia espetacular, espaco aereo favoravel, acesso facil. CUIDADO: anomalia magnetica |
| 3 | **Rio das Velhas em Rio Acima** | 20°05'S, 43°47'W | Monitoramento hidrico, acesso MG-030, espaco aereo livre |
| 4 | **Rio Paraopeba (Brumadinho)** | 20°10'S, 44°07'W | Impacto pos-barragem, alta publicabilidade, espaco aereo livre |
| 5 | **Lavras Novas (Ouro Preto)** | 20°28'S, 43°28'W | Rural, geologicamente rico, sem restricoes |

### Tier 2: Voo Possivel com Cuidados, Alto Valor Cientifico

| # | Area | Desafio | Solucao |
|---|---|---|---|
| 6 | Entorno da Serra do Gandarela (Rio Acima, Itabirito) | Proximo ao PN | Ficar fora dos limites do parque |
| 7 | Entorno da Serra da Piedade (Caete) | Monumento Natural + ferro | Voar fora do monumento, calibrar bussola |
| 8 | Serra de Ouro Branco (entorno) | Parque Estadual | Voar nas areas rurais ao redor |
| 9 | Raposos (Rio das Velhas) | ~18 km de SBBH | Verificar SARPAS, voar cedo |
| 10 | Matozinhos (carste) | ~15 km de SBCF | Verificar SARPAS |

### Tier 3: Voo Dificil, Requer Autorizacao Especifica

| # | Area | Desafio Principal |
|---|---|---|
| 11 | Serra do Rola-Moca | Parque Estadual (IEF) + proximidade SBBH |
| 12 | Serra do Cipo (PARNA) | SISBIO + ICMBio (31-60 dias uteis) |
| 13 | Serra do Gandarela (PARNA) | SISBIO + ICMBio |
| 14 | Serra do Caraca (RPPN) | Autorizacao dos Lazaristas |
| 15 | Inhotim (dentro) | Autorizacao do Instituto |

### Tier 4: Voo Muito Dificil ou Inviavel

| # | Area | Problema |
|---|---|---|
| 16 | Serra do Curral | Espaco aereo CTR-BH + patrimonio + mineracao |
| 17 | Lagoa Santa (centro) | SBCF + SBLS = proibitivo |
| 18 | EE Fechos | Estacao Ecologica fechada |
| 19 | Area da Barragem B1 (Brumadinho) | Infraestrutura critica + NOTAMs + Vale S.A. |
| 20 | Trecho urbano Rio das Velhas (BH) | CTR-BH + area urbana densa |

---

## 20. Recomendacoes Finais

### 20.1 Para Comecar Imediatamente (Sem Burocracia)

1. **Lapinha da Serra** — melhor custo-beneficio global. Campos rupestres equivalentes ao interior do PARNA, zero burocracia, zero risco de espaco aereo, zero anomalia magnetica.

2. **Serra da Moeda / Topo do Mundo** — geologia dramatica, facil acesso. Exige cuidado com anomalia magnetica (calibrar longe de ferro) e parapentes no Topo do Mundo.

3. **Rio das Velhas em Rio Acima** — aplicacao pratica imediata em monitoramento hidrico. Acesso pela MG-030.

### 20.2 Para Publicacao Rapida

**Rio Paraopeba pos-Brumadinho** — tema urgente, alta visibilidade, muitas revistas de impacto publicam sobre o desastre. Monitoramento de recuperacao ambiental com drone de baixo custo e altamente publicavel.

### 20.3 Para Maior Impacto Cientifico

**Serra do Cipo (APA, nao PARNA)** + **deep learning para classificacao de campos rupestres**. Gap claro na literatura: ninguem fez deteccao de mudancas automatizada com IA nesta vegetacao.

### 20.4 Cronograma Sugerido

| Mes | Acao |
|---|---|
| **Abril 2026** | Testar pipeline completo em area proxima a BH. Comprar Litchi |
| **Maio 2026** | 1a campanha: Lapinha da Serra (2-3 dias) + Rio Acima (1 dia) |
| **Maio 2026** | Submeter projeto SISBIO para PARNA Serra do Cipo |
| **Junho 2026** | Processar dados, treinar modelos IA, popular banco MySQL |
| **Julho 2026** | 2a campanha: Serra da Moeda + Brumadinho/Paraopeba |
| **Agosto 2026** | 3a campanha: Lapinha (repetir para deteccao de mudancas) |
| **Set-Out 2026** | Se SISBIO aprovado: 1a campanha dentro do PARNA |
| **Nov-Dez 2026** | Analise, escrita de artigo |

### 20.5 Checklist Antes de Cada Voo

- [ ] Verificar NOTAMs no AISWEB (https://aisweb.decea.mil.br/)
- [ ] Verificar SARPAS NG (https://servicos.decea.mil.br/sarpas/)
- [ ] Verificar zonas DJI GEO no app DJI Fly
- [ ] Confirmar limites de UC no QField/celular com GeoJSON carregados
- [ ] Calibrar bussola do drone no local, longe de ferro/metal
- [ ] Verificar previsao do tempo (vento < 20 km/h)
- [ ] Confirmar bateria padrao (248g, nao Plus) para isencao ANAC
- [ ] Carregar todas as baterias
- [ ] Formatar cartao SD (V30+)
- [ ] Levar documentos pessoais
