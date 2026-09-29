"""Cucaracha huye-luz NXT con nxt-python (USB).
Uso:
  source .venv/bin/activate
  python python/cucaracha.py  (desde la raiz del repositorio)

Es una demostracion por USB de la misma idea que nxc/cucaracha.nxc. El .nxc
se compila como .rxe y funciona sin computador; esta version Python necesita USB.
Hardware: luz en PORT_3 mirando arriba (LED apagado), ultrasonico en PORT_4 al frente,
  motores en B (izq) y C (der).
Comportamiento: en sombra duerme, con linterna huye en zigzag esquivando paredes.

OJO escala: en NXC el sensor da 0-100; aqui se invierte la lectura cruda
  (0-1023) para que un numero mayor signifique mas luz.
  UMBRAL 55 en NXC no equivale exactamente a 560 aqui: calibra con las muestras.
"""
import random
import time

import nxt.locator
import nxt_usb_patch  # noqa: F401  (permite conectar por USB en este Mac)
from nxt.motor import PORT_B, PORT_C, Motor
from nxt.sensor import PORT_3, PORT_4
from nxt.sensor.generic import Light, Ultrasonic

UMBRAL_LUZ = 560  # decision: mayor que 560 significa mas luz/linterna
PARED_CM = 30     # seguridad: si hay pared a menos de 30 cm, gira

print("Buscando NXT por USB...")
brick = nxt.locator.find()
print(f"Conectado: {brick.get_device_info()}")

left = Motor(brick, PORT_B)
right = Motor(brick, PORT_C)
light = Light(brick, PORT_3)
light.set_illuminated(False)  # LED apagado: mide luz externa
ultra = Ultrasonic(brick, PORT_4)
time.sleep(0.5)


def medir_luz():
    """Convierte el valor crudo: mas luz produce un numero mas grande."""
    return 1023 - light.get_sample()


print("Muestras (tapa y alumbra el sensor):")
for _ in range(10):
    try:
        print(f"luz={medir_luz()} ultra={ultra.get_distance()} cm")
    except Exception as e:
        print(f"lectura fallida: {e}")
    time.sleep(0.3)


def dormir():
    """Deja quietas las dos ruedas cuando esta en sombra."""
    left.brake()
    right.brake()


def huir_recto(seg=0.35, vel=70):
    """Mueve las dos ruedas igual durante un tiempo: avanza recto."""
    left.run(-vel)   # En este chasis, negativo = avanzar (OnRev en NXC).
    right.run(-vel)
    time.sleep(seg)


def girar_huyendo():
    # Ruedas en sentidos opuestos: gira en el mismo lugar para esquivar.
    left.run(-60)
    right.run(60)
    time.sleep(0.45)


def zigzag():
    # Una rueda mas rapida que la otra curva el camino; se elige al azar.
    if random.choice([True, False]):
        left.run(-70)
        right.run(-30)
    else:
        left.run(-30)
        right.run(-70)
    time.sleep(0.25)


try:
    while True:
        # Repite siempre el ciclo: mirar sensores -> decidir -> mover ruedas.
        luz = medir_luz()
        try:
            d = ultra.get_distance()
        except Exception:
            d = 255  # Sin lectura: se trata como espacio libre.

        print(f"luz={luz} d={d}")

        if luz <= UMBRAL_LUZ:
            # SI no llega suficiente luz, parar y esperar otra lectura.
            print("Zzz sombra")
            dormir()
            time.sleep(0.15)
        else:
            # SI hay luz, avisar con sonido y elegir una ruta de huida.
            print("HUYO!")
            brick.play_tone(1200, 80)
            if 0 < d < PARED_CM:
                # Una pared cercana tiene prioridad sobre avanzar.
                girar_huyendo()
            else:
                huir_recto()
                zigzag()
        time.sleep(0.05)
except KeyboardInterrupt:
    pass  # Ctrl+C termina el programa desde el computador.
finally:
    # Se ejecuta incluso al interrumpir: el robot no queda andando.
    left.brake()
    right.brake()
    print("Stop")
