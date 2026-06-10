.class public Lcom/esminis/server/library/permission/PermissionRequester;
.super Ljava/lang/Object;
.source "PermissionRequester.java"


# static fields
.field private static final REQUEST_CODE_PERMISSION:I = 0x1


# instance fields
.field private emitterInProgress:Lio/reactivex/CompletableEmitter;

.field private final lock:Ljava/lang/Object;

.field private showExplanation:Z


# direct methods
.method public constructor <init>()V
    .locals 1
    .annotation runtime Ljavax/inject/Inject;
    .end annotation

    .line 40
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    .line 35
    new-instance v0, Ljava/lang/Object;

    invoke-direct {v0}, Ljava/lang/Object;-><init>()V

    iput-object v0, p0, Lcom/esminis/server/library/permission/PermissionRequester;->lock:Ljava/lang/Object;

    const/4 v0, 0x0

    .line 36
    iput-object v0, p0, Lcom/esminis/server/library/permission/PermissionRequester;->emitterInProgress:Lio/reactivex/CompletableEmitter;

    const/4 v0, 0x0

    .line 37
    iput-boolean v0, p0, Lcom/esminis/server/library/permission/PermissionRequester;->showExplanation:Z

    return-void
.end method

.method public static hasPermission(Landroid/content/Context;Ljava/lang/String;)Z
    .locals 1

    .line 47
    const/4 v0, 0x1

    return v0
.end method

.method public static hasPermission(Landroidx/fragment/app/Fragment;Ljava/lang/String;)Z
    .locals 0

    if-nez p0, :cond_0

    const/4 p0, 0x0

    goto :goto_0

    .line 43
    :cond_0
    invoke-virtual {p0}, Landroidx/fragment/app/Fragment;->getContext()Landroid/content/Context;

    move-result-object p0

    :goto_0
    invoke-static {p0, p1}, Lcom/esminis/server/library/permission/PermissionRequester;->hasPermission(Landroid/content/Context;Ljava/lang/String;)Z

    move-result p0

    return p0
.end method


# virtual methods
.method cleanup()V
    .locals 2

    .line 114
    iget-object v0, p0, Lcom/esminis/server/library/permission/PermissionRequester;->lock:Ljava/lang/Object;

    monitor-enter v0

    const/4 v1, 0x0

    .line 115
    :try_start_0
    iput-object v1, p0, Lcom/esminis/server/library/permission/PermissionRequester;->emitterInProgress:Lio/reactivex/CompletableEmitter;

    const/4 v1, 0x0

    .line 116
    iput-boolean v1, p0, Lcom/esminis/server/library/permission/PermissionRequester;->showExplanation:Z

    .line 117
    monitor-exit v0

    return-void

    :catchall_0
    move-exception v1

    monitor-exit v0
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    throw v1
.end method

.method public synthetic lambda$request$0$PermissionRequester(Ljava/lang/ref/WeakReference;Ljava/lang/String;Landroidx/fragment/app/Fragment;Lio/reactivex/CompletableEmitter;)V
    .locals 2
    .annotation system Ldalvik/annotation/Throws;
        value = {
            Ljava/lang/Exception;
        }
    .end annotation

    .line 54
    invoke-virtual {p1}, Ljava/lang/ref/WeakReference;->get()Ljava/lang/Object;

    move-result-object p1

    check-cast p1, Landroidx/fragment/app/Fragment;

    const/4 v0, 0x0

    if-nez p1, :cond_0

    .line 56
    new-instance p1, Lcom/esminis/server/library/permission/PermissionRequestFailed;

    invoke-direct {p1, v0}, Lcom/esminis/server/library/permission/PermissionRequestFailed;-><init>(I)V

    invoke-interface {p4, p1}, Lio/reactivex/CompletableEmitter;->onError(Ljava/lang/Throwable;)V

    goto :goto_0

    :cond_0
    if-nez p2, :cond_1

    .line 60
    new-instance p1, Lcom/esminis/server/library/permission/PermissionRequestFailed;

    const/4 p2, 0x4

    invoke-direct {p1, p2}, Lcom/esminis/server/library/permission/PermissionRequestFailed;-><init>(I)V

    invoke-interface {p4, p1}, Lio/reactivex/CompletableEmitter;->onError(Ljava/lang/Throwable;)V

    goto :goto_0

    .line 63
    :cond_1
    invoke-virtual {p1}, Landroidx/fragment/app/Fragment;->getContext()Landroid/content/Context;

    move-result-object p1

    invoke-static {p1, p2}, Lcom/esminis/server/library/permission/PermissionRequester;->hasPermission(Landroid/content/Context;Ljava/lang/String;)Z

    move-result p1

    if-eqz p1, :cond_2

    .line 64
    invoke-interface {p4}, Lio/reactivex/CompletableEmitter;->onComplete()V

    goto :goto_0

    .line 66
    :cond_2
    iget-object p1, p0, Lcom/esminis/server/library/permission/PermissionRequester;->lock:Ljava/lang/Object;

    monitor-enter p1

    .line 67
    :try_start_0
    iget-object v1, p0, Lcom/esminis/server/library/permission/PermissionRequester;->emitterInProgress:Lio/reactivex/CompletableEmitter;

    if-eqz v1, :cond_3

    .line 68
    new-instance p2, Lcom/esminis/server/library/permission/PermissionRequestFailed;

    const/4 p3, 0x3

    invoke-direct {p2, p3}, Lcom/esminis/server/library/permission/PermissionRequestFailed;-><init>(I)V

    invoke-interface {p4, p2}, Lio/reactivex/CompletableEmitter;->onError(Ljava/lang/Throwable;)V

    .line 73
    monitor-exit p1

    return-void

    .line 75
    :cond_3
    invoke-virtual {p3, p2}, Landroidx/fragment/app/Fragment;->shouldShowRequestPermissionRationale(Ljava/lang/String;)Z

    move-result v1

    iput-boolean v1, p0, Lcom/esminis/server/library/permission/PermissionRequester;->showExplanation:Z

    .line 76
    iput-object p4, p0, Lcom/esminis/server/library/permission/PermissionRequester;->emitterInProgress:Lio/reactivex/CompletableEmitter;

    .line 77
    monitor-exit p1
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    const/4 p1, 0x1

    new-array p4, p1, [Ljava/lang/String;

    aput-object p2, p4, v0

    .line 78
    invoke-virtual {p3, p4, p1}, Landroidx/fragment/app/Fragment;->requestPermissions([Ljava/lang/String;I)V

    :goto_0
    return-void

    :catchall_0
    move-exception p2

    .line 77
    :try_start_1
    monitor-exit p1
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    throw p2
.end method

.method onRequestPermissionsResult(I[I)V
    .locals 4

    const/4 v0, 0x1

    if-eq p1, v0, :cond_0

    return-void

    .line 89
    :cond_0
    iget-object p1, p0, Lcom/esminis/server/library/permission/PermissionRequester;->lock:Ljava/lang/Object;

    monitor-enter p1

    .line 90
    :try_start_0
    iget-object v1, p0, Lcom/esminis/server/library/permission/PermissionRequester;->emitterInProgress:Lio/reactivex/CompletableEmitter;

    .line 91
    iget-boolean v2, p0, Lcom/esminis/server/library/permission/PermissionRequester;->showExplanation:Z

    const/4 v3, 0x0

    .line 92
    iput-object v3, p0, Lcom/esminis/server/library/permission/PermissionRequester;->emitterInProgress:Lio/reactivex/CompletableEmitter;

    const/4 v3, 0x0

    .line 93
    iput-boolean v3, p0, Lcom/esminis/server/library/permission/PermissionRequester;->showExplanation:Z

    .line 94
    monitor-exit p1
    :try_end_0
    .catchall {:try_start_0 .. :try_end_0} :catchall_0

    if-nez v1, :cond_1

    return-void

    :cond_1
    if-eqz p2, :cond_2

    .line 98
    array-length p1, p2

    if-lez p1, :cond_2

    aget p1, p2, v3

    if-nez p1, :cond_2

    .line 102
    invoke-interface {v1}, Lio/reactivex/CompletableEmitter;->onComplete()V

    goto :goto_0

    .line 104
    :cond_2
    new-instance p1, Lcom/esminis/server/library/permission/PermissionRequestFailed;

    if-eqz v2, :cond_3

    const/4 v0, 0x2

    :cond_3
    invoke-direct {p1, v0}, Lcom/esminis/server/library/permission/PermissionRequestFailed;-><init>(I)V

    invoke-interface {v1, p1}, Lio/reactivex/CompletableEmitter;->onError(Ljava/lang/Throwable;)V

    :goto_0
    return-void

    :catchall_0
    move-exception p2

    .line 94
    :try_start_1
    monitor-exit p1
    :try_end_1
    .catchall {:try_start_1 .. :try_end_1} :catchall_0

    throw p2
.end method

.method public request(Landroidx/fragment/app/Fragment;Ljava/lang/String;)Lio/reactivex/Completable;
    .locals 2

    .line 52
    new-instance v0, Ljava/lang/ref/WeakReference;

    invoke-direct {v0, p1}, Ljava/lang/ref/WeakReference;-><init>(Ljava/lang/Object;)V

    .line 53
    new-instance v1, Lcom/esminis/server/library/permission/-$$Lambda$PermissionRequester$o7zE-5TiwB8uYIEBk4H1ivcsqkM;

    invoke-direct {v1, p0, v0, p2, p1}, Lcom/esminis/server/library/permission/-$$Lambda$PermissionRequester$o7zE-5TiwB8uYIEBk4H1ivcsqkM;-><init>(Lcom/esminis/server/library/permission/PermissionRequester;Ljava/lang/ref/WeakReference;Ljava/lang/String;Landroidx/fragment/app/Fragment;)V

    invoke-static {v1}, Lio/reactivex/Completable;->create(Lio/reactivex/CompletableOnSubscribe;)Lio/reactivex/Completable;

    move-result-object p1

    .line 80
    invoke-static {}, Lio/reactivex/android/schedulers/AndroidSchedulers;->mainThread()Lio/reactivex/Scheduler;

    move-result-object p2

    invoke-virtual {p1, p2}, Lio/reactivex/Completable;->subscribeOn(Lio/reactivex/Scheduler;)Lio/reactivex/Completable;

    move-result-object p1

    invoke-static {}, Lio/reactivex/android/schedulers/AndroidSchedulers;->mainThread()Lio/reactivex/Scheduler;

    move-result-object p2

    invoke-virtual {p1, p2}, Lio/reactivex/Completable;->observeOn(Lio/reactivex/Scheduler;)Lio/reactivex/Completable;

    move-result-object p1

    return-object p1
.end method
