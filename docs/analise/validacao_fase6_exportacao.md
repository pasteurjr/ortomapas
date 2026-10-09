# Validação da Fase 6: exportação da missão

Foi validada uma missão real persistida no PostgreSQL (`id=22`, cinco waypoints) por chamadas autenticadas ao backend local.

| Formato | Endpoint | HTTP | Conteúdo conferido |
|---|---|---:|---|
| KML | `/api/missoes-captura/22/exportar?formato=kml` | 200 | XML KML com cinco placemarks e uma LineString de rota. |
| GeoJSON | `/api/missoes-captura/22/exportar?formato=geojson` | 200 | FeatureCollection com cinco pontos e uma linha, em EPSG:4326. |
| CSV | `/api/missoes-captura/22/exportar?formato=csv` | 200 | Cabeçalho e cinco linhas com ordem, coordenadas, altitude, velocidade, gimbal e rumo. |
| Litchi CSV | `/api/missoes-captura/22/exportar?formato=litchi_csv` | 200 | 18 colunas do formato Litchi, cinco waypoints, ação `Take Photo` e intervalo de distância. |

Também foi corrigida uma falha encontrada durante o teste: as coordenadas dos waypoints são armazenadas em `missoes_waypoints.geometria` (PostGIS), e não em colunas latitude/longitude. O exportador passou a extrair as coordenadas com `ST_X`/`ST_Y`.

## Interface

O planejador agora apresenta o botão **Exportar**. Ele baixa o KML da missão autenticada para abrir no Google Earth ou em uma ferramenta de planejamento. GeoJSON e CSV permanecem disponíveis pela API para os adaptadores específicos de aplicativos de voo.

## Limite conhecido

O CSV canônico continua disponível para integrações próprias. Para uso no Mission Hub, o adaptador Litchi abaixo gera um CSV com as colunas específicas do formato.

## Adaptador Litchi

O adaptador específico já foi implementado nesta fase. Ele produz as colunas de waypoint descritas no formato CSV do Litchi, incluindo `altitude(m)`, `heading(deg)`, `gimbalmode`, `gimbalpitchangle`, `actiontype1`, `actionparam1`, `speed(m/s)` e `photo_distinterval`. O arquivo foi validado estruturalmente com `csv.reader` e contém cinco linhas de waypoint.

O Mission Hub aceita CSV, KML e arquivos de missão, mas parâmetros globais como modo de heading, ação final e velocidade de cruzeiro não são preservados no CSV e devem ser revisados após a importação. Referências: [ajuda oficial do Litchi](https://flylitchi.com/help) e [descrição das colunas CSV](https://www.litchiutilities.com/docs/litchiCsv.php).
