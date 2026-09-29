"""Perrito faldero NXT con nxt-python (USB).
Uso:
  source .venv/bin/activate
  python python/perrito.py  (desde la raiz del repositorio)

Es una demostracion por USB de la idea de nxc/perrito.nxc. El .nxc compilado
funciona dentro del brick; esta version Python necesita el computador.
Hardware: ultrasonico en PORT_4 al frente, tacto en PORT_2 en cabeza/lomo,
  motores en B (izq) y C (der).
  En este chasis, potencia negativa hace avanzar (OnRev en NXC).
Comportamiento:
  - Lejos (>60 cm): espera.
  - A 31-60 cm: se acerca (VELOCIDAD 60), salvo si ya pedia caricias
    y la persona sigue a 35 cm o menos.
  - A <=30 cm: se detiene y pide caricias (ladrido triple).
    Al pulsar el tacto se menea y vuelve a pedir.

Para explicar por BLOQUES:
  BLOQUE 1: ¿veo a alguien? (ultrasonico)
  BLOQUE 2: SI distancia intermedia ENTONCES me acerco
  BLOQUE 3: SI cerca ENTONCES pido mimos + ladro
  BLOQUE 4: SI me tocan ENTONCES meneito feliz
"""
import time

import nxt.locator
import nxt_usb_patch  # noqa: F401  (permite conectar por USB en este Mac)
from nxt.motor import PORT_B, PORT_C, Motor
from nxt.sensor import PORT_2, PORT_4
from nxt.sensor.generic import Touch, Ultrasonic

DETECTA = 60     # cm: mas alla, espera
MIMOS = 30       # cm: aqui entra en modo caricias
SALE_MIMOS = 35  # cm: sigue pidiendo caricias hasta superar 35
VELOCIDAD = 60   # potencia de ambas ruedas al acercarse
PIDE_CADA = 0.8  # segundos minimos entre llamadas mientras pide caricias

print("Buscando NXT por USB...")
brick = nxt.locator.find()
print(f"Conectado: {brick.get_device_info()}")

left = Motor(brick, PORT_B)
right = Motor(brick, PORT_C)
ultra = Ultrasonic(brick, PORT_4)
boton = Touch(brick, PORT_2)
time.sleep(0.5)

print("Muestras (acerca la mano y pulsa el tacto):")
for _ in range(10):
    try:
        d = ultra.get_distance()
    except Exception:
        d = 255
    print(f"d={d} cm tacto={int(bool(boton.get_sample()))}")
    time.sleep(0.3)


def parar():
    """Frena las dos ruedas."""
    left.brake()
    right.brake()


def ladrido_insistente():
    # Tres tonos forman una llamada; las pausas hacen que se distingan.
    brick.play_tone(880, 150)
    time.sleep(0.18)
    brick.play_tone(660, 150)
    time.sleep(0.18)
    brick.play_tone(990, 200)
    time.sleep(0.22)


def meneito():
    # Ruedas opuestas: giro a un lado, al otro y vuelvo al frente.
    print("MIMOS! ^_^")
    parar()
    time.sleep(0.1)
    brick.play_tone(523, 170)
    left.run(-40)
    right.run(40)
    time.sleep(0.18)
    brick.play_tone(659, 340)
    left.run(40)
    right.run(-40)
    time.sleep(0.36)
    brick.play_tone(784, 170)
    left.run(-40)
    right.run(40)
    time.sleep(0.18)
    parar()


def distancia():
    """Devuelve centimetros; 255 representa ausencia de eco o fallo."""
    try:
        return ultra.get_distance()
    except Exception:
        return 255  # 255 = sin eco = libre


try:
    estado = 0  # memoria: 0=espero, 1=me acerco, 2=pido caricias
    ultimo_ladrido = 0  # hora de la ultima llamada para no ladrar sin pausa
    parar()
    while True:
        # En cada vuelta: leer distancia y boton -> elegir estado -> actuar.
        d = distancia()
        tocado = bool(boton.get_sample())
        print(f"d={d} estado={estado} tacto={int(tocado)}")

        # 255 = sin eco. Si marca 0, solo se toma como muy cerca cuando
        # ya habia detectado a alguien. Esto evita arrancar por una lectura rara.
        if d == 255 or d > DETECTA:
            nuevo = 0
        elif d == 0:
            nuevo = 2 if estado in (1, 2) else 0
        else:
            # La franja 31-35 cm conserva el modo caricias si ya estaba en el.
            if d <= MIMOS or (estado == 2 and d <= SALE_MIMOS):
                nuevo = 2
            else:
                nuevo = 1

        if nuevo != estado:
            # Solo al cambiar de estado hace el aviso de entrada.
            estado = nuevo
            ultimo_ladrido = 0  # avisa enseguida al cambiar
            if estado == 0:
                print("ESPERO... VEN...")
            elif estado == 1:
                print("VOY :) GUAU!")
                brick.play_tone(880, 100)
            else:
                print("ACARICIAME <3")
                ladrido_insistente()
                ultimo_ladrido = time.time()

        # Cada estado tiene una accion distinta: esperar, acercarse o pedir.
        if estado == 0:
            parar()
        elif estado == 1:
            # Si la persona esta a distancia intermedia, avanza hacia ella.
            left.run(-VELOCIDAD)  # OnRev en NXC = avanzar en este chasis.
            right.run(-VELOCIDAD)
        else:
            # Si ya esta cerca, se detiene y pide caricias con pausas.
            parar()
            # Python repite el meneito si el boton queda apretado.
            # El .nxc solo cuenta una pulsacion nueva.
            if tocado:
                meneito()
                ultimo_ladrido = time.time()
            elif time.time() - ultimo_ladrido >= PIDE_CADA:
                ladrido_insistente()
                ultimo_ladrido = time.time()

        time.sleep(0.05)
except KeyboardInterrupt:
    pass  # Ctrl+C termina el programa desde el computador.
finally:
    # Frenar tambien si se interrumpe el programa.
    parar()
    print("Stop")
