# Validacao do NodeODM com dataset Aukerman

Data: 2026-09-11  
Projeto: Ortomapas

## Objetivo

Confirmar que o NodeODM instalado pelo `docker-compose.yml` aceita imagens reais de drone e produz produtos fotogrametricos, sem depender do visualizador do Ortomapas.

## Dataset

- Origem: repositorio oficial [OpenDroneMap/odm_data_aukerman](https://github.com/OpenDroneMap/odm_data_aukerman)
- Catalogo: [OpenDroneMap/ODMdata](https://github.com/OpenDroneMap/ODMdata)
- Conteudo: 77 imagens JPG com coordenadas EXIF
- Armazenamento local: `data/odm_test/odm_data_aukerman-master/images/`

## Execucao

- Endpoint: `http://127.0.0.1:8021`
- Tarefa: `ortomapas-aukerman-smoke`
- UUID: `94e7fce1-f092-4fb9-aaed-2cf664e07bdd`
- Opcoes: `resize-to=1200`, `fast-orthophoto=true`, `skip-3dmodel=true`
- Resultado NodeODM: status `40` (concluido), progresso `100%`
- Tempo informado pelo NodeODM: aproximadamente 4min14s

## Produtos verificados

- Ortofoto: `data/odm_test/results/odm_orthophoto/odm_orthophoto.tif`
  - 7.290 x 5.314 pixels, 4 bandas `uint8`
  - CRS `EPSG:32617`
  - tamanho aproximado: 49,5 MB
- Relatorio ODM: `data/odm_test/results/odm_report/report.pdf`
- Nuvem de pontos: `data/odm_test/results/odm_georeferencing/odm_georeferenced_model.laz`
- Limites vetoriais: GeoJSON e GPKG em `odm_georeferencing/`
- Pacote completo: `data/odm_test/aukerman-results.zip`

## Conclusao

O serviço NodeODM está funcional para processamento fotogramétrico real. O teste valida a infraestrutura WebODM/NodeODM e o banco PostgreSQL compartilhado, mas não valida integração automática com a aplicação Ortomapas: o código da aplicação ainda não chama a API ODM nem importa esses produtos para o visualizador.
