# PHSERVER — Build assinado

APK compilado a partir de `PH_Server.7z` (projeto `02_modified_smali_resources`, apktool 2.10.0).

## Arquivo

- **APK:** `PHSERVER.apk`
- **Versão:** 1.6.5-arm (versionCode 43)
- **minSdk / targetSdk:** 16 / 28
- **SHA-256:** `bb63f7601a6b2d84ae9a24206cf562a43eba912e5691459966da3829f73a317a`
- **Assinatura:** v1 (JAR) + v2 + v3 — verificado com `apksigner verify`.

## Mudanças incluídas neste build

1. **Máscara de senha com `*`** — todos os campos de senha do app exibem `*`
   (classe `com.phda.phserver.AsteriskPasswordTransformationMethod`).
2. **Auto-start no boot (robusto)** — o servidor sobe sozinho quando o aparelho
   liga, sem o usuário abrir/configurar o app:
   - Patch em `com.esminis.server.library.service.AutoStart` (sempre inicia).
   - NOVO receiver `com.phda.phserver.BootReceiver`, que replica o caminho
     comprovado do `LockActivity`: **espera o componente de injeção ficar
     pronto (~5s) via `getComponent(int)`** antes de chamar
     `requestStartForeground()`. Isso resolve a falha de boot a frio (o DI do
     app normalmente ainda não está pronto quando o `BOOT_COMPLETED` chega).
   - Registrado para `BOOT_COMPLETED`, `QUICKBOOT_POWERON` (e variante HTC) e
     `MY_PACKAGE_REPLACED` (re-arma após atualizar o app).

## IMPORTANTE — requisitos do Android para o boot funcionar

Estes dois pontos são imposições do próprio Android/fabricante e NÃO podem ser
contornados por código:

1. **Abra o app pelo menos UMA vez após instalar.** Apps recém-instalados ficam
   em estado "stopped" e o Android NÃO entrega `BOOT_COMPLETED` até a primeira
   abertura manual.
2. **Permita o "autostart" do app** nas configurações do fabricante
   (Xiaomi/MIUI, Huawei, Oppo/ColorOS, Samsung, etc.) e desative a otimização
   de bateria para o app. Sem isso, o sistema bloqueia o início em background.

## Como instalar

1. Baixe `PHSERVER.apk` no aparelho Android.
2. Habilite "Instalar apps de fontes desconhecidas" para o app usado para abrir.
3. Instale. Na primeira execução, conceda as permissões e, se solicitado,
   permita "ignorar otimizações de bateria" para o auto-start no boot funcionar
   de forma confiável.

## Chave de assinatura

O APK foi assinado com `phserver-signing.keystore` (auto-assinado, gerado para
este build):

- alias: `phserver`
- storepass / keypass: `phserver123`

> IMPORTANTE: guarde esta keystore. Atualizações futuras do app só instalam
> "por cima" (sem desinstalar) se forem assinadas com ESTA mesma chave.
> Por ser uma chave auto-assinada de uso pessoal, ela acompanha o repositório;
> troque-a/proteja-a se for distribuir o app publicamente.

## Como reconstruir

```bash
# montar o APK a partir do projeto apktool
java -jar apktool_2.10.0.jar b 02_modified_smali_resources -o unsigned.apk

# alinhar e assinar
zipalign -p -f 4 unsigned.apk aligned.apk
apksigner sign --ks phserver-signing.keystore --ks-pass pass:phserver123 \
  --ks-key-alias phserver --key-pass pass:phserver123 \
  --out PHSERVER.apk aligned.apk
apksigner verify --verbose PHSERVER.apk
```
