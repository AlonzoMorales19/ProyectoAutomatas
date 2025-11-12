import sys
from flask import Flask, request, jsonify
from flask_cors import CORS


# Definicion de Nodos
class Nodo:
    def __str__(self):
        return self.__class__.__name__


class Hoja(Nodo):
    def __init__(self, simbolo, posicion):
        self.simbolo = simbolo
        self.posicion = posicion
        self.id = f"h{posicion}"

    def __str__(self):
        return f"Hoja({self.simbolo}, {self.posicion})"


class Union(Nodo):
    def __init__(self, izquierda, derecha, id):
        self.izquierda = izquierda
        self.derecha = derecha
        self.id = id

    def __str__(self):
        return f"Union({self.izquierda}, {self.derecha})"


class Concat(Nodo):
    def __init__(self, izquierda, derecha, id):
        self.izquierda = izquierda
        self.derecha = derecha
        self.id = id

    def __str__(self):
        return f"Concat({self.izquierda}, {self.derecha})"


class Estrella(Nodo):
    def __init__(self, hijo, id):
        self.hijo = hijo
        self.id = id

    def __str__(self):
        return f"Estrella({self.hijo})"


# Clase que analiza la expresion
class AnalizadorRegex:
    def __init__(self):
        self.expresion = ""
        self.posicion = 0
        self.numHoja = 1
        self.mapaHojas = {}
        self.alfabeto = set()
        self.idInterno = 0

    def nuevoId(self):
        self.idInterno += 1
        return f"n{self.idInterno}"

    def parse(self, expresion):
        self.expresion = expresion.replace('+', '|')
        self.expresion = self.expresion.replace(' ', '')
        self.posicion = 0
        self.numHoja = 1
        self.mapaHojas = {}
        self.alfabeto = set()
        self.idInterno = 0
        if not self.expresion:
            raise ValueError("Expresión vacía")
        expresion_aumentada = f"({self.expresion})#"
        self.expresion = expresion_aumentada
        arbol = self.Expresion()
        if self.posicion < len(self.expresion):
            raise ValueError(
                f"Error'{self.expresion[self.posicion:]}'")
        self.hoja_aceptacion_pos = self.numHoja - 1
        return arbol, self.mapaHojas, self.alfabeto, self.hoja_aceptacion_pos

    def Expresion(self):
        nodo_izq = self.Termino()
        while self.verActual() == '|':
            self.avanzar('|')
            nodo_der = self.Termino()
            nodo_izq = Union(nodo_izq, nodo_der, self.nuevoId())
        return nodo_izq

    def Termino(self):
        nodo_izq = self.FactorEs()
        while self.verActual() and self.verActual() not in '|)':
            nodo_der = self.FactorEs()
            nodo_izq = Concat(nodo_izq, nodo_der, self.nuevoId())
        return nodo_izq

    def FactorEs(self):
        nodo_base = self.difinicion()
        if self.verActual() == '*':
            self.avanzar('*')
            nodo_base = Estrella(nodo_base, self.nuevoId())
        return nodo_base

    def difinicion(self):
        SimboloActual = self.verActual()
        if SimboloActual == '(':
            self.avanzar('(')
            nodo = self.Expresion()
            self.avanzar(')')
            return nodo
        elif ('a' <= SimboloActual <= 'z') or \
            ('A' <= SimboloActual <= 'Z') or \
            ('0' <= SimboloActual <= '9') or \
                SimboloActual == '#' or \
                SimboloActual == '.':
            self.avanzar(SimboloActual)
            nodo = Hoja(SimboloActual, self.numHoja)
            self.mapaHojas[self.numHoja] = nodo
            if SimboloActual != '#':
                self.alfabeto.add(SimboloActual)
            self.numHoja += 1
            return nodo
        else:
            raise ValueError(f"Token inesperado: '{SimboloActual}'")

    def verActual(self):
        return self.expresion[self.posicion] if self.posicion < len(self.expresion) else None

    def avanzar(self, esperado):
        if self.posicion == len(self.expresion):
            raise ValueError(
                f"Se esperaba '{esperado}' pero se encontró el fin")
        if self.verActual() == esperado:
            self.posicion += 1
        else:
            raise ValueError(
                f"Se esperaba '{esperado}' pero se encontró '{self.verActual()}'")


# Clase que construye el AFD
class CreadorAFD:
    def __init__(self, arbol, mapaHojas, alfabeto, posAceptacion):
        self.arbol = arbol
        self.mapaHojas = mapaHojas
        self.alfabeto = sorted(list(alfabeto))
        self.posAceptacion = posAceptacion
        self.anulables = {}
        self.primeraPos = {}
        self.ultimaPos = {}
        self.siguientePos = {i: set() for i in range(1, len(mapaHojas) + 1)}
        self.posAEstados = {}
        self.transiciones = {}
        self.estadoInicial = None
        self.estadosAceptacion = set()
        self.numEstados = 0

    def calcularFunciones(self, nodo):
        if isinstance(nodo, Hoja):
            self.anulables[nodo] = False
            self.primeraPos[nodo] = {nodo.posicion}
            self.ultimaPos[nodo] = {nodo.posicion}
        elif isinstance(nodo, Union):
            self.calcularFunciones(nodo.izquierda)
            self.calcularFunciones(nodo.derecha)
            self.anulables[nodo] = self.anulables[nodo.izquierda] or self.anulables[nodo.derecha]
            self.primeraPos[nodo] = self.primeraPos[nodo.izquierda].union(
                self.primeraPos[nodo.derecha])
            self.ultimaPos[nodo] = self.ultimaPos[nodo.izquierda].union(
                self.ultimaPos[nodo.derecha])
        elif isinstance(nodo, Concat):
            self.calcularFunciones(nodo.izquierda)
            self.calcularFunciones(nodo.derecha)
            self.anulables[nodo] = self.anulables[nodo.izquierda] and self.anulables[nodo.derecha]
            self.primeraPos[nodo] = self.primeraPos[nodo.izquierda].union(
                self.primeraPos[nodo.derecha]) if self.anulables[nodo.izquierda] else self.primeraPos[nodo.izquierda]
            self.ultimaPos[nodo] = self.ultimaPos[nodo.derecha].union(
                self.ultimaPos[nodo.izquierda]) if self.anulables[nodo.derecha] else self.ultimaPos[nodo.derecha]
            for pos_i in self.ultimaPos[nodo.izquierda]:
                self.siguientePos[pos_i].update(self.primeraPos[nodo.derecha])
        elif isinstance(nodo, Estrella):
            self.calcularFunciones(nodo.hijo)
            self.anulables[nodo] = True
            self.primeraPos[nodo] = self.primeraPos[nodo.hijo]
            self.ultimaPos[nodo] = self.ultimaPos[nodo.hijo]
            for pos_i in self.ultimaPos[nodo.hijo]:
                self.siguientePos[pos_i].update(self.primeraPos[nodo.hijo])

    def crearAFD(self):
        self.calcularFunciones(self.arbol)
        q0_set = frozenset(
            self.primeraPos[self.arbol]) if self.primeraPos[self.arbol] else frozenset([-1])
        self.estadoInicial = self.getNombreEstado(q0_set)
        cola_trabajo = [q0_set]
        estados_vistos = {q0_set}
        while cola_trabajo:
            estado_actual_set = cola_trabajo.pop(0)
            nombre_estado_actual = self.getNombreEstado(
                estado_actual_set)
            if self.posAceptacion in estado_actual_set or (self.anulables[self.arbol] and estado_actual_set == frozenset([-1])):
                self.estadosAceptacion.add(nombre_estado_actual)
            for simbolo in self.alfabeto:
                nuevo_estado_set = set().union(
                    *(self.siguientePos[pos] for pos in estado_actual_set if pos != -1 and self.mapaHojas[pos].simbolo == simbolo))
                if nuevo_estado_set:
                    nuevo_estado_frozenset = frozenset(nuevo_estado_set)
                    nombre_nuevo_estado = self.getNombreEstado(
                        nuevo_estado_frozenset)
                    self.transiciones[(
                        nombre_estado_actual, simbolo)] = nombre_nuevo_estado
                    if nuevo_estado_frozenset not in estados_vistos:
                        estados_vistos.add(nuevo_estado_frozenset)
                        cola_trabajo.append(nuevo_estado_frozenset)
        estados_a_posiciones = {v: k for k,
                                v in self.posAEstados.items()}
        return {
            "alfabeto": self.alfabeto,
            "estados": sorted(list(self.posAEstados.values()), key=lambda q: int(q.replace('q', ''))),
            "estado_inicial": self.estadoInicial,
            "estados_aceptacion": sorted(list(self.estadosAceptacion), key=lambda q: int(q.replace('q', ''))),
            "transiciones": {f"{estado}_{sym}": destino for (estado, sym), destino in self.transiciones.items()},
            "estados_a_posiciones": estados_a_posiciones
        }

    def getNombreEstado(self, setPosiciones):
        if setPosiciones not in self.posAEstados:
            self.posAEstados[setPosiciones] = f"q{self.numEstados}"
            self.numEstados += 1
        return self.posAEstados[setPosiciones]


# Simulador del AFD
class Simulador:
    def __init__(self, transiciones, inicial, aceptacion):
        self.transiciones = transiciones
        self.estado_inicial = inicial
        self.estados_aceptacion = aceptacion

    def probarCadena(self, cadena):
        if cadena == "":
            es_valido = self.estado_inicial in self.estados_aceptacion
            mensaje = f"Inicio en {self.estado_inicial} ({'Aceptación' if es_valido else 'No Aceptación'}). Cadena vacía {'VÁLIDA' if es_valido else 'INVÁLIDA'}."
            return es_valido, [mensaje]
        estado_actual = self.estado_inicial
        pasos = [f"Inicio en estado {estado_actual}"]
        for simbolo in cadena:
            clave_transicion = f"{estado_actual}_{simbolo}"
            if clave_transicion in self.transiciones:
                estado_siguiente = self.transiciones[clave_transicion]
                pasos.append(
                    f"Leyó '{simbolo}', pasó de {estado_actual} -> {estado_siguiente}")
                estado_actual = estado_siguiente
            else:
                pasos.append(
                    f"Error: No hay transición desde {estado_actual} con '{simbolo}'")
                return False, "\n".join(pasos)
        es_valido = estado_actual in self.estados_aceptacion
        pasos.append(
            f"Fin de cadena. Estado final {estado_actual} ({'Aceptación' if es_valido else 'No Aceptación'})")
        return es_valido, "\n".join(pasos)


def formatearSet(s):
    if s == frozenset([-1]):
        return "{ε}"
    if not s:
        return "Ø"
    return "{" + ", ".join(map(str, sorted(list(s)))) + "}"


def DatosArbol(nodo, anulables, primeraPos, ultimaPos):
    nodos = []
    ejes = []

    def recorrer(n):
        n_anulable = anulables.get(n, False)
        anulable_str = "V" if n_anulable else "F"
        if isinstance(n, Hoja):
            n_first = primeraPos.get(n, {n.posicion})
            n_last = ultimaPos.get(n, {n.posicion})
            first_str = formatearSet(n_first)
            last_str = formatearSet(n_last)
            label = f"{first_str} <b>{n.simbolo}</b> {last_str}\n<code>({n.posicion}{anulable_str})</code>"
            nodos.append({"id": n.id, "label": label, "shape": "circle",
                         "color": "#f9f9f9", "font": {"color": "#333"}})
            return n.id
        n_first = primeraPos.get(n, set())
        n_last = ultimaPos.get(n, set())
        first_str = formatearSet(n_first)
        last_str = formatearSet(n_last)
        op_label = "|" if isinstance(n, Union) else "·" if isinstance(
            n, Concat) else "*" if isinstance(n, Estrella) else "?"
        label = f"{first_str} <b>{op_label}</b> {last_str}\n<code>({anulable_str})</code>"
        nodos.append({"id": n.id, "label": label, "shape": "circle",
                     "color": "#4a69bd", "font": {"color": "white"}})
        if isinstance(n, Estrella):
            hijo_id = recorrer(n.hijo)
            ejes.append({"from": n.id, "to": hijo_id})
        else:
            izq_id = recorrer(n.izquierda)
            der_id = recorrer(n.derecha)
            ejes.append({"from": n.id, "to": izq_id})
            ejes.append({"from": n.id, "to": der_id})
        return n.id
    recorrer(nodo)
    return {"nodes": nodos, "edges": ejes}


def afdjs(afd_data):
    nodos = []
    ejes = []
    estados_a_pos_str = afd_data.get("estados_a_posiciones_str", {})

    niveles = {}
    cola = []
    estado_inicial = afd_data.get("estado_inicial")

    if estado_inicial:
        niveles[estado_inicial] = 1
        cola = [(estado_inicial, 1)]

    transiciones_map = {}
    for clave, destino in afd_data.get("transiciones", {}).items():
        origen, _ = clave.split('_', 1)
        if origen not in transiciones_map:
            transiciones_map[origen] = []
        if destino not in transiciones_map[origen]:
            transiciones_map[origen].append(destino)

    vistos = {estado_inicial}
    head = 0
    while head < len(cola):
        estado_actual, nivel_actual = cola[head]
        head += 1

        for estado_siguiente in transiciones_map.get(estado_actual, []):
            if estado_siguiente not in vistos:
                vistos.add(estado_siguiente)
                niveles[estado_siguiente] = nivel_actual + 1
                cola.append((estado_siguiente, nivel_actual + 1))

    for estado_nombre in afd_data["estados"]:
        es_aceptacion = (estado_nombre in afd_data["estados_aceptacion"])
        es_inicial = (estado_nombre == afd_data["estado_inicial"])
        label_nodo = estados_a_pos_str.get(estado_nombre, "Error")

        nivel_nodo = niveles.get(estado_nombre, 1)

        nodo = {
            "id": estado_nombre, "label": label_nodo,
            "level": nivel_nodo,
            "x": nivel_nodo * 220,
            "fixed": {"x": True}
        }

        if es_inicial and es_aceptacion:
            nodo.update({"color": "#03A9F4", "font": {
                        "color": "white", "size": 14}})
        elif es_aceptacion:
            nodo.update({"color": "#4CAF50",
                        "font": {"color": "white", "size": 14}})
        elif es_inicial:
            nodo.update({"color": "#FFC107", "font": {
                        "color": "black", "size": 14}})
        else:
            nodo.update(
                {"shape": "circle", "color": "#f0f2f5", "font": {"size": 14}})

        nodos.append(nodo)

    ejes_agrupados = {}
    for clave, destino_nombre in afd_data["transiciones"].items():
        origen_nombre, simbolo = clave.split('_', 1)
        tupla_eje = (origen_nombre, destino_nombre)
        if tupla_eje not in ejes_agrupados:
            ejes_agrupados[tupla_eje] = []
        ejes_agrupados[tupla_eje].append(simbolo)

    for (origen_nombre, destino_nombre), simbolos in ejes_agrupados.items():
        ejes.append({"from": origen_nombre, "to": destino_nombre, "label": ", ".join(
            simbolos), "arrows": "to", "font": {"align": "horizontal"}})

    if afd_data["estado_inicial"]:
        nodos.append({
            "id": "start_node", "label": "Inicio",
            "shape": "text", "font": {"size": 16},
            "level": 0,
            "x": 0, "fixed": {"x": True}
        })

        ejes.append({"from": "start_node", "to": afd_data["estado_inicial"], "arrows": "to", "color": {
                    "color": "#333"}})

    return {"nodes": nodos, "edges": ejes}


def siguientejs(siguientePos_dict, mapaHojas_dict):
    tabla = []
    for pos in sorted(siguientePos_dict.keys()):
        simbolo = mapaHojas_dict.get(pos, None)
        if simbolo:
            simbolo_str = simbolo.simbolo
            siguientePstr = formatearSet(siguientePos_dict[pos])
            tabla.append({"posicion": pos, "simbolo": simbolo_str,
                         "siguiente": siguientePstr})
    return tabla


# Construir el AFN
def afnjs(constructor, firstpos_root):
    mapaHojas = constructor.mapaHojas
    siguientePos = constructor.siguientePos
    posAceptacion = constructor.posAceptacion
    q0_set = frozenset(firstpos_root)

    niveles = {}
    cola_bfs = []

    if q0_set:
        niveles[q0_set] = 1
        cola_bfs = [(q0_set, 1)]

    vistos_bfs = {q0_set}
    transiciones_map_afn = {}

    head = 0
    while head < len(cola_bfs):
        estado_actual_set, nivel_actual = cola_bfs[head]
        head += 1

        transiciones_map_afn[estado_actual_set] = []

        for pos in estado_actual_set:
            if pos == -1:
                continue
            simbolo = mapaHojas[pos].simbolo
            if simbolo == '#':
                continue

            destinos_set = siguientePos.get(pos, set())

            if destinos_set:
                destino_frozenset = frozenset(destinos_set)

                if destino_frozenset not in transiciones_map_afn[estado_actual_set]:
                    transiciones_map_afn[estado_actual_set].append(
                        destino_frozenset)

                if destino_frozenset not in vistos_bfs:
                    vistos_bfs.add(destino_frozenset)
                    niveles[destino_frozenset] = nivel_actual + 1
                    cola_bfs.append((destino_frozenset, nivel_actual + 1))

    nodos = []
    ejes = []
    estados_map = {}
    contador_estados = 0

    def obtener_nombre_estado_afn(pos_set):
        nonlocal contador_estados
        if pos_set not in estados_map:
            id_estado = f"n{contador_estados}"
            estados_map[pos_set] = id_estado
            contador_estados += 1

            label_nodo = formatearSet(pos_set)
            es_final = posAceptacion in pos_set
            es_inicial = pos_set == q0_set
            nivel_nodo = niveles.get(pos_set, 1)

            nodo = {
                "id": id_estado, "label": label_nodo,
                "shape": "circle", "level": nivel_nodo,
                "x": nivel_nodo * 220,
                "fixed": {"x": True}
            }

            if es_inicial and es_final:
                nodo.update({"color": "#03A9F4", "font": {"color": "white"}})
            elif es_final:
                nodo.update({"color": "#4CAF50", "font": {"color": "white"}})
            elif es_inicial:
                nodo.update({"color": "#FFC107"})
            else:
                nodo.update(
                    {"shape": "circle", "color": "#E0E0E0", "font": {"color": "#333333", "size": 14}})

            nodos.append(nodo)

        return estados_map[pos_set]

    for estado_actual_set in vistos_bfs:
        nombre_estado_actual = obtener_nombre_estado_afn(estado_actual_set)

        for pos in estado_actual_set:
            if pos == -1:
                continue
            simbolo = mapaHojas[pos].simbolo
            if simbolo == '#':
                continue

            destinos_set = siguientePos.get(pos, set())
            if destinos_set:
                destino_frozenset = frozenset(destinos_set)
                nombre_destino = obtener_nombre_estado_afn(destino_frozenset)

                ejes.append({
                    "from": nombre_estado_actual,
                    "to": nombre_destino,
                    "label": simbolo,
                    "arrows": "to"
                })

    nombre_q0 = obtener_nombre_estado_afn(q0_set)

    nodos.append({
        "id": "start_node_afn", "label": "Inicio",
        "shape": "text", "font": {"size": 16},
        "level": 0,
        "x": 0, "fixed": {"x": True}
    })

    ejes.append({"from": "start_node_afn", "to": nombre_q0,
                "arrows": "to", "color": {"color": "#333"}})

    ejes_agrupados_dict = {}
    for eje in ejes:
        tupla_eje = (eje["from"], eje["to"])
        if tupla_eje not in ejes_agrupados_dict:
            ejes_agrupados_dict[tupla_eje] = set()
        if "label" in eje:
            ejes_agrupados_dict[tupla_eje].add(eje["label"])

    ejes_finales = []
    for (origen, destino), simbolos in ejes_agrupados_dict.items():
        if not simbolos:
            ejes_finales.append(
                {"from": origen, "to": destino, "arrows": "to", "color": {"color": "#333"}})
        else:
            ejes_finales.append({"from": origen, "to": destino, "label": ", ".join(
                sorted(list(simbolos))), "arrows": "to"})

    return {"nodes": nodos, "edges": ejes_finales}


app = Flask(__name__)
CORS(app)


@app.route('/analizar', methods=['POST'])
def procesarAnalisis():
    datos = request.json
    expresion = datos.get('expresion')
    cadenas = datos.get('cadenas', [])

    try:
        parser = AnalizadorRegex()
        arbol, mapaHojas, alfabeto, posAceptacion = parser.parse(expresion)
        constructor = CreadorAFD(arbol, mapaHojas, alfabeto, posAceptacion)

        afd_data = constructor.crearAFD()

        simulador = Simulador(
            afd_data["transiciones"], afd_data["estado_inicial"], afd_data["estados_aceptacion"])
        resultados_validacion = []
        for cadena in cadenas:
            es_valida, pasos = simulador.probarCadena(cadena)
            resultados_validacion.append(
                {"cadena": cadena, "esValida": es_valida, "historial": pasos})

        datosArbol = DatosArbol(
            arbol, constructor.anulables, constructor.primeraPos, constructor.ultimaPos)
        datosSiguienteP = siguientejs(
            constructor.siguientePos, constructor.mapaHojas)

        estados_a_pos_str = {
            estado: formatearSet(pos_set)
            for estado, pos_set in afd_data["estados_a_posiciones"].items()
        }
        afd_data_para_enviar = afd_data.copy()
        afd_data_para_enviar["estados_a_posiciones_str"] = estados_a_pos_str
        del afd_data_para_enviar["estados_a_posiciones"]

        graficoAFD = afdjs(afd_data_para_enviar)

        graficoAFN = afnjs(
            constructor, constructor.primeraPos[arbol])

        return jsonify({
            'datos_arbol': datosArbol,
            'datos_afd': afd_data_para_enviar,
            'grafico_afd': graficoAFD,
            'grafico_afn': graficoAFN,
            'resultados_validacion': resultados_validacion,
            'tabla_siguienteP': datosSiguienteP
        })

    except ValueError as e:
        return jsonify({'error': f" {str(e)}"}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f"Error interno del servidor: {str(e)}"}), 500


if __name__ == '__main__':
    print("Servidor iniciado en http://127.0.0.1:5000")
    print("Abre el archivo 'visual.html' en tu navegador.")
    app.run(debug=True, port=5000)
