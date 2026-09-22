import sqlite3

from datetime import datetime, timezone

from config import DATABASE_PATH


class Database:

    def __init__(self):

        self.database_path = DATABASE_PATH

        self.criar_tabelas()

    # =========================
    # CONEXÃO
    # =========================

    def _conectar(self):

        return sqlite3.connect(
            self.database_path
        )

    # =========================
    # CRIAR TABELAS
    # =========================

    def criar_tabelas(self):

        with self._conectar() as conexao:

            cursor = conexao.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS eventos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    event_id TEXT
                    NOT NULL
                    UNIQUE,

                    camera_id TEXT
                    NOT NULL,

                    tipo TEXT
                    NOT NULL
                    CHECK (
                        tipo IN (
                            'entrada',
                            'saida'
                        )
                    ),

                    timestamp TEXT
                    NOT NULL,

                    recebido_em TEXT
                    NOT NULL
                )
                """
            )

            conexao.commit()

        print(
            f"Banco carregado: "
            f"{self.database_path}"
        )

    # =========================
    # SALVAR EVENTO
    # =========================

    def salvar_evento(
        self,
        event_id,
        camera_id,
        tipo,
        timestamp
    ):

        recebido_em = datetime.now(
            timezone.utc
        ).isoformat()

        try:

            with self._conectar() as conexao:

                cursor = conexao.cursor()

                cursor.execute(
                    """
                    INSERT INTO eventos (
                        event_id,
                        camera_id,
                        tipo,
                        timestamp,
                        recebido_em
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        camera_id,
                        tipo,
                        timestamp,
                        recebido_em,
                    )
                )

                conexao.commit()

            return True

        except sqlite3.IntegrityError:

            # Um event_id já existente
            # não será salvo novamente.
            return False