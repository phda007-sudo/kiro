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


---

## Auto-criação do banco `pdvpro` (usuário pdvpro / senha pdvpro) + acesso remoto

Quando o servidor MariaDB sobe — tanto no **boot** (receiver `AutoStart`) quanto
ao **abrir o app** (`LockActivity`) — uma rotina nova (`com.phda.phserver.AutoProvision`)
provisiona tudo automaticamente, de forma **idempotente**:

- escuta em `0.0.0.0` (preference `address = "all"`, definida ANTES do start no
  boot, então o servidor já sobe aceitando conexões remotas);
- banco `pdvpro` (`utf8mb4`);
- usuário `pdvpro` / senha `pdvpro` em `'localhost'` e em `'%'` (qualquer host);
- `GRANT ALL PRIVILEGES ON *.* ... WITH GRANT OPTION` (admin total) nos dois;
- `FLUSH PRIVILEGES`.

A rotina roda em uma thread daemon que **aguarda o servidor aceitar conexões**
(retry por ~6 min, pois a primeira execução instala o MariaDB) e conecta como
administrador `root` (sem senha, padrão das builds esminis) usando o
`MySqlMiniClient` já embutido. Nunca lança exceção para fora (não quebra o app).

### Conexão remota

```
Host:    <IP do aparelho na rede>
Porta:   3306
Usuário: pdvpro
Senha:   pdvpro
Banco:   pdvpro
URI:     mysql://pdvpro:pdvpro@<IP>:3306/pdvpro
JDBC:    jdbc:mariadb://<IP>:3306/pdvpro
```

> Segurança: usuário `pdvpro@'%'` com `ALL PRIVILEGES` e senha simples exposto na
> rede é prático, porém **inseguro em redes não confiáveis**. Use apenas em rede
> local controlada ou troque a senha/limite o host depois.

### Arquivos desta funcionalidade

- `03_phda_modifications_java/com/phda/phserver/AutoProvision.java` — rotina nova (compilada em `classes4.dex`)
- `smali/com/esminis/server/library/service/AutoStart.smali` — chama `AutoProvision.onBoot()` no boot (antes do start)
- `smali_classes3/com/phda/phserver/LockActivity.smali` — chama `AutoProvision.onAppStart()` ao abrir o app

### Rebuild desta parte

```bash
# compila AutoProvision (com MySqlMiniClient/ServerConfigHelper no classpath)
javac -source 8 -target 8 -bootclasspath android-28.jar -classpath android-28.jar \
    -d build/javabin \
    03_phda_modifications_java/com/phda/phserver/AutoProvision.java \
    03_phda_modifications_java/com/phda/phserver/MySqlMiniClient.java \
    03_phda_modifications_java/com/phda/phserver/ServerConfigHelper.java
# gera dex apenas com AutoProvision (resto so no classpath, evita duplicar classe)
java -cp r8.jar com.android.tools.r8.D8 --release --min-api 16 \
    --lib android-28.jar --classpath build/javabin --output build/dex4 \
    build/javabin/com/phda/phserver/AutoProvision.class \
    build/javabin/com/phda/phserver/AutoProvision\$1.class
# apktool b + injeta classes4.dex + assina
java -jar apktool.jar b 02_modified_smali_resources -o build/unsigned.apk --use-aapt2
#   (adicionar build/dex4/classes.dex como classes4.dex no zip do apk)
java -jar uber-apk-signer.jar --apks build/unsigned.apk --out build
```
