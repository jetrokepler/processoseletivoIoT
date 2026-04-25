# =============================================================================
# Sistema de Iluminacao Inteligente Industrial - ESP32 + MicroPython
# Incremento 1: Controle basico de iluminacao por LDR com histerese
# =============================================================================
# Objetivo:
#   Ler o sensor de luminosidade (LDR) e ligar/desligar o LED RGB
#   automaticamente com base na claridade do ambiente.
#   Histerese aplicada para evitar oscilacao rapida do LED.
#
# Comportamento esperado:
#   - Slider LDR baixo (pouca luz, ADC alto > 2500) -> LED branco ligado
#   - Slider LDR alto  (muita luz, ADC baixo < 1800) -> LED apagado
#   - Entre 1800 e 2500: mantem estado atual (zona morta da histerese)
#
# Pinos:
#   GPIO 25 -> LED RGB vermelho
#   GPIO 26 -> LED RGB verde
#   GPIO 27 -> LED RGB azul
#   GPIO 34 -> LDR (AO - saida analogica)
# =============================================================================

from machine import Pin, PWM, ADC
from utime import ticks_ms, ticks_diff

# --- Hardware ---

led_r = PWM(Pin(25), freq=1000)
led_g = PWM(Pin(26), freq=1000)
led_b = PWM(Pin(27), freq=1000)

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)  # faixa 0-3.3V -> leitura 0-4095

# --- Constantes ---

INTERVALO_SENSOR_MS = 500
INTERVALO_PRINT_MS  = 1000

# Histerese: dois limiares evitam liga/desliga rapido
# ADC alto = pouca luz = escuro; ADC baixo = muita luz = claro
LDR_LIMIAR_ESCURO = 2500  # acima: ambiente escuro -> liga LED
LDR_LIMIAR_CLARO  = 1800  # abaixo: ambiente claro -> desliga LED

# --- Estado inicial ---

iluminacao_ativa = False
t_ultimo_sensor  = ticks_ms()
t_ultimo_print   = ticks_ms()


# ---------------------------------------------------------------------------
# Funcoes de atuacao
# ---------------------------------------------------------------------------

def set_rgb(r, g, b):
    """Define cor do LED RGB (0-1023 por canal)."""
    led_r.duty(r)
    led_g.duty(g)
    led_b.duty(b)

def apagar():
    set_rgb(0, 0, 0)

def iluminar_normal():
    """Branco pleno — iluminacao padrao."""
    set_rgb(800, 800, 800)


# ---------------------------------------------------------------------------
# Funcao de leitura
# ---------------------------------------------------------------------------

def ler_ldr():
    """Retorna valor ADC do LDR (0 a 4095)."""
    return ldr.read()


# ---------------------------------------------------------------------------
# Logica de controle com histerese
# ---------------------------------------------------------------------------

def atualizar_iluminacao(valor_ldr):
    """
    Decide ligar ou desligar o LED com base no LDR e histerese.
    Retorna True se iluminacao ativa, False se apagada.
    """
    global iluminacao_ativa

    if not iluminacao_ativa and valor_ldr > LDR_LIMIAR_ESCURO:
        iluminacao_ativa = True
        iluminar_normal()
        print("[ATIVO] Ambiente escuro. Iluminacao ligada.")

    elif iluminacao_ativa and valor_ldr < LDR_LIMIAR_CLARO:
        iluminacao_ativa = False
        apagar()
        print("[DESLIGADO] Ambiente claro. Iluminacao desligada.")

    return iluminacao_ativa


# ---------------------------------------------------------------------------
# Inicializacao
# ---------------------------------------------------------------------------

apagar()
print("Teste")
print("=== Incremento 1: Controle por LDR com histerese ===")
print("Slider LDR baixo = escuro = LED liga")
print("Slider LDR alto  = claro  = LED apaga")
print("---")


# ---------------------------------------------------------------------------
# Loop principal — nao-bloqueante
# ---------------------------------------------------------------------------

while True:
    agora = ticks_ms()

    if ticks_diff(agora, t_ultimo_sensor) >= INTERVALO_SENSOR_MS:
        t_ultimo_sensor = agora
        valor = ler_ldr()
        atualizar_iluminacao(valor)

    if ticks_diff(agora, t_ultimo_print) >= INTERVALO_PRINT_MS:
        t_ultimo_print = agora
        valor = ler_ldr()
        print("LDR={} | Iluminacao={}".format(
            valor,
            "ATIVA" if iluminacao_ativa else "DESLIGADA"
        ))