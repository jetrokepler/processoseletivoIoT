<div align=center>

###### Processo Seletivo — Intensivo Maker | IoT
# Iluminação inteligente industrial com otimização energética


![Versão](https://img.shields.io/badge/versão-v1.0.0-light?style=for-the-badge)
![Python](https://img.shields.io/badge/micropython-3776AB?style=for-the-badge&logo=micropython&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-E7352C?style=for-the-badge&logo=espressif&logoColor=white)
![Wokwi](https://img.shields.io/badge/Wokwi-005A00?style=for-the-badge&logo=wokwi&logoColor=white)
![mpremote](https://img.shields.io/badge/mpremote_--_1.28.0-991664?style=for-the-badge&logo=mpremote&logoColor=white)
![Docker](https://img.shields.io/badge/Dev_Container-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

### 👤 Identificação do Candidato

- **Nome completo:** _Jetro Kepler Gomes Alencar Gonzaga Viana_



## 1️⃣ Visão Geral da Solução

Este projeto implementa um **sistema embarcado de iluminação inteligente** simulado em ESP32 com MicroPython, voltado para ambientes industriais.

O sistema monitora continuamente dois parâmetros do ambiente — **luminosidade** e **presença humana** — e decide automaticamente se deve ligar, reduzir ou desligar a iluminação. O objetivo é simular um cenário real de eficiência energética: a luz só acende quando há alguém no ambiente e somente se o local estiver escuro.

O usuário interage com o sistema ajustando o slider do sensor de luminosidade e clicando no sensor de movimento para simular presença.



## 2️⃣ Arquitetura do Sistema Embarcado

### Fluxo principal do `main.py`

O firmware é organizado em três camadas independentes, seguindo o princípio de separação de responsabilidades:

```
Leitura (ler_sensores)
    ↓
Decisão (calcular_proximo_estado)
    ↓
Atuação (transicionar → aplicar_saida)
```

Essa separação garante que a lógica de decisão nunca dependa diretamente do hardware — facilitando testes, manutenção e expansão.

### Máquina de Estados Finitos (FSM)

O comportamento do sistema é controlado por uma FSM com três estados:

| Estado | Condição | LED |
|---|---|---|
| `DESLIGADO` | Sem presença detectada | Apagado |
| `ECO` | Presença + ambiente já claro | Âmbar fraco (R=80, G=60, B=0) |
| `ATIVO` | Presença + ambiente escuro | Branco pleno (R=800, G=800, B=800) |

**Tabela de transições:**

```
DESLIGADO + presença + escuro  → ATIVO
DESLIGADO + presença + claro   → ECO
ECO       + escuro             → ATIVO
ATIVO     + claro              → ECO
ECO/ATIVO + ausência por 3s   → DESLIGADO
```

### Temporização não-bloqueante

O loop principal usa `ticks_ms()` e `ticks_diff()` para controlar dois ciclos independentes:

- **Ciclo de sensor:** a cada 500ms — lê os sensores e atualiza o estado
- **Ciclo de print:** a cada 1000ms — imprime o status no terminal serial

Isso garante que o sistema nunca "trava" esperando um temporizador, podendo responder a eventos em qualquer momento.

### Histerese no LDR

Dois limiares distintos evitam que o LED fique oscilando quando a luminosidade está na fronteira:

```
ADC > 2500  →  ambiente escuro  →  permite iluminação plena
ADC < 1800  →  ambiente claro   →  reduz ou desliga
Entre 1800 e 2500: mantém o estado atual (zona morta)
```

### Tolerância do PIR

O PIR detecta **movimento**, não presença contínua. Quando a pessoa fica imóvel, o sensor pode perder o sinal. Para evitar desligar prematuramente, o sistema aguarda **6 ciclos consecutivos sem detecção** (equivalente a 3 segundos) antes de transitar para `DESLIGADO`.


## 3️⃣ Componentes Utilizados na Simulação

| Componente | Tipo no Wokwi | Pino ESP32 | Função |
|---|---|---|---|
| ESP32 DevKit C V4 | `board-esp32-devkit-c-v4` | — | Microcontrolador principal |
| LED RGB | `wokwi-rgb-led` | GPIO 25 / 26 / 27 | Representa a iluminação do ambiente |
| Resistor 220Ω (×3) | `wokwi-resistor` | — | Proteção dos canais R, G e B do LED |
| Sensor de luminosidade | `wokwi-photoresistor-sensor` | GPIO 34 (ADC) | Mede a claridade do ambiente |
| Sensor de presença | `wokwi-pir-motion-sensor` | GPIO 13 (Digital) | Detecta movimento no ambiente |

### Conceitos técnicos dos componentes

**PWM (Modulação por Largura de Pulso):** técnica que controla a potência entregue a um componente variando a proporção de tempo em que o sinal fica em nível alto. Com `duty=800` o LED recebe 78% da potência máxima; com `duty=80` recebe apenas 8%. É assim que se controla o brilho do LED RGB.

**ADC (Conversor Analógico-Digital):** converte a tensão analógica do LDR (0 a 3.3V) em um número inteiro (0 a 4095). Quanto mais escuro o ambiente, maior a resistência do LDR, maior a tensão no pino e maior o valor lido pelo ADC.

**LDR (Resistor Dependente de Luz):** resistor cuja resistência varia com a luz. Em ambientes escuros sua resistência aumenta; em ambientes claros diminui. No Wokwi é controlado por um slider que representa a intensidade luminosa em lux.

**PIR (Sensor Infravermelho Passivo):** detecta variações de radiação infravermelha causadas pelo calor corporal humano em movimento. Saída digital: HIGH quando detecta movimento, LOW quando não detecta.


## 4️⃣ Decisões Técnicas Relevantes

**Máquina de estados finitos como estrutura central:** os estados tornam o comportamento do sistema explícito e previsível. Cada transição é claramente definida na tabela de estados, e a função `calcular_proximo_estado` não tem efeitos colaterais — apenas calcula e retorna, sem modificar nada.

**Separação em três camadas:** `ler_sensores()` nunca decide nada; `calcular_proximo_estado()` nunca aciona hardware; `aplicar_saida()` nunca lê sensores. Esse desacoplamento facilita a expansão — para adicionar um novo sensor, basta alterar `ler_sensores()` e `calcular_proximo_estado()`, sem tocar no restante.

**Histerese no LDR:** limiares assimétricos (2500 para ligar, 1800 para desligar) criam uma zona morta que absorve oscilações naturais do sensor, evitando o efeito de "piscar" do LED na fronteira entre claro e escuro.

**Tolerância de ausência no PIR:** o PIR detecta movimento, não presença estática. A tolerância de 6 ciclos (3 segundos) compensa o comportamento real do sensor e evita falsos desligamentos quando a pessoa está imóvel.

**Registro de tempo por estado:** a variável `tempo_por_estado` acumula quantos milissegundos o sistema passou em cada estado. Isso serve como base para métricas de eficiência energética em incrementos futuros.

## 5️⃣ Resultados Obtidos

O sistema funciona corretamente na simulação Wokwi, apresentando o seguinte comportamento validado:

- **Sem presença:** LED permanece apagado independentemente da luminosidade
- **Presença + ambiente escuro:** LED acende em branco pleno (estado `ATIVO`)
- **Presença + ambiente claro:** LED acende em âmbar fraco (estado `ECO`)
- **Transição entre ECO e ATIVO:** responde em até 500ms à mudança do slider do LDR
- **Retorno ao DESLIGADO:** ocorre após 3 segundos sem detecção de movimento
- **Terminal serial:** exibe transições de estado e status periódico a cada 1 segundo
- **Pipeline CI/CD:** executa com sucesso no GitHub Actions, validando o `print("Teste")` esperado

### Como testar no Wokwi

1. Gere o `fs.bin` com o comando Docker e reinicie a simulação
```
docker build --no-cache -t esp32-builder . && \
docker run --name esp32-fs-tmp esp32-builder /bin/bash ; \
docker cp esp32-fs-tmp:/fs.bin . ; \
docker rm esp32-fs-tmp
```
2. **Teste SEM presença:** Clique no LDR, ajuste o slider diminuindo e aumentando a 'lux' e perceba que o led não liga, pois não há nenhum tipo de presença; 
3. **Teste de luminosidade:** com o PIR ativo, mova o slider do LDR:
   - Slider baixo (pouca luz ou 'lux') → LED branco — estado `ATIVO`
   - Slider alto (muita luz) → LED âmbar — estado `ECO`

4. **Teste de tolerância:** pare de clicar no PIR e aguarde 3 segundos — o LED apaga

---

## 6️⃣ Comentários Adicionais

### Configuração do ambiente de desenvolvimento

O repositório inclui `pyrightconfig.json` e `.vscode/settings.json` para silenciar avisos falsos do Pylance e do cSpell no Visual Studio Code. As bibliotecas machine, utime e dht são nativas do MicroPython e não existem no ambiente Python padrão — por isso o analisador as acusa como não resolvidas, embora o projeto funcione corretamente. Portanto, adicionei os arquivos de configuração supracitados para omitir tais avisos.

### Limitações da solução

- O potenciômetro de simulação de consumo energético e o sensor DHT22 (temperatura/umidade) estão planejados para incrementos futuros e não estão presentes nesta versão
- O modo MANUAL e o modo FESTA (controle por botão) também são incrementos planejados
- A simulação de consumo energético é representativa, não real

### Melhorias futuras

- Incremento 4: sensor DHT22 para conforto ambiental e estado `CONFORTO`
- Incremento 5: potenciômetro simulando consumo e estado `ALERTA`
- Incremento 6: coleta e exibição de métricas operacionais completas
- Incremento 7: botão para modo manual com override do sistema automático
- Incremento 8: modo FESTA com animação RGB

### Aprendizados

O projeto consolidou conceitos fundamentais de sistemas embarcados: arquitetura de firmware orientada a estados, temporização não-bloqueante, leitura de sensores analógicos e digitais, controle PWM de atuadores e integração de pipeline CI/CD com simulação de hardware virtual.

---
 
> ✅ Simulação funcional no Wokwi com todos os componentes do incremento 3  
> ✅ Código modular, comentado e organizado em camadas