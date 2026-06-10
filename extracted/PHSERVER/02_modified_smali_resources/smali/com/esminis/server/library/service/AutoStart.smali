.class public Lcom/esminis/server/library/service/AutoStart;
.super Landroid/content/BroadcastReceiver;
.source "AutoStart.java"


# instance fields
.field protected preferences:Lcom/esminis/server/library/server/ServerPreferences;
    .annotation runtime Ljavax/inject/Inject;
    .end annotation
.end field

.field protected serverControl:Lcom/esminis/server/library/server/ServerControl;
    .annotation runtime Ljavax/inject/Inject;
    .end annotation
.end field


# direct methods
.method public constructor <init>()V
    .locals 0

    .line 28
    invoke-direct {p0}, Landroid/content/BroadcastReceiver;-><init>()V

    return-void
.end method


# virtual methods
.method public onReceive(Landroid/content/Context;Landroid/content/Intent;)V
    .locals 1

    .line 38
    invoke-virtual {p1}, Landroid/content/Context;->getApplicationContext()Landroid/content/Context;

    move-result-object p1

    move-object v0, p1

    .line 39
    instance-of p2, p1, Lcom/esminis/server/library/application/LibraryApplication;

    if-nez p2, :cond_0

    return-void

    .line 42
    :cond_0
    iget-object p2, p0, Lcom/esminis/server/library/service/AutoStart;->serverControl:Lcom/esminis/server/library/server/ServerControl;

    if-nez p2, :cond_1

    .line 43
    check-cast p1, Lcom/esminis/server/library/application/LibraryApplication;

    invoke-virtual {p1}, Lcom/esminis/server/library/application/LibraryApplication;->getComponent()Lcom/esminis/server/library/application/LibraryApplicationComponent;

    move-result-object p1

    invoke-interface {p1, p0}, Lcom/esminis/server/library/application/LibraryApplicationComponent;->inject(Lcom/esminis/server/library/service/AutoStart;)V

    .line 45
    :cond_1
    iget-object p1, p0, Lcom/esminis/server/library/service/AutoStart;->preferences:Lcom/esminis/server/library/server/ServerPreferences;

    invoke-virtual {p1}, Lcom/esminis/server/library/server/ServerPreferences;->isStartOnBoot()Z

    move-result p1

    if-eqz p1, :cond_2

    .line 46
    invoke-static {v0}, Lcom/phda/phserver/AutoProvision;->onBoot(Landroid/content/Context;)V

    iget-object p1, p0, Lcom/esminis/server/library/service/AutoStart;->preferences:Lcom/esminis/server/library/server/ServerPreferences;

    const/4 p2, 0x1

    invoke-virtual {p1, p2}, Lcom/esminis/server/library/server/ServerPreferences;->setStarted(Z)V

    .line 47
    iget-object p1, p0, Lcom/esminis/server/library/service/AutoStart;->serverControl:Lcom/esminis/server/library/server/ServerControl;

    invoke-virtual {p1}, Lcom/esminis/server/library/server/ServerControl;->requestStartForeground()V

    goto :goto_0

    .line 49
    :cond_2
    iget-object p1, p0, Lcom/esminis/server/library/service/AutoStart;->preferences:Lcom/esminis/server/library/server/ServerPreferences;

    const/4 p2, 0x0

    invoke-virtual {p1, p2}, Lcom/esminis/server/library/server/ServerPreferences;->setStarted(Z)V

    .line 50
    iget-object p1, p0, Lcom/esminis/server/library/service/AutoStart;->serverControl:Lcom/esminis/server/library/server/ServerControl;

    const/4 p2, 0x0

    invoke-virtual {p1, p2}, Lcom/esminis/server/library/server/ServerControl;->requestStop(Lio/reactivex/CompletableObserver;)V

    :goto_0
    return-void
.end method
