from machine import Pin, PWM, ADC
from utime import ticks_ms, ticks_diff

led_r = PWM(Pin(25), freq=1000)
led_g = PWM(Pin(26), freq=1000)
led_b = PWM(Pin(27), freq=1000)

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)

pir = Pin(13, Pin.IN)  # HIGH = presenca detectada

INTERVALO_SENSOR_MS  = 500
INTERVALO_PRINT_MS   = 1000

LDR_LIMIAR_ESCURO    = 2500
LDR_LIMIAR_CLARO     = 1800

PIR_TOLERANCIA_CICLOS = 6   # 6 x 500ms = 3s de ausencia antes de desligar

estado_atual    = "DESLIGADO"
ciclos_ausencia = 0

t_ultimo_sensor = ticks_ms()
t_ultimo_print  = ticks_ms()

def set_rgb(r, g, b):
    led_r.duty(r)
    led_g.duty(g)
    led_b.duty(b)

def apagar():
    set_rgb(0, 0, 0)

def iluminar_eco():
    set_rgb(80, 60, 0)

def iluminar_ativo():
    set_rgb(800, 800, 800)

def aplicar_estado(estado):
    if estado == "DESLIGADO":
        apagar()
    elif estado == "ECO":
        iluminar_eco()
    elif estado == "ATIVO":
        iluminar_ativo()

def ler_sensores():
    return {
        "ldr":      ldr.read(),
        "presenca": pir.value() == 1
    }

def atualizar_estado(leituras):
    global estado_atual, ciclos_ausencia

    presenca = leituras["presenca"]
    ldr_val  = leituras["ldr"]
    escuro   = ldr_val > LDR_LIMIAR_ESCURO
    claro    = ldr_val < LDR_LIMIAR_CLARO

    novo_estado = estado_atual  # assume sem mudanca

    if presenca:
        ciclos_ausencia = 0

        if estado_atual == "DESLIGADO":
            novo_estado = "ATIVO" if escuro else "ECO"
        elif estado_atual == "ECO" and escuro:
            novo_estado = "ATIVO"
        elif estado_atual == "ATIVO" and claro:
            novo_estado = "ECO"

    else:
        ciclos_ausencia += 1
        if ciclos_ausencia >= PIR_TOLERANCIA_CICLOS:
            novo_estado = "DESLIGADO"

    if novo_estado != estado_atual:
        print("[ESTADO] {} -> {}".format(estado_atual, novo_estado))
        estado_atual = novo_estado
        aplicar_estado(estado_atual)

apagar()
print("Teste")
print("=== Incremento 2: LDR + PIR — ECO / ATIVO ===")
print("PIR sem presenca: LED apagado")
print("PIR com presenca + escuro: LED branco (ATIVO)")
print("PIR com presenca + claro:  LED ambar  (ECO)")
print("---")

while True:
    agora = ticks_ms()

    if ticks_diff(agora, t_ultimo_sensor) >= INTERVALO_SENSOR_MS:
        t_ultimo_sensor = agora
        leituras = ler_sensores()
        atualizar_estado(leituras)

    if ticks_diff(agora, t_ultimo_print) >= INTERVALO_PRINT_MS:
        t_ultimo_print = agora
        leituras = ler_sensores()
        print("LDR={} | PIR={} | Estado={}".format(
            leituras["ldr"],
            "SIM" if leituras["presenca"] else "NAO",
            estado_atual
        ))