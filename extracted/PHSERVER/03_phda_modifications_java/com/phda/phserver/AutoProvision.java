package com.phda.phserver;

import android.content.Context;

import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Auto-provisionamento do PHSERVER.
 *
 * Assim que o servidor MariaDB sobe (no boot via {@code AutoStart} ou ao abrir
 * o app via {@code LockActivity}), esta classe garante de forma idempotente:
 *
 * <ul>
 *   <li>banco de dados {@code pdvpro};</li>
 *   <li>usuario {@code pdvpro} / senha {@code pdvpro} em {@code 'localhost'} e {@code '%'};</li>
 *   <li>{@code GRANT ALL PRIVILEGES ON *.*} ... {@code WITH GRANT OPTION} (admin total);</li>
 *   <li>escuta em {@code 0.0.0.0} (preference address = "all") para uso remoto.</li>
 * </ul>
 *
 * Tudo roda em uma thread daemon que aguarda o servidor aceitar conexoes
 * (retry por alguns minutos, pois a primeira execucao instala o MariaDB).
 * Conecta como administrador {@code root} (sem senha, padrao das builds esminis)
 * via {@link MySqlMiniClient}. Nunca lanca excecao para fora.
 */
public final class AutoProvision {

    // Alvos solicitados.
    private static final String DB_NAME   = "pdvpro";
    private static final String DB_USER   = "pdvpro";
    private static final String DB_PASS   = "pdvpro";

    // Conexao de administrador (padrao das builds esminis: root sem senha).
    private static final String ADMIN_HOST = "127.0.0.1";
    private static final int    ADMIN_PORT = 3306;
    private static final String ADMIN_USER = "root";
    private static final String ADMIN_PASS = "";

    // Janela de espera ate o servidor aceitar conexoes.
    private static final int  MAX_ATTEMPTS    = 120;   // 120 x 3s = ~6 min
    private static final long ATTEMPT_DELAY_MS = 3000L;
    private static final int  CONNECT_TIMEOUT_MS = 4000;

    private static final AtomicBoolean RUNNING = new AtomicBoolean(false);

    private AutoProvision() {}

    /** Chamado pelo receiver de boot ({@code AutoStart}). */
    public static void onBoot(Context context) {
        start(context);
    }

    /** Chamado ao abrir o app ({@code LockActivity}). */
    public static void onAppStart(Context context) {
        start(context);
    }

    private static void start(Context context) {
        if (context == null) return;
        final Context app = context.getApplicationContext() != null
                ? context.getApplicationContext() : context;

        // Garante a escuta em 0.0.0.0 (uso remoto). E uma preference persistida,
        // entao vale para esta e para as proximas inicializacoes do servidor.
        try {
            ServerConfigHelper.setAddress(app, "all");
        } catch (Throwable ignored) {}

        // Evita rodar duas threads ao mesmo tempo (boot + abertura do app).
        if (!RUNNING.compareAndSet(false, true)) {
            return;
        }

        Thread t = new Thread(new Runnable() {
            @Override public void run() {
                try {
                    provision();
                } catch (Throwable ignored) {
                    // Nunca propaga: provisionamento jamais pode quebrar o app.
                } finally {
                    RUNNING.set(false);
                }
            }
        }, "PHSERVER-AutoProvision");
        t.setDaemon(true);
        try {
            t.start();
        } catch (Throwable ignored) {
            RUNNING.set(false);
        }
    }

    private static void provision() {
        // 1) Espera o servidor aceitar conexoes (a 1a execucao instala o MariaDB).
        boolean ready = false;
        for (int i = 0; i < MAX_ATTEMPTS; i++) {
            if (serverReady()) {
                ready = true;
                break;
            }
            try {
                Thread.sleep(ATTEMPT_DELAY_MS);
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                return;
            }
        }
        if (!ready) return;

        // 2) Cria banco, usuario, concede privilegios totais (idempotente).
        String userLocal = "'" + DB_USER + "'@'localhost'";
        String userAny   = "'" + DB_USER + "'@'%'";

        String[] statements = new String[] {
            "CREATE DATABASE IF NOT EXISTS `" + DB_NAME + "` "
                + "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci",

            "CREATE USER IF NOT EXISTS " + userLocal
                + " IDENTIFIED BY '" + DB_PASS + "'",
            "CREATE USER IF NOT EXISTS " + userAny
                + " IDENTIFIED BY '" + DB_PASS + "'",

            // Garante a senha mesmo que o usuario ja existisse.
            "ALTER USER " + userLocal + " IDENTIFIED BY '" + DB_PASS + "'",
            "ALTER USER " + userAny   + " IDENTIFIED BY '" + DB_PASS + "'",

            // Privilegios totais (admin) em todos os bancos, com GRANT OPTION.
            "GRANT ALL PRIVILEGES ON *.* TO " + userLocal + " WITH GRANT OPTION",
            "GRANT ALL PRIVILEGES ON *.* TO " + userAny   + " WITH GRANT OPTION",

            "FLUSH PRIVILEGES"
        };

        for (int i = 0; i < statements.length; i++) {
            try {
                MySqlMiniClient.executeStatement(
                        ADMIN_HOST, ADMIN_PORT, ADMIN_USER, ADMIN_PASS,
                        statements[i], 8000);
            } catch (Throwable ignored) {
                // Segue para o proximo; comandos sao idempotentes.
            }
        }
    }

    /** True se o servidor responde a um SELECT 1 como root. */
    private static boolean serverReady() {
        try {
            MySqlMiniClient.QueryResult r = MySqlMiniClient.executeQuery(
                    ADMIN_HOST, ADMIN_PORT, ADMIN_USER, ADMIN_PASS,
                    "SELECT 1", CONNECT_TIMEOUT_MS);
            return r != null && !r.isError();
        } catch (Throwable th) {
            return false;
        }
    }
}
