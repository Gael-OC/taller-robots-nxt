"""Bailarin de palmadas NXT con nxt-python (USB).
Uso:
  source .venv/bin/activate
  python python/palmadas.py  (desde la raiz del repositorio)

Es una demostracion por USB de la idea de nxc/palmadas.nxc. El .nxc compilado
funciona dentro del brick; esta version Python necesita el computador.
Hardware: sonido en PORT_2 (no tapar micro), motores en B y C.
  En este chasis, potencia negativa hace avanzar (OnRev en NXC).
Comportamiento: 1a palmada = baila, 2a palmada = para.

Version SIMPLIFICADA para entender la logica:
  el .nxc toca La Cucaracha entera y omite las primeras notas al escuchar
  para evitar ecos. Aqui suena una melodia corta y no hay ese tiempo ciego.

OJO escala: en NXC el sonido da 0-100; aqui se invierte la lectura cruda
  (0-1023) para que un numero mayor signifique mas ruido.
  UMBRAL 90 en NXC no equivale exactamente a 850 aqui: calibra con las muestras.
"""
import time

import nxt.locator
import nxt_usb_patch  # noqa: F401  (permite conectar por USB en este Mac)
from nxt.motor import PORT_B, PORT_C, Motor
from nxt.sensor import PORT_2
from nxt.sensor.generic import Sound

UMBRAL = 850  # dos lecturas a este nivel cuentan como palmada
REARME = 550  # antes de otra palmada, el ruido debe bajar de este nivel

print("Buscando NXT por USB...")
brick = nxt.locator.find()
print(f"Conectado: {brick.get_device_info()}")

left = Motor(brick, PORT_B)
right = Motor(brick, PORT_C)
micro = Sound(brick, PORT_2)
time.sleep(0.2)


def medir_ruido():
    """Convierte el valor crudo: un sonido mas fuerte da un numero mayor."""
    return 1023 - micro.get_sample()


print("Muestras (aplaude cerca del sensor):")
for _ in range(15):
    print(f"ruido={medir_ruido()}")
    time.sleep(0.2)

bailando = False  # recuerda si esta bailando o esperando
armado = True    # evita contar una sola palmada varias veces
paso = 0  # 0=avanza 1=gira izq 2=retrocede 3=gira der


def parar():
    """Frena ambas ruedas."""
    left.brake()
    right.brake()


def paso_baile(p):
    # El numero de paso elige un movimiento; el bucle fija cuanto dura.
    if p == 0:
        left.run(-70)   # avanza
        right.run(-70)
    elif p == 1:
        left.run(-70)   # gira
        right.run(70)
    elif p == 2:
        left.run(70)    # retrocede
        right.run(70)
    else:
        left.run(70)    # gira al otro lado
        right.run(-70)


def es_palmada():
    """Cuenta una palmada tras 2 lecturas fuertes; espera silencio para rearmar."""
    global armado
    r = medir_ruido()
    print(f"ruido={r} bailando={int(bailando)}")
    if r <= REARME:
        # El sonido volvio a bajar: ya puede llegar una palmada nueva.
        armado = True
        return False
    if r >= UMBRAL and armado:
        time.sleep(0.03)
        r2 = medir_ruido()
        if r2 >= UMBRAL:
            # Queda desarmado hasta que el ruido baje otra vez.
            armado = False
            return True
    return False


try:
    parar()
    while True:
        # Dos estados: espera la primera palmada o ejecuta el baile.
        if not bailando:
            # Una palmada confirmada cambia de ESPERA a BAILE.
            if es_palmada():
                print("1a palmada: BAILO")
                bailando = True
                paso = 0
                brick.play_tone_and_wait(784, 120)  # aviso G5
            time.sleep(0.03)
        else:
            # El numero de paso cambia el movimiento y la nota.
            brick.play_tone(523 + paso * 100, 130)
            paso_baile(paso % 4)
            time.sleep(0.15)
            parar()
            time.sleep(0.02)

            # Solo escucha en esta pausa; una palmada durante el movimiento
            # puede pasar inadvertida. El .nxc tambien escucha en pausas.
            for _ in range(5):
                time.sleep(0.025)
                if es_palmada():
                    print("2a palmada: PARO")
                    bailando = False
                    parar()
                    brick.play_tone_and_wait(262, 300)
                    break
            paso += 1  # la secuencia de 4 movimientos vuelve con paso % 4
except KeyboardInterrupt:
    pass  # Ctrl+C termina el programa desde el computador.
finally:
    # Frenar tambien si se interrumpe el programa.
    parar()
    print("Stop")
