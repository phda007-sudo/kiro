# PHSERVER 10.3.8 — build PDVPRO

Build do PHSERVER (derivado de `SERVIDOR MARIA DB.apk`, `com.esminis.server.mariadb`)
com as automações pedidas.

## Downloads diretos

- **APK já compilado e assinado (v1+v2+v3):**
  [`PHSERVER-10.3.8-pdvpro.apk`](./PHSERVER-10.3.8-pdvpro.apk?raw=true)
- **Código-fonte completo (engenharia reversa + modificações + script de build):**
  [`PHSERVER-source-completo.zip`](./PHSERVER-source-completo.zip?raw=true)

> Dica: nesta página do GitHub, clique no arquivo e depois em **Download** /
> **Raw**. Os links acima com `?raw=true` já forçam o download direto.

## O que mudou nesta build

1. **Senhas mascaradas** — as telas de PIN `2394` (acesso), `4872` (configurações)
   e `9652` (parar servidor) agora exibem `•/*` ao digitar
   (`setTransformationMethod(PasswordTransformationMethod)`).

2. **Armazenamento interno privado (zero permissão)** — os dados do banco passam a
   ficar em `getFilesDir()/phserver` (interno e privado do app). Com isso:
   - A tela **"CONCEDER permissão de arquivos"** nunca mais aparece
     (`PermissionRequester.hasPermission` forçado para `true`).
   - A permissão `WRITE_EXTERNAL_STORAGE` foi removida do `AndroidManifest`.
   - Máxima compatibilidade. **Atenção:** desinstalar o app apaga os dados —
     faça export/backup quando precisar (em servidor dedicado/kiosk costuma ser ok).

3. **Auto-instalação do MariaDB 10.3.8 + auto-start no boot** — uma nova
   `PhdaApplication` roda um `Bootstrap` logo na criação do processo (inclusive
   após o **BOOT** do aparelho, via o receiver `BOOT_COMPLETED`). O Bootstrap:
   - escolhe e **instala automaticamente o pacote 10.3.8** embutido em
     `assets/packages/259.7z` (arm) / `260` (x86) — equivale a clicar no botão de
     instalar daquela tela de seleção de versão;
   - liga "iniciar no boot" (`startOnBoot=true`);
   - liga a escuta em `0.0.0.0` (`address="all"`) para **acesso remoto**;
   - sobe o servidor em foreground.

   **Início no boot garantido:** `ServerPreferences.isStartOnBoot()` foi forçado
   para `true` e o receiver `AutoStart` foi marcado `enabled/exported`. Assim o
   servidor sobe sozinho após ligar o aparelho, sem depender de timing nem de
   preferência salva (o receiver de boot consulta esse método diretamente).

4. **Banco/usuário criados automaticamente** — assim que o servidor responde em
   `127.0.0.1:3306`, o Bootstrap cria (idempotente):
   - banco **`pdvpro`**
   - usuário **`pdvpro`** / senha **`pdvpro`** em `'pdvpro'@'%'` e `'pdvpro'@'localhost'`
   - `GRANT ALL PRIVILEGES ON *.* ... WITH GRANT OPTION` + `FLUSH PRIVILEGES`
   - acessível remotamente.

## Como recompilar

Dentro do zip: `PHSERVER/build.sh` (precisa de `apktool 2.10`, `baksmali 2.5.2`,
`r8.jar` (D8), `android.jar` SDK 28 e `uber-apk-signer 1.3.0`). Fluxo:
`javac --release 8` → `D8` → `baksmali` → `apktool b --use-aapt2` → `uber-apk-signer`.

## Observação de teste

As automações de bootstrap (instalação, escuta remota e criação do banco) foram
implementadas e o APK compila/assina/empacota corretamente, mas **não foi possível
validá-las em um aparelho real** neste ambiente. Recomenda-se um teste em
dispositivo antes de produção.

> A chave de assinatura é a chave debug do `uber-apk-signer`. Para distribuir em
> produção, reassine com sua própria keystore.
