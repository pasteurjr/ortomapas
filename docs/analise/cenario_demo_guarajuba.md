# Cenário real de demonstração: Condomínio Paraíso, Guarajuba

## Área

O cenário usa a região de Guarajuba, em Camaçari/BA, com referência aproximada à portaria do Condomínio Paraíso (`-12.6504521, -38.0714399`). A AOI de teste cobre aproximadamente `-12.6538,-38.0758` a `-12.6470,-38.0680`.

O polígono é uma área de demonstração, não um limite cadastral. Antes de qualquer voo ou medição oficial, deve ser substituído por um limite fornecido pelo proprietário ou por levantamento autorizado.

## Dados baixados

- `data/guarajuba_osm.osm`: recorte oficial da API OpenStreetMap para a área de teste.
- `data/guarajuba_osm_referencia.geojson`: 852 feições convertidas para referência visual, incluindo edificações, vias, áreas e a AOI aproximada.
- A base cartográfica exibida no navegador usa tiles OpenStreetMap; o uso deve respeitar a licença ODbL e a atribuição aos colaboradores.

## Uso no vídeo

1. Abrir o mapa na região de Guarajuba.
2. Mostrar a portaria e o entorno do Condomínio Paraíso.
3. Importar ou desenhar a AOI aproximada.
4. Gerar a missão de cobertura fotogramétrica.
5. Validar waypoints, espaçamentos, altitude, sobreposição e autonomia.
6. Exportar KML/GeoJSON/Litchi CSV.
7. Mostrar que a missão é uma simulação e não autoriza voo sem checagem de campo.

## Limitação de imagem aérea

OpenStreetMap fornece cartografia vetorial, não fotos capturadas pelo drone. Para demonstrar ortomosaico, DSM, DTM, nuvem de pontos e análises raster, é necessário adicionar um conjunto de imagens aéreas licenciado ou dados sintéticos explicitamente identificados como simulados. O roteiro deve separar claramente cartografia OSM, dados sintéticos e produtos reais do WebODM.
