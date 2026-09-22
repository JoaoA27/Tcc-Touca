import time

from config import (
    SENTIDO_ENTRADA,
    TEMPO_TOLERANCIA_FORA_ZONA,
    TIMEOUT_TRACK_CONTADOR,
)


class ContadorPessoas:

    def __init__(self, tempo_minimo_zona):

        self.tempo_minimo_zona = tempo_minimo_zona

        self.estados = {}

        self.entradas = 0
        self.saidas = 0

    # =====================================================
    # NOVO ESTADO
    # =====================================================

    def _novo_estado(self, agora):

        return {
            "dentro_zona": False,

            "inicio_zona": None,

            "lado_entrada": None,

            "ultimo_lado": None,

            "fora_desde": None,

            "ultimo_visto": agora,
        }

    # =====================================================
    # INICIAR PASSAGEM
    # =====================================================

    def _iniciar_passagem(
        self,
        estado,
        lado,
        agora
    ):

        estado["dentro_zona"] = True

        estado["inicio_zona"] = agora

        estado["fora_desde"] = None

        if lado != 0:

            estado["lado_entrada"] = lado
            estado["ultimo_lado"] = lado

        else:

            estado["lado_entrada"] = None
            estado["ultimo_lado"] = None

    # =====================================================
    # ENCERRAR PASSAGEM
    # =====================================================

    def _encerrar_passagem(self, estado):

        estado["dentro_zona"] = False

        estado["inicio_zona"] = None

        estado["lado_entrada"] = None

        estado["ultimo_lado"] = None

        estado["fora_desde"] = None

    # =====================================================
    # CLASSIFICAR MOVIMENTO
    # =====================================================

    def _classificar(
        self,
        lado_entrada,
        lado_saida
    ):

        movimento = (
            lado_entrada,
            lado_saida
        )

        if movimento == SENTIDO_ENTRADA:

            return "entrada"

        sentido_saida = (
            SENTIDO_ENTRADA[1],
            SENTIDO_ENTRADA[0]
        )

        if movimento == sentido_saida:

            return "saida"

        return None

    # =====================================================
    # ATUALIZAR TRACK
    # =====================================================

    def atualizar(
        self,
        track_id,
        dentro,
        lado,
        agora=None
    ):

        if agora is None:
            agora = time.monotonic()

        # Cria estado para novo ID
        if track_id not in self.estados:

            self.estados[track_id] = (
                self._novo_estado(agora)
            )

        estado = self.estados[track_id]

        estado["ultimo_visto"] = agora

        # =================================================
        # PESSOA DENTRO DA ZONA
        # =================================================

        if dentro:

            estado["fora_desde"] = None

            # Entrou agora na zona
            if not estado["dentro_zona"]:

                self._iniciar_passagem(
                    estado,
                    lado,
                    agora
                )

            # Caso tenha entrado exatamente sobre a linha
            if (
                estado["lado_entrada"] is None
                and lado != 0
            ):

                estado["lado_entrada"] = lado

            # Guarda último lado válido
            if lado != 0:

                estado["ultimo_lado"] = lado

            return None

        # =================================================
        # PESSOA FORA DA ZONA
        # =================================================

        if estado["dentro_zona"]:

            # Primeiro frame fora
            if estado["fora_desde"] is None:

                estado["fora_desde"] = agora

            tempo_fora = (
                agora
                -
                estado["fora_desde"]
            )

            # Espera um pouco para evitar
            # oscilações na borda da zona
            if (
                tempo_fora
                <
                TEMPO_TOLERANCIA_FORA_ZONA
            ):

                return None

            # =============================================
            # PASSAGEM CONFIRMADA
            # =============================================

            tempo_na_zona = (
                estado["fora_desde"]
                -
                estado["inicio_zona"]
            )

            lado_entrada = (
                estado["lado_entrada"]
            )

            # Preferimos o lado atual.
            # Se for 0, usamos o último lado válido.
            lado_saida = (
                lado
                if lado != 0
                else estado["ultimo_lado"]
            )

            evento = None

            # Só considera se ficou tempo suficiente
            if (
                tempo_na_zona
                >=
                self.tempo_minimo_zona
                and lado_entrada is not None
                and lado_saida is not None
            ):

                # Só conta se realmente mudou de lado
                if lado_entrada != lado_saida:

                    tipo = self._classificar(
                        lado_entrada,
                        lado_saida
                    )

                    if tipo == "entrada":

                        self.entradas += 1

                    elif tipo == "saida":

                        self.saidas += 1

                    if tipo is not None:

                        evento = {
                            "track_id": track_id,

                            "tipo": tipo,

                            "lado_origem":
                                lado_entrada,

                            "lado_destino":
                                lado_saida,

                            "tempo_zona":
                                round(
                                    tempo_na_zona,
                                    2
                                ),
                        }

            # A passagem acabou,
            # tenha contado ou não.
            self._encerrar_passagem(
                estado
            )

            return evento

        return None

    # =====================================================
    # LIMPEZA DE IDs ANTIGOS
    # =====================================================

    def limpar_tracks_antigos(
        self,
        agora=None
    ):

        if agora is None:
            agora = time.monotonic()

        ids_remover = []

        for (
            track_id,
            estado
        ) in self.estados.items():

            tempo_sem_ver = (
                agora
                -
                estado["ultimo_visto"]
            )

            if (
                tempo_sem_ver
                >=
                TIMEOUT_TRACK_CONTADOR
            ):

                ids_remover.append(
                    track_id
                )

        for track_id in ids_remover:

            del self.estados[track_id]