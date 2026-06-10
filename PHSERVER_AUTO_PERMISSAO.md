# PHSERVER — Concessão automática da permissão de arquivos (sem a tela "CONCEDER")

## O que foi alterado

Apenas **uma** mudança, no `apktool.yml` do projeto
(`extracted/PHSERVER/02_modified_smali_resources/apktool.yml`):

```diff
 sdkInfo:
   minSdkVersion: 16
-  targetSdkVersion: 28
-  maxSdkVersion: 28
+  targetSdkVersion: 22
```

## Por que isso resolve

A tela **"CONCEDER"** (`PermissionRequestFragment`) só aparece quando
`PermissionRequester.hasPermission()` retorna falso para
`android.permission.WRITE_EXTERNAL_STORAGE`. O botão CONCEDER apenas abre o
**diálogo do sistema Android** — e nenhum app consegue clicar nesse diálogo
sozinho (é uma barreira de segurança do Android).

Quando o app tem `targetSdkVersion <= 22`, o Android **concede as permissões
declaradas no manifesto já no momento da instalação**, sem diálogo de runtime.
Resultado:

- `hasPermission()` retorna verdadeiro logo de cara → a tela CONCEDER **nunca aparece**;
- a permissão é **realmente concedida**, então o MariaDB continua gravando
  normalmente em `/storage/emulated/0/...` (diretório de dados padrão definido em
  `ServerPreferences.getRootDirectory()`);
- o `maxSdkVersion: 28` foi removido para não bloquear a instalação em Android
  mais novo.

Combinado com o auto-start no boot que o app **já possui** (receiver
`com.esminis.server.library.service.AutoStart` ligado a `BOOT_COMPLETED`), o
fluxo fica 100% automático: liga o aparelho → app sobe → permissão já concedida
→ servidor MariaDB no ar, sem nenhum toque.

## APK gerado

- Arquivo: `build/PHSERVER.apk`
- Assinatura: v1 + v2 + v3 (chave debug do uber-apk-signer; reassine com sua
  keystore para produção)
- `targetSdkVersion = 22`, `WRITE_EXTERNAL_STORAGE` declarada
- sha256: `46aafe91abc517428ee02c4a79d1b783d645f0b4ce197abcc1210ed1fc5adaf0`

## Como reconstruir

```bash
java -jar apktool.jar b extracted/PHSERVER/02_modified_smali_resources \
    -o build/PHSERVER_unsigned.apk --use-aapt2
java -jar uber-apk-signer.jar --apks build/PHSERVER_unsigned.apk --out build
```

## Limitações / observações

- **Android 14+ (API 34+)** bloqueia a instalação de apps com
  `targetSdkVersion < 23`. Se o aparelho for Android 14 ou superior, este APK
  não instala. Alternativas para esse caso:
  - apontar o diretório de dados para o armazenamento privado do app
    (`getExternalFilesDir`), que dispensa a permissão em qualquer versão; ou
  - conceder via PC uma vez:
    `adb shell pm grant com.esminis.server.mariadb android.permission.WRITE_EXTERNAL_STORAGE`; ou
  - em aparelho com root, conceder no boot via `pm grant` / `appops`.
- Desinstale a versão anterior antes de instalar (assinaturas podem diferir).
- Se o usuário revogar a permissão manualmente em Configurações, a tela CONCEDER
  pode voltar a aparecer (comportamento esperado).
