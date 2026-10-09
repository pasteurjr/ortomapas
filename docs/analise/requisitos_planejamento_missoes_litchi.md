# Requisitos - Planejamento de Missoes de Captura para Litchi e Alternativas

**Produto:** Ortomapas  
**Versao:** 1.0  
**Data:** 2026-10-07  
**Status:** especificacao para implementacao  
**Escopo:** gerar, validar, versionar e exportar missoes de captura fotografica por drone para uso no Litchi/Litchi Pilot, Dronelink e Map Pilot Pro, alimentando posteriormente o fluxo WebODM/NodeODM.

## 1. Objetivo

O Ortomapas deve oferecer uma interface baseada em mapas para que o operador desenhe uma area de interesse, configure os parametros fotogrametricos e gere uma missao de voo composta por linhas, waypoints e comandos de captura. A missao deve ser revisada no mapa, validada contra restricoes de seguranca e exportada em um pacote que possa ser importado no Litchi Mission Hub e sincronizado com o Litchi/Litchi Pilot.

O resultado da missao e a aquisicao controlada de fotografias georreferenciadas, com sobreposicao, GSD e consistencia de camera suficientes para gerar ortomosaico, DSM/DTM, nuvem de pontos e relatorio no ODM.

O sistema nao assume controle direto do drone. Ele planeja e exporta a missao; a autorizacao final, o pre-voo e a execucao continuam sendo responsabilidade do operador no aplicativo de voo.

## 2. Referencias e premissas

- A documentacao oficial do Litchi descreve importacao no Mission Hub em CSV, KML e arquivo de missao Litchi, alem de exportacao CSV e KML 3D Path.
- O Litchi oferece altitude relativa ao ponto de decolagem e modo Above Ground quando ha dados de elevacao.
- O Litchi permite Heading Mode, Finish Action, Path Mode, Cruising Speed, Max Flight Speed, Photo Capture Interval, gimbal pitch e ate 15 acoes por waypoint.
- Acoes de waypoint dependentes da chegada ao ponto nao devem ser usadas com Path Mode = Curved Turns. Para fotogrametria, o padrao deve ser Straight Lines.
- O formato canonico interno sera independente do formato Litchi. Um adaptador versionado sera responsavel por exportar o CSV/arquivo compativel e declarar qualquer perda de informacao.
- Dronelink declara suporte ao DJI Mini 3, Mini 3 Pro e Mini 2, com missoes de mapeamento, waypoints e orbitas. Exige conta e plano ativo para criar e executar missoes.
- Map Pilot Pro declara suporte a serie Mini 3 por uma variante Android/Enterprise do aplicativo e requer controle compativel, como RC-N1 ou RC Pro; o DJI RC com tela integrada e iOS nao devem ser considerados no primeiro incremento.
- A operacao no Brasil continua condicionada as regras aplicaveis da ANAC, DECEA, SARPAS, fabricante, local e tipo de operacao. O exportador nao concede autorizacao de voo.

Referencias externas:

- Litchi Help: https://flylitchi.com/help
- Litchi Help (documentacao detalhada): https://docs.flylitchi.com/help
- ANAC RBAC-E 94: https://www.anac.gov.br/assuntos/legislacao/legislacao-1/boletim-de-pessoal/2023/bps-v-18-no-14-03-a-06-04-2023/rbac-e-94/visualizar_ato_normativo

## 3. Atores e integracoes

| Ator ou sistema | Responsabilidade |
|---|---|
| Operador de drone | Define a area, revisa parametros, executa checklist e inicia/interrompe a missao no Litchi. |
| Revisor tecnico | Confere GSD, sobreposicao, altitude, cobertura, autonomia e autorizacoes. |
| Administrador | Mantem perfis de drone/camera, limites operacionais, usuarios e auditoria. |
| Ortomapas | Gera, valida, versiona e exporta a missao; vincula a um projeto e a um voo. |
| Litchi Mission Hub | Importa a missao, permite revisar no mapa e sincroniza com dispositivos autenticados. |
| Litchi/Litchi Pilot | Executa a missao e registra telemetria, imagens e eventos de voo. |
| Dronelink | Alternativa de planejamento e execucao para Mini 3, sujeita a conta, plano e compatibilidade de dispositivo. |
| Map Pilot Pro | Alternativa especializada em mapeamento, com variante Android para a serie Mini 3. |
| WebODM/NodeODM | Processa as imagens e gera ortomosaico, DSM, DTM, nuvem de pontos e relatorio. |
| DEM/servico de elevacao | Fornece elevacao do terreno para altitude AGL e seguimento de terreno. |
| GIS/MapServer | Fornece mapas base, camadas cadastrais, areas restritas e geometrias de referencia. |

## 4. Conceitos do dominio

- **Projeto:** unidade de trabalho do usuario, com area, voos, produtos e permissoes.
- **Missao de captura:** uma versao executavel do planejamento, vinculada a um projeto.
- **Area de interesse (AOI):** poligono que define a cobertura desejada.
- **Zona de exclusao:** poligono ou circulo que nao pode ser sobrevoado.
- **Bloco de voo:** conjunto de linhas paralelas, waypoints e parametros homogeneos.
- **Waypoint:** ponto com latitude, longitude, altitude, rumo, velocidade, gimbal e acoes.
- **Perfil de drone/camera:** parametros fisicos usados no calculo de GSD, enquadramento e intervalo.
- **Execucao:** ocorrencia real da missao, com operador, horario, logs, imagens e resultado.
- **Pacote de exportacao:** arquivos da missao, manifesto, checklist e relatorio de validacao.

## 5. Fluxo principal

1. Usuario cria ou seleciona um projeto.
2. Usuario cria uma missao e informa ponto de decolagem, drone e camera.
3. Usuario desenha/importa a AOI e, se necessario, zonas de exclusao e pontos de interesse.
4. Usuario escolhe o tipo de cobertura: grid, double-grid, corredor, fachada, orbita ou waypoints manuais.
5. Sistema calcula altitude, GSD, espacamento de linhas, distancia entre fotos, numero de imagens, tempo e baterias.
6. Sistema mostra a rota no mapa, perfil de elevacao, cobertura, estimativa de fotos e alertas.
7. Usuario ajusta parametros ou confirma a versao.
8. Sistema executa validacoes geometricas, fotogrametricas, de autonomia e de seguranca.
9. Usuario exporta CSV Litchi e os arquivos auxiliares KML/GeoJSON/JSON, com checklist.
10. Operador importa no Mission Hub, confere o pre-flight report e sincroniza com o dispositivo.
11. Apos o voo, operador importa fotos e logs; o Ortomapas vincula a execucao e inicia o fluxo ODM.

## 6. Requisitos da interface baseada em mapa

### 6.1 Mapa e camadas

**RF-MAP-001.** Exibir mapa base com alternancia entre rua, satelite, terreno e camada GIS configurada.

**RF-MAP-002.** Permitir zoom, pan, centralizacao na AOI, escala grafica, norte, coordenadas e unidade de distancia.

**RF-MAP-003.** Permitir desenhar, editar, mover, simplificar e excluir um poligono AOI. O poligono deve fechar e mostrar area e perimetro.

**RF-MAP-004.** Permitir importar KML/KMZ, GeoJSON e Shapefile zipado como AOI, zona de exclusao, linha de corredor ou ponto de interesse. O sistema deve reprojetar para WGS84 e preservar a geometria original.

**RF-MAP-005.** Permitir criar zonas de exclusao, buffers de seguranca, pontos de decolagem, pontos de pouso alternativo e pontos de interesse.

**RF-MAP-006.** Exibir linhas de voo, setas de direcao, numero dos waypoints, pontos de captura, ponto inicial/final, RTH e trechos fora da AOI.

**RF-MAP-007.** Exibir sobreposicao da rota com zonas restritas, relevo, vias, edificacoes e camadas de referencia quando disponiveis.

**RF-MAP-008.** Permitir desfazer/refazer e registrar cada alteracao na versao da missao.

### 6.1.1 Paridade de interacao com o Litchi Hub

O editor do Ortomapas deve adotar o mesmo modelo mental de interacao do Litchi Hub: mapa como area de trabalho principal, ferramentas de desenho visiveis, selecao direta dos pontos e painel lateral para parametros. A paridade desejada e funcional, nao uma copia de codigo ou de identidade visual.

**RF-HUB-001.** Oferecer ferramenta de poligono para desenhar a AOI clicando em vertices e fechando no primeiro ponto.

**RF-HUB-002.** Oferecer ferramenta de linha para desenhar corredor, rota manual ou eixo de inspeccao.

**RF-HUB-003.** Permitir selecionar, arrastar, inserir antes/depois, duplicar e excluir waypoints diretamente no mapa.

**RF-HUB-004.** Mostrar numeracao, sentido por setas e destaque do waypoint selecionado.

**RF-HUB-005.** Oferecer painel de edicao individual e edicao em lote para altitude, velocidade, rumo, gimbal, intervalo e acoes.

**RF-HUB-006.** Oferecer ferramentas de mover, girar, escalar, inverter sentido, centralizar e limpar a missao.

**RF-HUB-007.** Permitir importar uma geometria existente, editar sobre ela e salvar como nova versao sem alterar a versao executada.

**RF-HUB-008.** Exibir informacoes da missao no proprio mapa: distancia, tempo, area, quantidade de waypoints, fotos, blocos e alertas.

**RF-HUB-009.** Permitir travar a missao para revisao e exigir desbloqueio explicito antes de editar.

**RF-HUB-010.** Oferecer modo de simulacao com reproducao da rota, pausa, avanco e selecao de um waypoint inicial.

**RF-HUB-011.** Manter atalhos de teclado e botoes com icones para desfazer, refazer, salvar, importar, exportar, selecionar tudo e apagar, com tooltip acessivel.

**RF-HUB-012.** Nao esconder erros de validacao em modal. Exibir lista lateral clicavel que centraliza o mapa na geometria do problema.

### 6.2 Geracao de cobertura

**RF-GRID-001.** Gerar grid paralela cobrindo a AOI com orientacao definida pelo usuario ou calculada para reduzir o comprimento total.

**RF-GRID-002.** Gerar double-grid com segunda passada rotacionada, quando o objetivo for melhorar geometria 3D.

**RF-GRID-003.** Gerar corredor a partir de linha ou poligono estreito, com largura lateral configuravel.

**RF-GRID-004.** Gerar orbita, fachada e missao de waypoints manuais como modos distintos, sem misturar parametros silenciosamente.

**RF-GRID-005.** Recortar linhas na AOI, inserir margem de entrada/saida e respeitar zonas de exclusao.

**RF-GRID-006.** Dividir a missao em baterias ou blocos quando o tempo/distancia exceder os limites definidos.

**RF-GRID-007.** Permitir reordenar blocos e definir ponto de inicio, sentido, alternancia de linhas e retorno entre blocos.

**RF-GRID-008.** Mostrar antes da confirmacao: area coberta, numero de linhas, waypoints, fotos estimadas, distancia, tempo, baterias e GSD.

## 7. Parametros de captura

### 7.1 Identificacao e referencia espacial

| Campo | Obrigatorio | Regra |
|---|---:|---|
| Nome da missao | Sim | Unico no projeto; incluir local, data planejada e versao. |
| Projeto | Sim | Deve existir e o usuario deve ter permissao de edicao. |
| Operador e revisor | Sim | Identidade persistida para auditoria. |
| Drone e camera | Sim | Selecionados de perfis cadastrados. |
| CRS de armazenamento | Sim | WGS84/EPSG:4326 para exportacao Litchi. |
| Unidade | Sim | Metros, m/s e graus; decimal com ponto no arquivo. |
| Ponto de decolagem/home | Sim | Latitude, longitude, altitude e fonte. |
| Referencia de altitude | Sim | AGL, relativo ao takeoff ou AMSL; nunca omitir. |
| Data/janela de voo | Recomendado | Usada para checklist, luz e autorizacoes. |

### 7.2 Perfil de camera

O perfil deve conter sensor (largura/altura em mm), resolucao (px), pixel pitch se conhecido, distancia focal real e equivalente, abertura, formato, obturador, ISO, foco, estabilizacao, modo de disparo, intervalo minimo da camera, tamanho medio de arquivo, GPS/RTK e modelo/firmware.

Configuracao recomendada para ortomapeamento:

- foto e nao video;
- JPEG ou JPEG+RAW conforme armazenamento e processamento;
- maior resolucao suportada pelo sensor;
- foco travado apos foco de teste;
- ISO baixo e obturador suficiente para evitar arrasto;
- balanco de branco fixo;
- exposicao consistente entre linhas;
- gimbal em -90 graus para grid nadir;
- horario e iluminacao registrados no voo.

### 7.3 Parametros fotogrametricos

| Parametro | Regra/recomendacao |
|---|---|
| GSD alvo | Entrada principal; o sistema calcula altitude ou informa conflito com altitude definida. |
| Sobreposicao frontal | Faixa configuravel; valor inicial recomendado 75-80%. |
| Sobreposicao lateral | Faixa configuravel; valor inicial recomendado 70-75%. |
| Altitude AGL | Preferida quando ha DEM; limitar por regulamentacao e obstaculos. |
| Altitude relativa ao takeoff | Usada quando nao ha DEM; alertar em terreno inclinado. |
| Orientacao das linhas | Manual ou otimizada para minimizar distancia e vento cruzado. |
| Velocidade | Deve respeitar limite da camera e permitir obturador sem motion blur. |
| Intervalo de foto | Em segundos ou metros; calcular para cumprir a sobreposicao frontal. |
| Espacamento entre linhas | Calcular pela largura do footprint e sobreposicao lateral. |
| Gimbal | Nadir para ortomosaico; obliquo somente em modo especifico. |
| Double-grid | Opcional para reconstrucoes 3D e areas com pouca textura. |
| Seguimento de terreno | Requer DEM, limite de variacao, densidade de amostras e plano de contingencia. |
| GCP/RTK/PPK | Registrar uso, sistema de referencia, pontos e qualidade; nao presumir precisao. |

Calculos minimos:

```text
GSD = (H * sensor_largura) / (focal_real * largura_imagem)
H = (GSD_alvo * focal_real * largura_imagem) / sensor_largura
footprint_largura = GSD * largura_imagem
footprint_comprimento = GSD * altura_imagem
espacamento_linhas = footprint_largura * (1 - overlap_lateral)
distancia_fotos = footprint_comprimento * (1 - overlap_frontal)
intervalo_segundos = distancia_fotos / velocidade
```

O sistema deve aplicar uma margem de seguranca ao intervalo para considerar latencia do disparo, velocidade real, curva e limite minimo da camera. Valores impossiveis devem bloquear a exportacao, nao apenas gerar um aviso.

### 7.4 Parametros de missao Litchi

O adaptador deve expor e documentar:

- Heading Mode: Toward next Waypoint, Initial Direction, User Controlled ou Waypoint Defined;
- Finish Action: None, Go Home, Land, Back to First Waypoint ou Reverse, conforme suporte da versao;
- Path Mode: Straight Lines ou Curved Turns;
- Cruising Speed e Max Flight Speed;
- Default Gimbal Pitch e rotacao gerenciada;
- Photo Capture Interval global e por trecho;
- altitude por waypoint, velocidade por trecho, curva, rumo e POI;
- acoes por waypoint: Stay, Take Photo, Start Recording, Stop Recording, Rotate Aircraft e Tilt Camera, somente quando suportadas;
- RTH e comportamento em perda de sinal;
- limite de waypoints e limite de distancia da versao alvo do aplicativo.

Para mapeamento, o preset padrao deve usar Straight Lines, gimbal -90 graus, heading alinhado ao deslocamento e captura por intervalo. A captura explicita Take Photo em cada waypoint e uma alternativa; se usada, deve haver pausa suficiente e o modo de caminho deve ser Straight Lines.

## 8. Seguranca e conformidade

**RF-SAFE-001.** Bloquear exportacao se houver intersecao nao autorizada com zona de exclusao.

**RF-SAFE-002.** Verificar altitude maxima configurada, distancia maxima, raio de operacao, obstaculos, margem vertical e referencia AGL/AMSL.

**RF-SAFE-003.** Estimar duracao por bloco e exigir reserva de bateria configuravel. A missao deve considerar subida, deslocamento ate a area, linhas, retornos, vento e RTH.

**RF-SAFE-004.** Exigir ponto Home valido e altitude de RTH acima do maior obstaculo conhecido mais a margem.

**RF-SAFE-005.** Registrar clima, vento maximo aceitavel, chuva, visibilidade, iluminacao e criterio de abortar.

**RF-SAFE-006.** Exibir checklist de autorizacao local, ANAC/DECEA/SARPAS quando aplicavel, privacidade, terceiros, VLOS/BVLOS e restricoes ambientais.

**RF-SAFE-007.** O usuario deve confirmar que revisou a missao no Litchi antes de iniciar; essa confirmacao fica na auditoria.

**RF-SAFE-008.** Rejeitar missao sem operador, revisor quando exigido, versao, perfil de drone/camera ou manifesto.

## 9. Validacoes obrigatorias

### Erros que bloqueiam a exportacao

- AOI ausente, aberta, invalida ou com area zero;
- ponto de decolagem ausente ou fora do contexto permitido;
- waypoint sem altitude, coordenada WGS84 valida ou ordem deterministica;
- rota cruzando zona de exclusao;
- altitude abaixo da margem de obstaculo ou acima do limite configurado;
- GSD, overlap, intervalo ou espacamento fora das faixas do perfil;
- tempo estimado acima da autonomia menos reserva;
- modo Curved Turns combinado com acoes que exigem chegada ao waypoint;
- quantidade de waypoints ou distancia entre pontos fora do limite do adaptador;
- ausencia de autorizacao requerida no checklist.

### Avisos que exigem justificativa

- relevo sem DEM para uma area inclinada;
- sobreposicao abaixo do preset recomendado;
- vento cruzado acima do valor nominal;
- foto estimada acima do armazenamento disponivel;
- camera sem RTK/GCP em requisito de acuracia absoluta;
- exportacao que nao preserva alguma acao no formato alvo;
- linhas muito curtas para estabilizacao ou curvas apertadas;
- cobertura parcial por exclusoes ou borda da AOI.

## 10. Casos de uso

### UC-PLN-001 - Criar missao a partir de uma AOI

**Pre-condicoes:** usuario autenticado, projeto editavel e mapa disponivel.  
**Fluxo:** selecionar projeto; criar missao; desenhar/importar AOI; definir takeoff; salvar rascunho.  
**Resultado:** missao com versao, geometria WGS84, autor e status `rascunho`.  
**Aceite:** recarregar a tela preserva geometria, area, perimetro e historico.

### UC-PLN-002 - Configurar camera e objetivo fotogrametrico

**Fluxo:** selecionar perfil; informar GSD, overlap, altitude, velocidade e gimbal; sistema calcula footprint, linha e intervalo.  
**Aceite:** os calculos exibem formula, unidade e alertas; alterar um campo atualiza a estimativa sem perder a AOI.

### UC-PLN-003 - Gerar e editar grid

**Fluxo:** escolher grid/double-grid/corredor; escolher orientacao; gerar linhas; excluir ou ajustar linhas; recalcular waypoints.  
**Aceite:** todas as linhas ficam visiveis, numeradas e recortadas pela AOI, respeitando exclusoes.

### UC-PLN-004 - Validar seguranca e autonomia

**Fluxo:** executar validacao; abrir cada erro/aviso no mapa; corrigir ou justificar; assinar revisao.  
**Aceite:** exportacao fica bloqueada para erro critico e o relatorio guarda a evidenca.

### UC-PLN-005 - Pre-visualizar a missao

**Fluxo:** reproduzir a rota; alternar camadas; visualizar perfil de elevacao, altitude AGL, fotos e baterias.  
**Aceite:** a simulacao mostra inicio, fim, sentido, RTH, trechos excluidos e estimativas coerentes.

### UC-PLN-006 - Exportar para Litchi

**Fluxo:** escolher perfil Litchi/Litchi Pilot e versao; gerar CSV e pacote auxiliar; baixar manifesto, KML/GeoJSON, checklist e relatorio.  
**Aceite:** arquivo usa WGS84, decimal com ponto, ordem de colunas do adaptador, nome versionado e checksum; o importador local valida o arquivo antes do download.

### UC-PLN-007 - Revisar no Mission Hub e sincronizar

**Fluxo externo documentado:** importar CSV no Mission Hub; conferir rota, altitude, intervalos, acoes, Path Mode e Finish Action; salvar e sincronizar.  
**Aceite Ortomapas:** checklist exige que o operador marque os itens conferidos e anexe captura ou observacao.

### UC-PLN-008 - Registrar execucao e importar dados

**Fluxo:** informar missao executada; importar fotos e logs; validar EXIF/GPS/horario; detectar ausencia ou duplicidade; vincular a execucao.  
**Aceite:** o projeto mostra contagem, hashes, intervalo temporal, cobertura estimada e pendencias.

### UC-PLN-009 - Enviar imagens ao ODM

**Fluxo:** selecionar execucao valida; criar tarefa NodeODM/WebODM; acompanhar progresso; importar ortomosaico, DSM, DTM, nuvem e relatorio.  
**Aceite:** produtos ficam vinculados a projeto, missao, execucao, parametros e versao do processamento.

### UC-PLN-010 - Versionar e replanejar

**Fluxo:** duplicar missao; alterar area/parametros; comparar versoes; apos aprovacao tornar uma versao executavel.  
**Aceite:** nunca sobrescrever uma missao ja exportada ou executada; manter diff de geometria e parametros.

## 11. Contratos de dados e persistencia

As tabelas devem ser implementadas no PostgreSQL/PostGIS do Ortomapas, sem criar um segundo banco para o planejador:

- `missoes_captura`: projeto, nome, status, versao, perfil, operador, revisor, CRS, takeoff, timestamps;
- `missoes_areas`: AOI, exclusoes, corredores, POIs e geometrias PostGIS;
- `missoes_parametros`: camera, GSD, overlap, altitude, velocidade, gimbal, intervalos e seguranca em JSONB versionado;
- `missoes_waypoints`: ordem, latitude, longitude, altitude, AGL, rumo, velocidade, curva, gimbal e acoes;
- `missoes_blocos`: divisao por bateria, estimativas e ordem de execucao;
- `missoes_validacoes`: regra, severidade, resultado, valor, mensagem, geometria e timestamp;
- `missoes_exportacoes`: formato, perfil, versao do adaptador, checksum, arquivo, manifesto e perda de informacao;
- `missoes_execucoes`: operador, janela, dispositivo, log, contagem de fotos, clima, status e observacoes;
- `missoes_fotos`: arquivo, hash, EXIF, coordenada, horario, camera, qualidade e vinculo ODM.

JSON canonico minimo:

```json
{
  "schema": "ortomapas.capture-mission/1.0",
  "mission_id": "uuid",
  "crs": "EPSG:4326",
  "takeoff": {"lat": 0.0, "lon": 0.0, "amsl_m": 0.0},
  "capture": {"gsd_cm_px": 1.5, "front_overlap": 0.8, "side_overlap": 0.7, "gimbal_deg": -90},
  "litchi": {"path_mode": "straight", "heading_mode": "toward_next", "finish_action": "rth"},
  "blocks": [{"id": "B01", "waypoints": []}],
  "validation": {"status": "passed", "ruleset": "1.0"}
}
```

O arquivo de voo nao deve ser montado diretamente pela interface. O backend deve gerar o pacote por adaptador, validar o formato, salvar checksum e indicar no manifesto quais propriedades nao sao representaveis no formato alvo. KML 3D deve ser exportado para inspeccao no Google Earth; GeoJSON deve ser exportado como formato GIS interoperavel.

### 12.1 Matriz de adaptadores

| Alvo | Entrada/saida do Ortomapas | Uso | Restricoes a validar |
|---|---|---|---|
| Litchi Hub/Litchi Pilot | CSV Litchi, KML 3D, JSON canonico e manifesto | Planejar no Hub e executar no Pilot | Android para Pilot; confirmar acoes, limites e versao. |
| Dronelink | JSON canonico + pacote de geometria/parametros conforme adaptador | Planejamento e voo de mapeamento | Conta/plano ativo; confirmar dispositivo e firmware do Mini 3. |
| Map Pilot Pro | JSON canonico + pacote de area/parametros conforme adaptador | Mapeamento especializado | APK variante Enterprise no Android; RC-N1/RC Pro; nao usar DJI RC integrado. |
| GIS/Google Earth | KML/KMZ e GeoJSON | Revisao, compartilhamento e conferencia | KML e referencia visual; nao presumir que seja executavel pelo aplicativo. |

O primeiro release deve implementar o adaptador Litchi e o pacote canonico. Dronelink e Map Pilot Pro entram como adaptadores subsequentes, depois de teste real com Mini 3, controle e firmware definidos.

## 12. API proposta

| Metodo | Endpoint | Funcao |
|---|---|---|
| POST | `/api/projetos/{id}/missoes-captura` | Criar rascunho |
| GET/PATCH | `/api/missoes-captura/{id}` | Consultar/editar versao |
| POST | `/api/missoes-captura/{id}/areas/import` | Importar KML/KMZ/GeoJSON |
| POST | `/api/missoes-captura/{id}/gerar-grid` | Gerar cobertura |
| POST | `/api/missoes-captura/{id}/validar` | Executar regras |
| GET | `/api/missoes-captura/{id}/preview` | Rota, perfil e estimativas |
| POST | `/api/missoes-captura/{id}/export/{alvo}` | Gerar pacote Litchi, Dronelink ou Map Pilot Pro |
| POST | `/api/missoes-captura/{id}/execucoes` | Registrar voo |
| POST | `/api/execucoes/{id}/fotos` | Importar manifesto/fotos |
| POST | `/api/execucoes/{id}/odm` | Disparar processamento ODM |

Todas as operacoes devem exigir autenticacao, autorizacao por projeto, idempotency key em geracao/exportacao e auditoria.

## 13. Pacote de exportacao

```text
<projeto>_<missao>_v<versao>_<data>/
  mission_litchi.csv
  mission_canonical.json
  area_of_interest.kml
  area_of_interest.geojson
  manifest.json
  validation_report.pdf
  operator_checklist.pdf
  README_IMPORT_LITCHI.md
```

O manifesto deve informar: id/versao, data, autor, drone/camera, CRS, takeoff, parametros, contagem de waypoints/fotos, checksum SHA-256 de cada arquivo, regras executadas, alertas, perda de informacao e instrucoes de revisao no Litchi.

## 14. Criterios de aceite do primeiro incremento

1. Criar projeto e missao com autenticacao e permissao por usuario.
2. Desenhar AOI no mapa e importar KML/KMZ/GeoJSON.
3. Cadastrar ou selecionar perfil DJI Mini 3 e camera correspondente.
4. Gerar grid nadir com GSD, overlap, espacamento, intervalo e autonomia calculados.
5. Mostrar rota, waypoints, fotos estimadas, baterias, perfil de elevacao e alertas.
6. Bloquear exportacao para intersecao de zona proibida, altitude invalida, autonomia insuficiente ou combinacao incompatível de acoes/path mode.
7. Exportar CSV Litchi, KML, GeoJSON, JSON canonico, manifesto e relatorio; deixar os alvos Dronelink e Map Pilot Pro disponiveis como adaptadores versionados apos homologacao.
8. Importar o CSV em um fixture do Mission Hub ou validar a estrutura contra fixture versionado, sem depender de rede no teste automatizado.
9. Registrar a revisao do operador e vincular a missao a uma execucao.
10. Importar fotos de teste, validar EXIF e disponibilizar a execucao para o fluxo NodeODM/WebODM.

## 15. Plano de testes minimo

| ID | Teste | Evidencia |
|---|---|---|
| T01 | AOI desenhada e fechada | Screenshot do mapa + area/perimetro |
| T02 | Importacao KML/KMZ/GeoJSON | Arquivo original + geometria reexibida |
| T03 | Grid calculada | Linhas, waypoints e parametros |
| T04 | Calculo de GSD e intervalo | Valores e formula no painel |
| T05 | Exclusao bloqueia rota | Regra vermelha e geometria destacada |
| T06 | Autonomia divide blocos | Baterias e tempos por bloco |
| T07 | Exportacao Litchi | CSV, checksum e manifesto |
| T08 | Round-trip | Importar CSV no fixture e comparar waypoints |
| T09 | Execucao/fotos | EXIF, hashes, contagem e mapa de cobertura |
| T10 | ODM | Tarefa, produtos e vinculos no projeto |
| T11 | Permissoes | Usuario sem acesso nao ve nem exporta missao |
| T12 | Versionamento | Diff e impossibilidade de sobrescrever versao executada |

Cada teste deve ser executado com Playwright quando houver interface, gerar screenshot nomeado e registrar resultado esperado/obtido. Testes de calculo e exportacao devem tambem rodar sem navegador para detectar regressao numerica.

## 16. Roadmap de implementacao

**Fase 1 - Modelo e perfis:** migrations PostGIS, perfis de drone/camera, JSON canonico, autenticacao e permissoes.  
**Fase 2 - Editor cartografico:** AOI, exclusoes, importacao/exportacao GIS, undo/redo e camadas.  
**Fase 3 - Motor fotogrametrico:** GSD, grid, double-grid, corredor, intervalos, autonomia e DEM.  
**Fase 4 - Validador:** regras de seguranca, compatibilidade dos alvos, relatorio e auditoria.  
**Fase 5 - Adaptador Litchi:** CSV, KML 3D, manifesto, checksum, fixtures e round-trip.  
**Fase 6 - Campo e ODM:** execucao, fotos/logs, cobertura, NodeODM/WebODM e produtos.  
**Fase 7 - Adaptadores alternativos:** Dronelink e Map Pilot Pro, com teste real do Mini 3, RC-N1/RC Pro e firmware suportado.  
**Fase 8 - Refinamento:** vento, previsao, RTK/GCP, comparacao de versoes e double-grid 3D.

## 17. Decisoes em aberto

- Confirmar a versao exata do Litchi/Litchi Pilot e o limite de waypoints aplicavel ao modelo de drone usado.
- Definir a fonte DEM licenciada e a politica de cache/offline.
- Definir se o primeiro release exige apenas nadir ou tambem missao obliqua/fachada.
- Definir limites de vento, reserva de bateria e altura maxima por perfil e por operacao.
- Definir se o campo aceitara somente CSV ou tambem importacao direta de arquivo de missao Litchi.
- Definir o procedimento de evidencia de autorizacao SARPAS/DECEA e documentos anexados.

## 18. Definicao de pronto

Esta especificacao sera considerada implementada quando um operador autenticado puder criar um projeto, desenhar uma AOI real, gerar uma missao fotogrametrica, corrigir todos os erros do validador, exportar o pacote Litchi, revisar a missao no Mission Hub, registrar a execucao e enviar as fotos ao fluxo ODM, com todas as geometrias, parametros, evidencias e versoes persistidos no PostgreSQL/PostGIS.
