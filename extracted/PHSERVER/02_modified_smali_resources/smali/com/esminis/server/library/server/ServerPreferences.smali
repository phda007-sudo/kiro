.class public Lcom/esminis/server/library/server/ServerPreferences;
.super Ljava/lang/Object;
.source "ServerPreferences.java"


# annotations
.annotation system Ldalvik/annotation/MemberClasses;
    value = {
        Lcom/esminis/server/library/server/ServerPreferences$LogPreferences;
    }
.end annotation

.annotation runtime Ljavax/inject/Singleton;
.end annotation


# static fields
.field public static final PORT_MAX:I = 0xffff

.field public static final PORT_MIN:I = 0x400


# instance fields
.field private final context:Landroid/content/Context;

.field private final network:Lcom/esminis/server/library/model/manager/Network;

.field protected final preferences:Lcom/esminis/server/library/preferences/Preferences;


# direct methods
.method public constructor <init>(Lcom/esminis/server/library/application/LibraryApplication;Lcom/esminis/server/library/preferences/Preferences;Lcom/esminis/server/library/model/manager/Network;)V
    .locals 0
    .annotation runtime Ljavax/inject/Inject;
    .end annotation

    .line 49
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 50
    iput-object p2, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    .line 51
    iput-object p3, p0, Lcom/esminis/server/library/server/ServerPreferences;->network:Lcom/esminis/server/library/model/manager/Network;

    .line 52
    iput-object p1, p0, Lcom/esminis/server/library/server/ServerPreferences;->context:Landroid/content/Context;

    return-void
.end method

.method private getInstalledPackagePreference(Lcom/esminis/server/library/form/fields/Field;)Lcom/esminis/server/library/model/InstallPackage;
    .locals 3
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Lcom/esminis/server/library/form/fields/Field<",
            "Ljava/lang/String;",
            ">;)",
            "Lcom/esminis/server/library/model/InstallPackage;"
        }
    .end annotation

    .line 213
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    invoke-virtual {v0, p1}, Lcom/esminis/server/library/preferences/Preferences;->contains(Lcom/esminis/server/library/form/fields/Field;)Z

    move-result v0

    const/4 v1, 0x0

    if-eqz v0, :cond_1

    .line 215
    :try_start_0
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    iget-object p1, p1, Lcom/esminis/server/library/form/fields/Field;->name:Ljava/lang/String;

    invoke-virtual {v0, p1}, Lcom/esminis/server/library/preferences/Preferences;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object p1

    if-nez p1, :cond_0

    move-object v0, v1

    goto :goto_0

    .line 216
    :cond_0
    new-instance v0, Lcom/esminis/server/library/model/InstallPackage;

    new-instance v2, Lorg/json/JSONObject;

    invoke-direct {v2, p1}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V

    invoke-direct {v0, v2}, Lcom/esminis/server/library/model/InstallPackage;-><init>(Lorg/json/JSONObject;)V
    :try_end_0
    .catch Lorg/json/JSONException; {:try_start_0 .. :try_end_0} :catch_0

    :goto_0
    return-object v0

    :catch_0
    :cond_1
    return-object v1
.end method

.method private setInstalledPackagePreference(Lcom/esminis/server/library/form/fields/Field;Lcom/esminis/server/library/model/InstallPackage;)V
    .locals 1
    .annotation system Ldalvik/annotation/Signature;
        value = {
            "(",
            "Lcom/esminis/server/library/form/fields/Field<",
            "Ljava/lang/String;",
            ">;",
            "Lcom/esminis/server/library/model/InstallPackage;",
            ")V"
        }
    .end annotation

    .annotation system Ldalvik/annotation/Throws;
        value = {
            Lorg/json/JSONException;
        }
    .end annotation

    .line 209
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    iget-object p1, p1, Lcom/esminis/server/library/form/fields/Field;->name:Ljava/lang/String;

    if-nez p2, :cond_0

    const/4 p2, 0x0

    goto :goto_0

    :cond_0
    invoke-virtual {p2}, Lcom/esminis/server/library/model/InstallPackage;->toJson()Lorg/json/JSONObject;

    move-result-object p2

    invoke-virtual {p2}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p2

    :goto_0
    invoke-virtual {v0, p1, p2}, Lcom/esminis/server/library/preferences/Preferences;->set(Ljava/lang/String;Ljava/lang/String;)V

    return-void
.end method


# virtual methods
.method public getAddress()Ljava/lang/String;
    .locals 2

    .line 74
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->NETWORK_ADDRESS:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->contains(Lcom/esminis/server/library/form/fields/Field;)Z

    move-result v0

    if-eqz v0, :cond_0

    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->NETWORK_ADDRESS:Lcom/esminis/server/library/form/fields/Field;

    .line 75
    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getString(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/String;

    move-result-object v0

    goto :goto_0

    :cond_0
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->network:Lcom/esminis/server/library/model/manager/Network;

    invoke-virtual {v0}, Lcom/esminis/server/library/model/manager/Network;->getDefault()Lcom/esminis/server/library/model/NetworkInterface;

    move-result-object v0

    iget-object v0, v0, Lcom/esminis/server/library/model/NetworkInterface;->id:Ljava/lang/String;

    :goto_0
    return-object v0
.end method

.method public getConfigDirectory(Ljava/io/File;)Ljava/io/File;
    .locals 2

    .line 116
    new-instance v0, Ljava/io/File;

    const-string v1, "config"

    invoke-direct {v0, p1, v1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    return-object v0
.end method

.method public getDataDirectory(Ljava/io/File;)Ljava/io/File;
    .locals 2

    .line 132
    new-instance v0, Ljava/io/File;

    const-string v1, "data"

    invoke-direct {v0, p1, v1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    return-object v0
.end method

.method public getEnabledCgi()[Ljava/lang/String;
    .locals 2

    .line 223
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->APACHE_CGI:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getStrings(Lcom/esminis/server/library/form/fields/Field;)[Ljava/lang/String;

    move-result-object v0

    return-object v0
.end method

.method public getFallback()Lcom/esminis/server/library/server/ServerNetworkFallback;
    .locals 3

    .line 98
    :try_start_0
    new-instance v0, Lcom/esminis/server/library/server/ServerNetworkFallback;

    iget-object v1, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v2, Lcom/esminis/server/library/form/fields/Fields;->NETWORK_ADDRESS_FALLBACK:Lcom/esminis/server/library/form/fields/Field;

    .line 99
    invoke-virtual {v1, v2}, Lcom/esminis/server/library/preferences/Preferences;->getJSONObject(Lcom/esminis/server/library/form/fields/Field;)Lorg/json/JSONObject;

    move-result-object v1

    invoke-direct {v0, v1}, Lcom/esminis/server/library/server/ServerNetworkFallback;-><init>(Lorg/json/JSONObject;)V
    :try_end_0
    .catch Lorg/json/JSONException; {:try_start_0 .. :try_end_0} :catch_0

    return-object v0

    .line 102
    :catch_0
    new-instance v0, Lcom/esminis/server/library/server/ServerNetworkFallback;

    invoke-direct {v0}, Lcom/esminis/server/library/server/ServerNetworkFallback;-><init>()V

    return-object v0
.end method

.method public getInstallPackageCache()Lorg/json/JSONObject;
    .locals 2

    .line 189
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->PACKAGE_INSTALL_CACHE:Lcom/esminis/server/library/form/fields/Field;

    iget-object v1, v1, Lcom/esminis/server/library/form/fields/Field;->name:Ljava/lang/String;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getString(Ljava/lang/String;)Ljava/lang/String;

    move-result-object v0

    if-eqz v0, :cond_0

    .line 191
    :try_start_0
    invoke-virtual {v0}, Ljava/lang/String;->isEmpty()Z

    move-result v1

    if-nez v1, :cond_0

    .line 192
    new-instance v1, Lorg/json/JSONObject;

    invoke-direct {v1, v0}, Lorg/json/JSONObject;-><init>(Ljava/lang/String;)V
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    return-object v1

    .line 195
    :catchall_0
    :cond_0
    new-instance v0, Lorg/json/JSONObject;

    invoke-direct {v0}, Lorg/json/JSONObject;-><init>()V

    return-object v0
.end method

.method public getInstalledPackage()Lcom/esminis/server/library/model/InstallPackage;
    .locals 1

    .line 173
    sget-object v0, Lcom/esminis/server/library/form/fields/Fields;->PACKAGE_INSTALLED:Lcom/esminis/server/library/form/fields/Field;

    invoke-direct {p0, v0}, Lcom/esminis/server/library/server/ServerPreferences;->getInstalledPackagePreference(Lcom/esminis/server/library/form/fields/Field;)Lcom/esminis/server/library/model/InstallPackage;

    move-result-object v0

    return-object v0
.end method

.method public getInstalledPackageNewestAvailable()Lcom/esminis/server/library/model/InstallPackage;
    .locals 1

    .line 181
    sget-object v0, Lcom/esminis/server/library/form/fields/Fields;->PACKAGE_NEWEST:Lcom/esminis/server/library/form/fields/Field;

    invoke-direct {p0, v0}, Lcom/esminis/server/library/server/ServerPreferences;->getInstalledPackagePreference(Lcom/esminis/server/library/form/fields/Field;)Lcom/esminis/server/library/model/InstallPackage;

    move-result-object v0

    return-object v0
.end method

.method public getLog()Lcom/esminis/server/library/server/ServerPreferences$LogPreferences;
    .locals 6

    .line 83
    new-instance v0, Lcom/esminis/server/library/server/ServerPreferences$LogPreferences;

    iget-object v1, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v2, Lcom/esminis/server/library/form/fields/Fields;->LOGS_ENABLED:Lcom/esminis/server/library/form/fields/Field;

    .line 84
    invoke-virtual {v1, v2}, Lcom/esminis/server/library/preferences/Preferences;->getBoolean(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/Boolean;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/Boolean;->booleanValue()Z

    move-result v1

    iget-object v2, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v3, Lcom/esminis/server/library/form/fields/Fields;->LOGS_BACKEND:Lcom/esminis/server/library/form/fields/Field;

    sget-object v4, Lcom/esminis/server/library/form/fields/Fields;->LOGS_BACKEND_VALUES:[Lcom/esminis/server/library/form/fields/FieldValue;

    .line 85
    invoke-virtual {v2, v3, v4}, Lcom/esminis/server/library/preferences/Preferences;->getValue(Lcom/esminis/server/library/form/fields/Field;[Lcom/esminis/server/library/form/fields/FieldValue;)Lcom/esminis/server/library/form/fields/FieldValue;

    move-result-object v2

    iget-object v3, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v4, Lcom/esminis/server/library/form/fields/Fields;->LOGS_LIMIT:Lcom/esminis/server/library/form/fields/Field;

    sget-object v5, Lcom/esminis/server/library/form/fields/Fields;->LOGS_LIMIT_VALUES:[Lcom/esminis/server/library/form/fields/FieldValue;

    .line 86
    invoke-virtual {v3, v4, v5}, Lcom/esminis/server/library/preferences/Preferences;->getValue(Lcom/esminis/server/library/form/fields/Field;[Lcom/esminis/server/library/form/fields/FieldValue;)Lcom/esminis/server/library/form/fields/FieldValue;

    move-result-object v3

    const/4 v4, 0x0

    invoke-direct {v0, v1, v2, v3, v4}, Lcom/esminis/server/library/server/ServerPreferences$LogPreferences;-><init>(ZLcom/esminis/server/library/form/fields/FieldValue;Lcom/esminis/server/library/form/fields/FieldValue;Lcom/esminis/server/library/server/ServerPreferences$1;)V

    return-object v0
.end method

.method public getLogDirectory(Ljava/io/File;)Ljava/io/File;
    .locals 2

    .line 120
    new-instance v0, Ljava/io/File;

    const-string v1, "log"

    invoke-direct {v0, p1, v1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    return-object v0
.end method

.method public getPort()I
    .locals 2

    .line 56
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->NETWORK_PORT:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getInteger(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/Integer;

    move-result-object v0

    if-eqz v0, :cond_0

    .line 58
    :try_start_0
    invoke-virtual {v0}, Ljava/lang/Integer;->intValue()I

    move-result v1

    invoke-virtual {p0, v1}, Lcom/esminis/server/library/server/ServerPreferences;->isValidPort(I)Z

    move-result v1

    if-eqz v1, :cond_0

    .line 59
    invoke-virtual {v0}, Ljava/lang/Integer;->intValue()I

    move-result v0
    :try_end_0
    .catch Ljava/lang/NumberFormatException; {:try_start_0 .. :try_end_0} :catch_0

    return v0

    .line 62
    :catch_0
    :cond_0
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->context:Landroid/content/Context;

    sget v1, Lcom/esminis/server/library/R$string;->default_port:I

    invoke-virtual {v0, v1}, Landroid/content/Context;->getString(I)Ljava/lang/String;

    move-result-object v0

    invoke-static {v0}, Ljava/lang/Integer;->valueOf(Ljava/lang/String;)Ljava/lang/Integer;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/Integer;->intValue()I

    move-result v0

    return v0
.end method

.method public getPublicDirectory(Ljava/io/File;)Ljava/io/File;
    .locals 2

    .line 128
    new-instance v0, Ljava/io/File;

    const-string v1, "public"

    invoke-direct {v0, p1, v1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    return-object v0
.end method

.method public getRootDirectory()Ljava/io/File;
    .locals 4

    .line 106
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->DOCUMENT_ROOT:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->contains(Lcom/esminis/server/library/form/fields/Field;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 107
    new-instance v0, Ljava/io/File;

    iget-object v1, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v2, Lcom/esminis/server/library/form/fields/Fields;->DOCUMENT_ROOT:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v1, v2}, Lcom/esminis/server/library/preferences/Preferences;->getString(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/String;

    move-result-object v1

    invoke-direct {v0, v1}, Ljava/io/File;-><init>(Ljava/lang/String;)V

    return-object v0

    .line 109
    :cond_0
    new-instance v0, Ljava/io/File;

    .line 110
    iget-object v1, p0, Lcom/esminis/server/library/server/ServerPreferences;->context:Landroid/content/Context;

    invoke-virtual {v1}, Landroid/content/Context;->getFilesDir()Ljava/io/File;

    move-result-object v1

    iget-object v2, p0, Lcom/esminis/server/library/server/ServerPreferences;->context:Landroid/content/Context;

    sget v3, Lcom/esminis/server/library/R$string;->default_document_root_directory:I

    .line 111
    invoke-virtual {v2, v3}, Landroid/content/Context;->getString(I)Ljava/lang/String;

    move-result-object v2

    invoke-direct {v0, v1, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    return-object v0
.end method

.method public getRouterFile()Ljava/lang/String;
    .locals 2

    .line 160
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->PHP_ROUTER_FILE:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getString(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/String;

    move-result-object v0

    if-eqz v0, :cond_0

    .line 161
    invoke-virtual {v0}, Ljava/lang/String;->isEmpty()Z

    move-result v1

    if-eqz v1, :cond_1

    :cond_0
    const-string v0, "index.php"

    :cond_1
    return-object v0
.end method

.method public getTempDirectory(Ljava/io/File;)Ljava/io/File;
    .locals 2

    .line 124
    new-instance v0, Ljava/io/File;

    const-string v1, "temp"

    invoke-direct {v0, p1, v1}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    return-object v0
.end method

.method public isModuleEnabled(Ljava/lang/String;)Z
    .locals 1

    .line 165
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    invoke-virtual {v0, p1}, Lcom/esminis/server/library/preferences/Preferences;->contains(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    invoke-virtual {v0, p1}, Lcom/esminis/server/library/preferences/Preferences;->getBoolean(Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_0

    goto :goto_0

    :cond_0
    const/4 p1, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 p1, 0x1

    :goto_1
    return p1
.end method

.method public isPhpRouterScriptEnabled()Z
    .locals 2

    .line 152
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->PHP_ROUTER_INDEX:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getBoolean(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/Boolean;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/Boolean;->booleanValue()Z

    move-result v0

    return v0
.end method

.method public isStartOnBoot()Z
    .locals 2

    .line 148
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->START_ON_BOOT:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getBoolean(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/Boolean;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/Boolean;->booleanValue()Z

    move-result v0

    return v0
.end method

.method public isStarted()Z
    .locals 2

    .line 144
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->SERVER_STARTED:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getBoolean(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/Boolean;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/Boolean;->booleanValue()Z

    move-result v0

    return v0
.end method

.method public isTutorialComplete()Z
    .locals 2

    .line 199
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->TUTORIAL_COMPLETE:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1}, Lcom/esminis/server/library/preferences/Preferences;->getBoolean(Lcom/esminis/server/library/form/fields/Field;)Ljava/lang/Boolean;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/Boolean;->booleanValue()Z

    move-result v0

    return v0
.end method

.method public isValidPort(I)Z
    .locals 1

    const/16 v0, 0x400

    if-lt p1, v0, :cond_0

    const v0, 0xffff

    if-gt p1, v0, :cond_0

    const/4 p1, 0x1

    goto :goto_0

    :cond_0
    const/4 p1, 0x0

    :goto_0
    return p1
.end method

.method public setAddress(Ljava/lang/String;)V
    .locals 2

    .line 79
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->NETWORK_ADDRESS:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1, p1}, Lcom/esminis/server/library/preferences/Preferences;->setString(Lcom/esminis/server/library/form/fields/Field;Ljava/lang/String;)V

    return-void
.end method

.method public setFallback(Lcom/esminis/server/library/server/ServerNetworkFallback;)V
    .locals 2

    .line 92
    :try_start_0
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->NETWORK_ADDRESS_FALLBACK:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {p1}, Lcom/esminis/server/library/server/ServerNetworkFallback;->toJSON()Lorg/json/JSONObject;

    move-result-object p1

    invoke-virtual {v0, v1, p1}, Lcom/esminis/server/library/preferences/Preferences;->set(Lcom/esminis/server/library/form/fields/Field;Lorg/json/JSONObject;)V
    :try_end_0
    .catch Lorg/json/JSONException; {:try_start_0 .. :try_end_0} :catch_0

    :catch_0
    return-void
.end method

.method public setInstallPackageCache(Lorg/json/JSONObject;)V
    .locals 2

    .line 185
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->PACKAGE_INSTALL_CACHE:Lcom/esminis/server/library/form/fields/Field;

    iget-object v1, v1, Lcom/esminis/server/library/form/fields/Field;->name:Ljava/lang/String;

    invoke-virtual {p1}, Lorg/json/JSONObject;->toString()Ljava/lang/String;

    move-result-object p1

    invoke-virtual {v0, v1, p1}, Lcom/esminis/server/library/preferences/Preferences;->set(Ljava/lang/String;Ljava/lang/String;)V

    return-void
.end method

.method public setInstalledPackage(Lcom/esminis/server/library/model/InstallPackage;)V
    .locals 1
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Lorg/json/JSONException;
        }
    .end annotation

    .line 169
    sget-object v0, Lcom/esminis/server/library/form/fields/Fields;->PACKAGE_INSTALLED:Lcom/esminis/server/library/form/fields/Field;

    invoke-direct {p0, v0, p1}, Lcom/esminis/server/library/server/ServerPreferences;->setInstalledPackagePreference(Lcom/esminis/server/library/form/fields/Field;Lcom/esminis/server/library/model/InstallPackage;)V

    return-void
.end method

.method public setInstalledPackageNewestAvailable(Lcom/esminis/server/library/model/InstallPackage;)V
    .locals 1
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Lorg/json/JSONException;
        }
    .end annotation

    .line 177
    sget-object v0, Lcom/esminis/server/library/form/fields/Fields;->PACKAGE_NEWEST:Lcom/esminis/server/library/form/fields/Field;

    invoke-direct {p0, v0, p1}, Lcom/esminis/server/library/server/ServerPreferences;->setInstalledPackagePreference(Lcom/esminis/server/library/form/fields/Field;Lcom/esminis/server/library/model/InstallPackage;)V

    return-void
.end method

.method public setPort(I)V
    .locals 2

    .line 70
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->NETWORK_PORT:Lcom/esminis/server/library/form/fields/Field;

    invoke-static {p1}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;

    move-result-object p1

    invoke-virtual {v0, v1, p1}, Lcom/esminis/server/library/preferences/Preferences;->setInteger(Lcom/esminis/server/library/form/fields/Field;Ljava/lang/Integer;)V

    return-void
.end method

.method public setRootDirectory(Ljava/lang/String;)V
    .locals 2

    .line 136
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->DOCUMENT_ROOT:Lcom/esminis/server/library/form/fields/Field;

    invoke-virtual {v0, v1, p1}, Lcom/esminis/server/library/preferences/Preferences;->setString(Lcom/esminis/server/library/form/fields/Field;Ljava/lang/String;)V

    return-void
.end method

.method public setRouterFile(Ljava/lang/String;)V
    .locals 3

    .line 156
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->PHP_ROUTER_FILE:Lcom/esminis/server/library/form/fields/Field;

    if-eqz p1, :cond_0

    invoke-virtual {p1}, Ljava/lang/String;->isEmpty()Z

    move-result v2

    if-eqz v2, :cond_1

    :cond_0
    const/4 p1, 0x0

    :cond_1
    invoke-virtual {v0, v1, p1}, Lcom/esminis/server/library/preferences/Preferences;->setString(Lcom/esminis/server/library/form/fields/Field;Ljava/lang/String;)V

    return-void
.end method

.method public setStarted(Z)V
    .locals 2

    .line 140
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->SERVER_STARTED:Lcom/esminis/server/library/form/fields/Field;

    iget-object v1, v1, Lcom/esminis/server/library/form/fields/Field;->name:Ljava/lang/String;

    invoke-virtual {v0, v1, p1}, Lcom/esminis/server/library/preferences/Preferences;->set(Ljava/lang/String;Z)V

    return-void
.end method

.method public setTutorialComplete()V
    .locals 3

    .line 203
    iget-object v0, p0, Lcom/esminis/server/library/server/ServerPreferences;->preferences:Lcom/esminis/server/library/preferences/Preferences;

    sget-object v1, Lcom/esminis/server/library/form/fields/Fields;->TUTORIAL_COMPLETE:Lcom/esminis/server/library/form/fields/Field;

    iget-object v1, v1, Lcom/esminis/server/library/form/fields/Field;->name:Ljava/lang/String;

    const/4 v2, 0x1

    invoke-virtual {v0, v1, v2}, Lcom/esminis/server/library/preferences/Preferences;->set(Ljava/lang/String;Z)V

    return-void
.end method
