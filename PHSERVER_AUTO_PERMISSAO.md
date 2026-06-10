# PHSERVER — Funcionamento automático sem a tela "CONCEDER"

Objetivo: ligar o aparelho → o app sobe sozinho no boot → o servidor MariaDB
fica no ar **sem nenhum toque do usuário** e **sem a tela de permissão "CONCEDER"**.

O botão CONCEDER apenas abre o **diálogo de permissão do sistema Android**, e
nenhum app consegue clicar nesse diálogo sozinho (barreira de segurança do SO).
Por isso a solução não é "clicar no botão", e sim fazer com que o app **não
precise** dessa permissão.

---

## Solução implementada (à prova de Android 14+) — RECOMENDADA

O `PHSERVER.apk` deste repositório usa esta abordagem.

### 1) Diretório de dados no armazenamento PRIVADO do app (sem permissão)

`ServerPreferences.getRootDirectory()` foi alterado para, no caso padrão (sem
`DOCUMENT_ROOT` salvo), usar `context.getFilesDir()` em vez de
`Environment.getExternalStorageDirectory()`:

```diff
- new File(Environment.getExternalStorageDirectory(), default_document_root_directory)
+ new File(context.getFilesDir(),                      default_document_root_directory)
```

O armazenamento interno privado (`/data/data/com.esminis.server.mariadb/files/...`)
**não exige nenhuma permissão** em qualquer versão do Android, suporta sockets
Unix e execução de binários (essencial pro MariaDB) e não sofre com FUSE/sdcardfs.

### 2) Tela CONCEDER nunca aparece

`PermissionRequester.hasPermission()` foi alterado para retornar sempre `true`,
então o `PermissionRequestFragment` (tela CONCEDER) nunca é exibido e o app vai
direto para o servidor. Como os dados agora ficam no armazenamento interno,
nenhuma permissão real é necessária.

### 3) targetSdkVersion mantido em 28

Instala normalmente em **qualquer versão do Android, inclusive 14+**.

### Resultado

Combinado com o auto-start no boot que o app já possui (receiver
`com.esminis.server.library.service.AutoStart` ligado a `BOOT_COMPLETED`):

liga o aparelho → app sobe → sem tela CONCEDER → MariaDB no ar, zero toques.

### APK gerado

- Arquivo: `PHSERVER.apk` (raiz do repo)
- `targetSdkVersion = 28`, dados em armazenamento interno, sem necessidade de permissão
- Assinatura: v1 + v2 + v3 (chave debug do uber-apk-signer; reassine com sua keystore para produção)
- sha256: `82fb0c04fc73ec73d36e688f7586204d2ce5db94cf85b26d663e5ce96c2c8daa`

### Observações

- Os dados do banco passam a ficar no armazenamento interno privado do app.
  Vantagem: zero permissão e máxima compatibilidade. Atenção: **desinstalar o app
  apaga os dados** (faça backup/export quando necessário). Em um servidor
  dedicado/kiosk isso normalmente não é problema.
- Se quiser apontar os dados para outra pasta manualmente, o seletor de diretório
  do app continua funcionando (grava `DOCUMENT_ROOT`), mas aí pode voltar a
  exigir permissão dependendo do destino escolhido.

---

## Alternativa mais simples (somente Android <= 13)

Se o aparelho for Android 13 ou inferior e você preferir manter os dados em
`/storage/emulated/0/...`, basta baixar o `targetSdkVersion` para 22 no
`apktool.yml` (o Android concede `WRITE_EXTERNAL_STORAGE` na instalação, sem
diálogo). **Não funciona no Android 14+**, que bloqueia instalar apps com
`targetSdk < 23`. Por isso a solução interna acima é a recomendada.

---

## Como reconstruir

```bash
java -jar apktool.jar b extracted/PHSERVER/02_modified_smali_resources \
    -o build/PHSERVER_unsigned.apk --use-aapt2
java -jar uber-apk-signer.jar --apks build/PHSERVER_unsigned.apk --out build
```

## Arquivos alterados

- `smali/com/esminis/server/library/server/ServerPreferences.smali` — `getRootDirectory()` usa `getFilesDir()`
- `smali/com/esminis/server/library/permission/PermissionRequester.smali` — `hasPermission()` retorna `true`
- `apktool.yml` — `maxSdkVersion: 28` removido (instala em Android novo); `targetSdkVersion` = 28
