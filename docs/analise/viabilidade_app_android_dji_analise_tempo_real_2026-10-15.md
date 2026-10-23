# Viabilidade e especificacao: aplicativo Android de captura e analise para Ortomapas

- **Data:** 15/10/2026
- **Status:** estudo de viabilidade e requisitos propostos; nenhuma integracao DJI foi implementada ou testada em drone real.
- **Drone inicial:** DJI Mini 3 com controle DJI RC-N1 conectado a telefone/tablet Android. A combinacao exata de firmware, controle e telefone deve ser confirmada em bancada.

## 1. Decisao executiva

**E viavel criar um aplicativo Android proprio com o DJI Mobile SDK V5 para controlar camera, receber telemetria e video, executar uma missao e ligar a captura ao Ortomapas.** A DJI lista o Mini 3 entre os produtos suportados pelo SDK V5 e fornece bibliotecas e amostras Android. Suporte ao *produto* nao garante suporte a cada *funcao* em cada firmware; a execucao de waypoint nativo e a disponibilidade das fotos originais durante captura exigem prova no equipamento do usuario. [DJI Mobile SDK: produtos](https://developer.dji.com/mobile-sdk/), [introducao](https://developer.dji.com/doc/mobile-sdk-tutorial/en/basic-introduction/msdk-introduction.html), [amostra Android](https://developer.dji.com/doc/mobile-sdk-tutorial/en/quick-start/run-sample.html).

A primeira versao deve ser **Android nativo em Kotlin**, usando o SDK DJI e componentes Android para conexao USB, video, missao e armazenamento. O planejador web Ortomapas permanece como fonte da missao. React Native pode ser usado para telas compartilhadas somente depois de um modulo nativo robusto; nao reduz o risco principal, que esta nas APIs DJI, no ciclo de vida Android e no controle de voo. Java e tecnicamente possivel, mas Kotlin e a escolha natural para o aplicativo novo.

O diferencial do produto e fechar o ciclo **planejamento -> captura auditada -> QA em campo -> fotos verificadas -> ODM -> analise GIS/IA**. Para o Mini 3, a primeira entrega viavel e captura guiada com QA de video e sincronizacao confiavel; piloto automatico proprio depende dos testes fisicos descritos neste documento.

**Analise em tempo real** significa avaliar amostras do fluxo de video enquanto o drone voa: nitidez, exposicao, obstrucao, cena/objetos, estimativa de lacunas e alertas. O SDK permite receber quadros decodificados em formatos como RGBA/YUV para algoritmos locais. **Ortomosaico, DSM, DTM e nuvem de pontos definitivos** dependem das fotos originais, metadados e processamento fotogrametrico; nao devem ser prometidos como produto final em tempo real no Mini 3. [DJI: novos fluxos de video](https://developer.dji.com/doc/mobile-sdk-tutorial/en/tutorials/video-stream/video-stream2.html), [DJI: modos da camera](https://developer.dji.com/doc/mobile-sdk-tutorial/en/basic-introduction/basic-concepts/camera.html).

## 2. Graus de viabilidade

| Capacidade | Parecer | Condicao de aceite |
|---|---|---|
| Conectar Mini 3/RC-N1, registrar SDK, mostrar telemetria e video | Alta | Amostra DJI funcionando no conjunto fisico escolhido |
| Planejar grid, GSD, sobreposicao, baterias e zonas no Ortomapas | Ja existe em parte | Rever calculos e formato para o adaptador DJI |
| Capturar fotos a intervalos/distancias e registrar evento/posicao | Media/alta | Testar comandos da camera, latencia e intervalo no Mini 3 |
| Executar KMZ/WPML como missao embarcada no Mini 3 | **Nao comprovada** | Verificar suporte da API no produto e testar upload, start, pause, RTH e perda de link |
| Seguir rota por Virtual Stick quando waypoint embarcado nao existir | Viavel com risco maior | Controle a 5-25 Hz, watchdog, tomada manual, perda de link e ensaio de campo; nao e equivalente a missao embarcada |
| IA no celular sobre quadros de video | Alta para modelos leves | Benchmark de latencia, temperatura, bateria e falsos alertas no telefone alvo |
| IA no servidor sobre amostras enviadas pelo celular | Alta com rede disponivel | Fila, limites de banda, perda de rede e privacidade definidos |
| Receber **foto original a cada disparo enquanto segue fotografando** | Incerta e provavelmente limitada | Medir MediaManager no Mini 3; a DJI descreve modos de captura/download mutuamente exclusivos em sua documentacao geral |
| Ortomosaico/DSM/DTM/nuvem em tempo real durante voo | Baixa para este conjunto | Nao entra no MVP; processar fotos confirmadas apos pouso/pausa via NodeODM |

O SDK distingue missoes armazenadas/executadas pela aeronave das controladas continuamente no dispositivo. Uma missao de Virtual Stick depende da conexao e do processo Android; perda de link pode interrompe-la. O plano de seguranca deve refletir essa diferenca. [DJI: missoes](https://developer.dji.com/doc/mobile-sdk-tutorial/en/basic-introduction/basic-concepts/missions.html), [DJI: Virtual Stick](https://developer.dji.com/doc/mobile-sdk-tutorial/en/tutorials/virtual-stick.html), [DJI: waypoint KMZ](https://developer.dji.com/api-reference-v5/android-api/Components/IWaypointMissionManager/IWaypointMissionManager.html).

## 3. O que ja existe no Ortomapas

- `missoes_captura`, `missoes_areas`, `missoes_parametros`, `missoes_blocos`, `missoes_waypoints`, `missoes_validacoes`, `missoes_execucoes` e `missoes_fotos` no PostgreSQL/PostGIS.
- API para criar missao, gerar grid, editar waypoints, validar e exportar CSV Litchi/KML/GeoJSON em `backend/routers/missoes_captura.py`.
- Projeto, usuarios/permissoes, voos, upload de fotos e tarefa NodeODM em `backend/routers/odm.py`, com importacao de produtos processados.
- Mapas e analises geoespaciais web sobre os produtos gerados.

**Ainda nao existe** app Android, adaptador WPML/KMZ validado com DJI, pareamento com aeronave, telemetria ao vivo, sincronizacao movel de fotos ou inferencia movel. O fluxo atual e planejador/exportador + processamento posterior.

## 4. Arquitetura proposta

```text
Mini 3 <radio> RC-N1 <USB> Android/Kotlin + DJI MSDK V5
                                 | video -> quadros -> QA/IA local -> alertas
                                 | GPS/estado/eventos -> diario offline
                                 | fotos originais -> copia verificada quando SDK permitir
                                 | HTTPS autenticado, fila resumivel
                                 v
                Ortomapas API -> PostgreSQL/PostGIS + armazenamento de imagens
                                 | lote de fotos completo e validado
                                 v
                         NodeODM/WebODM -> ortofoto, DSM, DTM, nuvem
                                 v
                         visualizador e copiloto Ortomapas
```

O **servidor nao pilota o drone**. O caminho de controle fica local entre RC, Android e aeronave. Sem internet, o aplicativo preserva missao, telemetria e resultados locais e sincroniza depois. A IA local e o servidor podem sugerir repetir uma faixa, mas nao alteram rota/altitude em voo sem revisao explicita do piloto. O aplicativo Ortomapas deve ser o app de voo ativo; coexistencia/troca com DJI Fly nao e presumida. A documentacao DJI observa que DJI Fly nao oferece a mesma troca de contexto que DJI Pilot com um app MSDK. [DJI: notas MSDK V5](https://developer.dji.com/doc/mobile-sdk-tutorial/en/).

### 4.1 Modulos Android

1. **DJI Adapter:** inicializacao com App Key, conexao USB, capacidades consultadas no dispositivo, chaves da camera/gimbal, telemetria, video, estado da aeronave e erros do SDK. A DJI exige App Key propria por aplicativo. [Guia de amostra DJI](https://developer.dji.com/doc/mobile-sdk-tutorial/en/quick-start/run-sample.html).
2. **Mission Runner:** importa versao aprovada do contrato canonico, converte para WPML/KMZ se o Mini 3 aceitar; senao oferece modo guiado e estuda Virtual Stick em marco separado. Estados `preparada`, `validada`, `em_voo`, `pausada`, `interrompida`, `concluida` e `sincronizada`.
3. **Capture Journal:** registra cada disparo com ID local imutavel, instante monotonic/UTC, waypoint/trecho, posicao, altitude, rumo, gimbal, exposicao, resultado do comando e ID de arquivo DJI quando disponivel.
4. **QA ao vivo:** consome quadros reduzidos do video; detecta desfoque, sub/superexposicao, horizonte/obstrucao e possiveis lacunas de cobertura. A cobertura estimada usa plano, posicao e orientacao da camera, e nao a geometria exata do video comprimido. Mostra score, motivo, miniatura e area/trecho afetado. Resultado e **triagem**, nao aceite fotogrametrico final.
5. **Media Sync:** enumera/baixa originais em janela permitida pela camera, confere tamanho/hash, preserva EXIF e associa por horario/ID; guarda em fila local ate o servidor confirmar.
6. **Sync Client:** HTTPS com token do usuario, refresh, retomada por blocos, idempotencia por `execucao_id + camera_file_id/hash`, checksum e manifestos; envio de miniaturas separado dos originais.
7. **Flight UI:** mapa e grid, video ao vivo, estados de GPS/sinal/bateria/armazenamento, progresso de fotos, alertas claros, controle manual prioritario e comando de pausa/RTH conforme suporte real.

### 4.2 Analise no celular e no servidor

**No celular:** usar LiteRT/TFLite com CPU por padrao e GPU/NPU somente se benchmark do aparelho demonstrar beneficio sustentado. Os modelos devem ser pequenos, quantizados e operados sobre quadros amostrados, por exemplo 1-2 fps para QA; esse numero e alvo inicial, nao garantia. Metricas simples como blur/exposicao podem ser implementadas sem modelo. Registrar versao, latencia, temperatura, uso de bateria e confianca. O suporte NPU varia por fabricante. [Google LiteRT: NPU](https://ai.google.dev/edge/litert/android/npu), [DJI: quadros para algoritmos](https://developer.dji.com/doc/mobile-sdk-tutorial/en/tutorials/video-stream/video-stream2.html).

**No servidor durante o voo:** opcionalmente enviar miniaturas/quadros comprimidos e telemetria para inferencia mais pesada ou revisao humana. O servidor devolve alerta assincrono; atraso/rede nao podem bloquear captura nem controle. Nao enviar video bruto de modo permanente por padrao.

**Modelos:** blur, exposicao e cobertura podem comecar com metricas de imagem e geometria, sem LLM. Deteccao de objetos/segmentacao precisa de modelo de visao treinado e avaliado para o dominio; o repositorio ja possui um agente YOLOv8 para ortomapas, que pode ser estudado para o servidor, mas seus pesos genericos nao validam automaticamente as classes deste caso. O `qwen2.5-coder-32b-instruct` configurado hoje em `backend/config.py` e um modelo de texto/codigo; nao recebe pixels por si so. Para interpretacao visual por linguagem, seria necessario um VLM compativel e avaliado separadamente. O copiloto textual pode explicar alertas e medidas ja calculadas, sempre com fonte e incerteza.

**Apos voo ou pausa de captura:** transferir originais JPEG/DNG em janela testada, verificar cobertura com geotags/EXIF, detectar imagens ruins e lacunas, confirmar conjunto e acionar `POST /api/odm/tasks`. O NodeODM so recebe lote completo ou explicitamente aprovado; processamento fotogrametrico pesado permanece no servidor. A documentacao DJI afirma que download de midia e captura podem requerer modos distintos, portanto a transferencia por foto durante o voo e uma hipotese de bancada, nao requisito do MVP. [DJI: modos da camera](https://developer.dji.com/doc/mobile-sdk-tutorial/en/basic-introduction/basic-concepts/camera.html), [amostra MediaManager](https://developer.dji.com/doc/mobile-sdk-tutorial/en/tutorials/media-file.html).

## 5. Requisitos funcionais propostos

| ID | Requisito | Aceite observavel |
|---|---|---|
| MOB-01 | Autenticar usuario e listar apenas projetos/missoes permitidos | Outro usuario nao acessa execucao, fotos ou telemetria |
| MOB-02 | Baixar missao aprovada e travar versao/hash antes do voo | App e servidor exibem mesmo ID, versao, AOI e parametros |
| MOB-03 | Mostrar compatibilidade de drone, RC, firmware, SDK e capacidade por API | Funcao ausente desabilitada com motivo claro |
| MOB-04 | Checklist de pre-voo e validacao de bateria, GPS, armazenamento, gimbal, camera, altura, AOI e reserva | Inicio bloqueado por condicao critica; piloto pode abortar |
| MOB-05 | Executar grid e comandos de foto conforme o modo comprovado no Mini 3 | Log confronta waypoint/tempo/foto e registra falhas |
| MOB-06 | Exibir video, mapa, posicao, bateria, sinal, eventos e progresso | Atualizacao continua; tela tolera perda de link |
| MOB-07 | Pausar, retomar, abortar e permitir controle manual prioritario | Estado e evento auditados; perda de link segue configuracao de RTH do fabricante |
| MOB-08 | Analisar quadros em tempo real e destacar trecho suspeito | Alerta com causa, confianca, miniatura e posicao; sem comandar voo automaticamente |
| MOB-09 | Registrar cada captura e reconciliar com arquivo original | Contagem planejada, comandada, confirmada e recebida separadas |
| MOB-10 | Sincronizar offline/online com retomada e deduplicacao | Repetir envio nao cria foto nem execucao duplicada |
| MOB-11 | Reavaliar originais e cobertura antes de processar | Checklist informa fotos ausentes, geotag, blur, exposicao e sobreposicao estimada |
| MOB-12 | Submeter lote confirmado ao NodeODM e abrir produtos no Ortomapas | Task, logs, ortofoto e modelos vinculados ao projeto/voo |

## 6. Dados e API a acrescentar

Reaproveitar `missoes_execucoes` e `missoes_fotos`. Acrescentar migracoes PostgreSQL para: `missoes_eventos` (sequencia, instante, coordenada, origem e payload), `missoes_amostras_telemetria` (particionamento/retencao), `missoes_alertas_qa` (tipo, score, modelo, geometria, revisao), `missoes_transferencias` (estado, offsets, hash, erro) e campos de identificacao DJI em execucao/foto. Armazenar arquivos em disco/objeto, e no banco apenas caminhos, hashes, metadados, geometria e controle de acesso.

Endpoints **propostos, ainda inexistentes**:

- `GET /api/missoes-captura/{id}/pacote-mobile` e `POST /api/missoes-execucoes`: baixar plano imutavel e abrir execucao.
- `POST /api/missoes-execucoes/{id}/eventos`, `/telemetria` e `/alertas`: diario e QA.
- `POST /api/missoes-execucoes/{id}/fotos/sessoes`, `PUT /api/missoes-execucoes/{id}/fotos/{foto_id}/partes/{n}` e `POST /api/missoes-execucoes/{id}/fotos/{foto_id}/confirmar`: upload retomavel e verificado.
- `POST /api/missoes-execucoes/{id}/finalizar`: reconciliar contagens, fechar manifestos e liberar ODM.

Todos exigem usuario/projeto e chave de idempotencia. O endpoint ODM ja existe, mas precisara de orquestracao apos a transferencia.

## 7. Prova de viabilidade obrigatoria

**Gate A - bancada, sem voo:** instalar amostra DJI em Android com RC-N1 e Mini 3 real; registrar SDK, reconhecer modelo/firmware, obter video, telemetria, configuracoes de camera e capacidades `WaypointMissionManager`, `VirtualStickManager` e `MediaManager`. Registrar erros e latencias. O firmware do drone e do RC deve ser anotado.

**Gate B - captura controlada:** em area autorizada, piloto presente, testar disparo e geotag, pausa/retomada, perda de sinal e prioridade dos comandos manuais. Tentar missao WPML/KMZ apenas se a API confirmar suporte; caso contrario, avaliar Virtual Stick como projeto de controle separado com watchdog e testes extensivos.

**Gate C - midia:** fotografar em sequencia e tentar listar/baixar miniatura e original durante captura, entre trechos e apos pouso. Medir se ha interrupcao de camera, video ou missao e se o arquivo chega com EXIF completo. Se conflitar, fixar transferencia apos pouso como comportamento de produto.

**Gate D - IA e servidor:** benchmark no aparelho alvo por 20-30 minutos, incluindo video+mapa+inferencia+upload; medir fps, latencia p95, temperatura, bateria, memoria, tamanho de dados e falsos alertas. Desligar IA sob pressao termica sem afetar voo. Testar modo sem rede e retomada, fotos faltantes e duplicadas.

**Gate E - aceite ponta a ponta:** projeto e missao criados no Ortomapas, voo real com log, fotos reconciliadas, alerta QA inspecionado, lote ODM gerado e ortofoto/DSM/DTM/nuvem vinculados ao mesmo projeto. Conferir cobertura por pontos de foto e artefatos finais no mapa. Sem esse gate, o app permanece prototipo.

## 8. Ordem recomendada

1. **Spike DJI** curto e fisico para eliminar incertezas de Mini 3/RC-N1, waypoint e midia.
2. **App de observacao/captura guiada**: missao aprovada, video, telemetria, fotos e diario local; sem voo autonomo.
3. **Execucao automatica**, somente pelo modo comprovado no Gate B.
4. **QA local sobre video**, alertas de cobertura e sincronizacao com servidor.
5. **Transferencia de originais e ODM**, com retorno ao visualizador Ortomapas.
6. **IA avancada**: deteccao especifica do dominio, recomendacao de refazer faixas e revisao humana.

## 9. Riscos e limites

- Mini 3/RC-N1 suportados pelo SDK nao significam que todas as capacidades de missao embarcada ou midia simultanea existam. Os Gates A-C decidem o desenho final.
- Quadros transmitidos sao comprimidos e podem ter resolucao menor que a foto; servem para triagem, nao para substituir inspecao do original ou gerar ortofoto final.
- A qualidade do mapa depende de GSD, sobreposicao, exposicao, altitude real, vento e georreferenciamento. IA nao corrige falta fisica de cobertura.
- Virtual Stick aumenta dependencia de Android, USB, enlace e algoritmo de controle; nao deve ser a primeira entrega de voo automatico.
- Antes de operar no Brasil, o piloto deve conferir regras e autorizacoes aplicaveis ao local e ao tipo de voo. O app so pode ajudar com checklist; nao concede permissao.

## 10. Simulador de voo baseado no projeto local `drone`

### 10.1 Inventario e decisao de reaproveitamento

Foi inspecionado o projeto local `/mnt/data1/progpython/drone` (fora deste repositorio). Seu documento `DOCUMENTACAO_DRONE.md` descreve tres conjuntos de codigo:

| Fonte | O que aproveitar | O que impede o uso direto |
|---|---|---|
| `01_RLDDPGTD3LL` (projeto do usuario; [repositorio RL](https://github.com/pasteurjr/RL)) | Modelo de quadricoptero com 6 graus de liberdade, integracao RK4, mistura dos motores, experimentos de manobra e visualizacao Matplotlib; serve como referencia e base para testes de regressao | Parametros genericos de 1 kg, nao medidos no Mini 3; versoes `.py` com erros de integracao; notebook principal com problema de gravidade projetada e testes de RL que nao convergiram. Nao reutilizar o agente TD3 como piloto |
| `02_drone_sim` (terceiros, licenca MIT) | API simples `Drone.step` com RPM dos quatro motores, ruido de sensores e visualizacao 3D; exemplo de estrutura de modulo | Modelo e parametros genericos (massa de 0,468 kg); nao recebe comandos de alto nivel da DJI, nao representa o controlador interno do Mini 3 e nao tem validacao contra telemetria real |
| `03_rldrone` (prototipos antigos) | Formulas e experimentos PID podem orientar testes unitarios de sinais e eixos | No modelo 6-DOF, `fx=fy=0`, torque de guinada nulo e erros de unidades/integracao; nao consegue demonstrar corretamente comandos de avancar, recuar ou guinar |

**Decisao:** extrair conceitos e casos de teste, nao copiar os modulos atuais para producao. O codigo de dinamica deve ser isolado em biblioteca testavel, sem efeitos colaterais ao importar e com unidades/SI e referenciais explicitados. A primeira meta e **simulacao funcional e calibravel** para planejamento, comandos e captura; nao uma replica exata do firmware proprietario DJI. Um modelo sem parametros aerodinamicos, de motores e de controlador medidos no equipamento nao pode garantir equivalencia fisica com o Mini 3.

### 10.2 Arquitetura proposta

```text
Missao Ortomapas (grid, altitude, velocidade, fotos)
      -> Mission Runner / mesma maquina de estados do app Android
      -> contrato DroneGateway (comandos, telemetria, eventos de camera)
           -> DjiGateway: MSDK V5 + RC-N1 + Mini 3 real
           -> SimGateway: autopiloto substituto + dinamica 6-DOF + sensores/camera simulados
      -> diario de execucao e QA -> Ortomapas
      -> visualizacao: mapa 2D + cena 3D, rota planejada e percorrida
```

O `SimGateway` deve aceitar **o mesmo contrato de alto nivel** usado pelo app: velocidade horizontal, velocidade vertical/altitude, rumo ou taxa de guinada, pausar, retomar, pousar, RTH e disparar foto. Deve traduzir esses comandos para um controlador interno substituto (por exemplo PID em cascata), mistura de motores e dinamica 6-DOF. Aplicar RPM diretamente aos quatro motores testaria outra interface, nao a experiencia de Virtual Stick do usuario. O modo simulado tera identificacao visual inequivoca e isolamento que impossibilite enviar comandos ao drone real por engano.

Representar posicao em coordenadas locais ENU ou NED com conversao explicita para latitude/longitude; definir quadro do corpo e convencao de sinais para avancar/recuar, deslocar lateralmente, subir/descer e guinar. Propagar atitude preferencialmente por quaternions, exibindo angulos de Euler ao usuario; isto evita a singularidade da parametrizacao de Euler em inclinacoes elevadas. Usar passo fixo deterministico para testes, e RK4 ou integrador numerico equivalente apos testes de conservacao/estabilidade. Parametros da aeronave, camera, bateria e atrasos devem ser configuraveis e versionados, com valores nao medidos marcados como **hipoteses**.

### 10.3 Capacidades e cenarios obrigatorios

- Reproduzir uma missao real do banco Ortomapas sobre mapa/AOI, incluindo waypoints, curvas, velocidade, altitude, rumo, gimbal, intervalo de disparo e pegadas estimadas de cada foto. Registrar rota planejada e realizada, instantes e posicoes dos disparos; permitir replay e exportacao da telemetria.
- Injetar vento, rajadas, erro GNSS/IMU, atraso/jitter dos comandos, falha de camera, bateria baixa e perda de enlace. Exibir a consequencia operacional: foto perdida, lacuna de cobertura, desvio de rota, pausa, RTH ou termino seguro. Nao modelar obstaculos como evitados automaticamente sem prova de suporte do Mini 3 no modo de controle escolhido.
- Validar decolagem, hover, avancar, recuar, transladar, subir, descer, guinar, seguir trecho, pausar, retomar e pousar. Conferir sentido do movimento e dos eixos por testes unitarios antes de renderizar a trajetoria.
- Apresentar visualizacao interativa 2D/3D para inspecao humana; a renderizacao Matplotlib existente e util como diagnostico, mas nao substitui o mapa e a interface operacional do Ortomapas. A 3D deve distinguir simulacao fisica, terreno disponivel e estimativa de cobertura; nao sugerir foto real quando so existe disparo simulado.
- Executar testes automaticos sem interface (mesma semente, mesmo resultado) e cenarios visuais capturados. O aceite mede erro transversal/altitude/rumo, numero e distribuicao de fotos, sobreposicao prevista, latencia, violacoes de limites e comportamento de falhas. Limites numericos de erro so serao fixados depois de calibracao com logs reais.

### 10.4 Caminho de validacao

1. **Corrigir o nucleo fisico** em modulo novo: gravidade no referencial correto, empuxo projetado pela atitude, arrasto com sinal, derivada de posicao igual a velocidade, torques de roll/pitch/yaw e conversao RPM -> forca/torque. Criar testes de hover, simetria, sinais e conservacao basica.
2. **Implementar o adaptador de comandos** e testar cada comando de alto nivel com trajeto conhecido, sem RL. O controlador PID substituto e apenas parte do simulador, nao hipotese sobre o algoritmo interno DJI.
3. **Integrar uma missao do Ortomapas** e conferir georreferenciamento, geometria da rota, captura e cobertura em 2D/3D, com comparacao automatica entre esperado e obtido.
4. **Testar o simulador oficial do DJI MSDK V5** conectado ao Mini 3/RC-N1, se a combinacao concreta oferecer a funcao, para validar chamadas SDK e comportamento de estado. A DJI documenta a API de simulador, mas isso nao comprova aqui disponibilidade nem fidelidade para esse conjunto; requer prova de bancada. [DJI: Simulator Sample](https://developer.dji.com/doc/mobile-sdk-tutorial/en/tutorials/simulator.html).
5. **Calibrar com telemetria de voos reais controlados** em area autorizada, registrando firmware, bateria, vento, carga, velocidade, curvas e resposta a comandos; comparar distribuicoes de erro e atualizar parametros. Somente esses ensaios permitem afirmar quao proximo o modelo esta do Mini 3. Simulacao nao substitui teste fisico de seguranca.

**Escopo de aceite:** o simulador demonstra que o *nosso* planejador, runner, conversao de coordenadas, agenda de fotos, tratamento de falhas e interface operam corretamente no contrato definido. Ele nao certifica resposta aerodinamica, capacidade de waypoint nativo, evitamento de obstaculos, nem seguranca real do Mini 3 sem ensaio com aeronave e SDK.
