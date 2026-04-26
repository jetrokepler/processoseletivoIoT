from machine import Pin, PWM, ADC
from utime import ticks_ms, ticks_diff

led_r = PWM(Pin(25), freq=1000)
led_g = PWM(Pin(26), freq=1000)
led_b = PWM(Pin(27), freq=1000)

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)  

pir = Pin(13, Pin.IN)   

INTERVALO_SENSOR_MS  = 500
INTERVALO_PRINT_MS   = 1000
LDR_LIMIAR_ESCURO = 2500   
LDR_LIMIAR_CLARO  = 1800   
PIR_TOLERANCIA_CICLOS = 6 

DESLIGADO = "DESLIGADO" 
ECO       = "ECO"      
ATIVO     = "ATIVO"    

estado_atual     = DESLIGADO
ciclos_ausencia  = 0

t_ultimo_sensor  = ticks_ms()
t_ultimo_print   = ticks_ms()
t_entrada_estado = ticks_ms()

tempo_por_estado = { DESLIGADO: 0, ECO: 0, ATIVO: 0 }

def set_rgb(r, g, b):
    led_r.duty(r)
    led_g.duty(g)
    led_b.duty(b)

def aplicar_saida(estado):
    if estado == DESLIGADO:
        set_rgb(0, 0, 0)        
    elif estado == ECO:
        set_rgb(80, 60, 0)      
    elif estado == ATIVO:
        set_rgb(800, 800, 800) 

def ler_sensores():
    return {
        "ldr":      ldr.read(),
        "presenca": pir.value() == 1
    }

def calcular_proximo_estado(leituras):
    global ciclos_ausencia

    presenca = leituras["presenca"]
    ldr_val  = leituras["ldr"]
    escuro   = ldr_val > LDR_LIMIAR_ESCURO
    claro    = ldr_val < LDR_LIMIAR_CLARO

    if presenca:
        ciclos_ausencia = 0

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

    return estado_atual

def transicionar(novo_estado):
    global estado_atual, t_entrada_estado

    if novo_estado == estado_atual:
        return

    agora = ticks_ms()
    tempo_por_estado[estado_atual] += ticks_diff(agora, t_entrada_estado)
    t_entrada_estado = agora

    print("[FSM] {} -> {}".format(estado_atual, novo_estado))
    estado_atual = novo_estado
    aplicar_saida(estado_atual)

aplicar_saida(DESLIGADO)
print("Teste")
print("=== Inc3: FSM — DESLIGADO / ECO / ATIVO ===")
print("LDR GPIO34 | PIR GPIO13 | LED RGB GPIO25/26/27")
print("---")
print("Como testar:")
print("  LDR: slider baixo = escuro | slider alto = claro")
print("  PIR: clique no sensor para simular presenca")
print("---")

while True:
    agora = ticks_ms()

    if ticks_diff(agora, t_ultimo_sensor) >= INTERVALO_SENSOR_MS:
        t_ultimo_sensor = agora
        leituras    = ler_sensores()
        prox_estado = calcular_proximo_estado(leituras)
        transicionar(prox_estado)

    if ticks_diff(agora, t_ultimo_print) >= INTERVALO_PRINT_MS:
        t_ultimo_print = agora
        leituras = ler_sensores()
        print("LDR={} PIR={} Estado={}".format(
            leituras["ldr"],
            "SIM" if leituras["presenca"] else "NAO",
            estado_atual
        ))