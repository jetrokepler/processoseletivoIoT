'''
Sistema de Iluminacao Inteligente Industrial — ESP32 + MicroPython

Este firmware implementa um sistema de iluminação automática baseado em dois sensores: luminosidade (LDR) e presença (PIR). A lógica central é uma máquina de estuado finitos com três estados possíveis:

DESLIGADO — sem presença detectada. LED apagado.
ECO       — presença detectada, mas ambiente já iluminado. LED âmbar fraco.
ATIVO     — presença detectada e ambiente escuro. LED branco pleno.

O loop principal e nao-bloqueante: usa ticks_ms() para controlar o tempo sem pausar a execução com sleep(), permitindo que o sistema reaja rapidamente a qualquer evento.
'''

from machine import Pin, PWM, ADC
from utime import ticks_ms, ticks_diff

# ========
# HARDWARE
# ========

# LED RGB — cada canal controlado por PWM (Pulse Width Modulation).
# PWM permite variar o brilho de cada cor ajustando o duty cycle (0-1023).
# freq=1000 significa 1000 pulsos por segundo, imperceptivel ao olho humano.
led_r = PWM(Pin(25), freq=1000)  # canal vermelho
led_g = PWM(Pin(26), freq=1000)  # canal verde
led_b = PWM(Pin(27), freq=1000)  # canal azul

# LDR (Light Dependent Resistor) — sensor de luminosidade.
# Lido via ADC (Analog-to-Digital Converter): converte tensao em numero (0-4095).
# ATTN_11DB amplia a faixa de leitura para 0-3.3V, cobrindo toda a escala do sensor.
# Comportamento no Wokwi: slider baixo (pouca luz) -> ADC alto; slider alto (muita luz) -> ADC baixo.
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)

# PIR (Passive Infrared Sensor) — detecta movimento por variacao de calor.
# Saida digital: HIGH (1) = presenca detectada, LOW (0) = ausencia.
pir = Pin(13, Pin.IN)

# ==========
# CONSTANTES
# ==========

INTERVALO_SENSOR_MS   = 500   # le os sensores a cada 500ms
INTERVALO_PRINT_MS    = 1000  # imprime status a cada 1s

# Limiares do LDR com histerese: dois valores distintos evitam que o LED
# fique oscilando quando a luminosidade esta na fronteira entre claro e escuro.
LDR_LIMIAR_ESCURO = 2500  # ADC acima disso: ambiente escuro -> permite iluminacao plena
LDR_LIMIAR_CLARO  = 1800  # ADC abaixo disso: ambiente claro -> reduz ou desliga

# Tolerancia do PIR: o sensor perde o sinal quando a pessoa fica imavel.
# Aguarda N ciclos de ausencia antes de realmente desligar.
PIR_TOLERANCIA_CICLOS = 6  # 6 x 500ms = 3 segundos de tolerancia

# ==============
# ESTADOS DA FSM
# ==============

DESLIGADO = "DESLIGADO"  # sem presenca — LED apagado
ECO       = "ECO"        # presenca + claro — LED ambar (economia de energia)
ATIVO     = "ATIVO"      # presenca + escuro — LED branco pleno

# ===========================
# VARIAVEIS GLOBAIS DE ESTADO
# ===========================

estado_atual     = DESLIGADO
ciclos_ausencia  = 0          # contador de ciclos consecutivos sem presenca

t_ultimo_sensor  = ticks_ms()
t_ultimo_print   = ticks_ms()
t_entrada_estado = ticks_ms()  # marca quando entrou no estado atual

# Acumula tempo (ms) gasto em cada estado — base para metricas futuras
tempo_por_estado = { DESLIGADO: 0, ECO: 0, ATIVO: 0 }

# =================
# CAMADA DE ATUACAO
# =================

def set_rgb(r, g, b):
    """Define cor do LED RGB. Cada canal aceita valor de 0 (apagado) a 1023 (maximo)."""
    led_r.duty(r)
    led_g.duty(g)
    led_b.duty(b)


def aplicar_saida(estado):
    """Mapeia um estado da FSM para a cor correspondente no LED RGB."""
    if estado == DESLIGADO:
        set_rgb(0, 0, 0)          # apagado
    elif estado == ECO:
        set_rgb(80, 60, 0)        # ambar fraco — sinaliza presenca com baixo consumo
    elif estado == ATIVO:
        set_rgb(800, 800, 800)    # branco pleno — iluminacao de trabalho

# =================
# CAMADA DE LEITURA
# =================

def ler_sensores():
    """Retorna leitura atual de todos os sensores em um dicionario."""
    return {
        "ldr":      ldr.read(),        # valor ADC: 0 (claro) a 4095 (escuro)
        "presenca": pir.value() == 1   # True se movimento detectado
    }

# =================================
# CAMADA DE DECISAO — logica da FSM
# =================================

def calcular_proximo_estado(leituras):
    """
    Determina o proximo estado da FSM com base nas leituras dos sensores.
    Nao altera nenhuma variavel global de estado — apenas retorna o proximo estado.

    Tabela de transicoes:
      DESLIGADO + presenca + escuro      -> ATIVO
      DESLIGADO + presenca + claro/meio  -> ECO
      ECO       + escuro                 -> ATIVO
      ECO/ATIVO + ausencia por 3s        -> DESLIGADO
      ATIVO     + claro                  -> ECO
    """
    global ciclos_ausencia

    presenca = leituras["presenca"]
    ldr_val  = leituras["ldr"]
    escuro   = ldr_val > LDR_LIMIAR_ESCURO
    claro    = ldr_val < LDR_LIMIAR_CLARO

    if presenca:
        ciclos_ausencia = 0  # reseta tolerancia a cada deteccao

        if estado_atual == DESLIGADO:
            return ATIVO if escuro else ECO
        if estado_atual == ECO and escuro:
            return ATIVO
        if estado_atual == ATIVO and claro:
            return ECO

    else:
        ciclos_ausencia += 1
        if ciclos_ausencia >= PIR_TOLERANCIA_CICLOS:
            return DESLIGADO

    return estado_atual  # sem mudanca

# ========================
# GERENCIADOR DE TRANSICAO
# ========================

def transicionar(novo_estado):
    """
    Executa a transicao para um novo estado:
      1. Acumula o tempo que ficou no estado anterior (metrica)
      2. Atualiza o estado global
      3. Aplica a saida visual correspondente
      4. Registra a transicao no terminal
    """
    global estado_atual, t_entrada_estado

    if novo_estado == estado_atual:
        return  # sem mudanca, nada a fazer

    agora = ticks_ms()
    tempo_por_estado[estado_atual] += ticks_diff(agora, t_entrada_estado)
    t_entrada_estado = agora

    print("[FSM] {} -> {}".format(estado_atual, novo_estado))
    estado_atual = novo_estado
    aplicar_saida(estado_atual)

# =============
# INICIALIZAÇÃO
# =============

aplicar_saida(DESLIGADO)
print("Teste")
print("-" * 30)
print("Como testar:")
print("  LDR: slider baixo = escuro | slider alto = claro")
print("  PIR: clique no sensor para simular presenca")
print("---" * 30)

# ==============
# LOOP PRINCIPAL
# ==============

while True:
    agora = ticks_ms()

    # Ciclo de leitura e decisao (a cada 500ms)
    if ticks_diff(agora, t_ultimo_sensor) >= INTERVALO_SENSOR_MS:
        t_ultimo_sensor = agora
        leituras    = ler_sensores()
        prox_estado = calcular_proximo_estado(leituras)
        transicionar(prox_estado)

    # Ciclo de saida serial (a cada 1s) — menos verboso que o ciclo de sensor
    if ticks_diff(agora, t_ultimo_print) >= INTERVALO_PRINT_MS:
        t_ultimo_print = agora
        leituras = ler_sensores()
        print("LDR={} PIR={} Estado={}".format(
            leituras["ldr"],
            "SIM" if leituras["presenca"] else "NAO",
            estado_atual
        ))