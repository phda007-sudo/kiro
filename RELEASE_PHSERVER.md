# PHSERVER — Build assinado

APK compilado a partir de `PH_Server.7z` (projeto `02_modified_smali_resources`, apktool 2.10.0).

## Arquivo

- **APK:** `PHSERVER.apk`
- **Versão:** 1.6.5-arm (versionCode 43)
- **minSdk / targetSdk:** 16 / 28
- **SHA-256:** `6f5ccc8f345fa1f3402237ec9d19616f4656f528cb40f1cc0f6d38546e3c3b12`
- **Assinatura:** v1 (JAR) + v2 + v3 — verificado com `apksigner verify`.

## Mudanças incluídas neste build

1. **Máscara de senha com `*`** — todos os campos de senha do app exibem `*`
   (classe `com.phda.phserver.AsteriskPasswordTransformationMethod`).
2. **Auto-start no boot** — o servidor sobe sozinho quando o aparelho liga,
   sem o usuário abrir/configurar o app (patch em
   `com.esminis.server.library.service.AutoStart`).

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
